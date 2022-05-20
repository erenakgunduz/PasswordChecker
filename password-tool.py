import os
import json
import requests
from bs4 import BeautifulSoup
from getpass import getpass
import numpy as np
import findentropy
import scrapehelp
import sportsclubs
import shutil
import argparse


lists = ("lists/passwords.json", "lists/forenames.gz", "lists/surnames.gz")
affirm = ("yes", "yeah", "yea", "y")
refresh = 0


def check_4_lists():
    global refresh
    for listfile in lists:
        files_exist = os.path.exists(listfile)
        if files_exist is False:
            refresh += 1
            break
        else:
            if refresh > 0:
                return True
            else:
                refresh_p = input(
                    "List files exist. Would you like to refresh them? > "
                )
                if refresh_p.lower() in affirm:
                    refresh += 1
                    break
                else:
                    return True
    return False


def collect_lists():
    urls = (
        "https://nordpass.com/json-data/top-worst-passwords/findings/all.json",
        "https://forebears.io/earth/forenames",
        "https://forebears.io/earth/surnames",
    )

    headers = scrapehelp.headers
    print(headers)

    status = []
    content = np.array([])
    for url in urls:
        response = requests.get(url, allow_redirects=True, headers=headers)
        status.append(response.status_code)
        content = np.append(content, response.text)

    print(status)
    match status:
        case [200, 200, 200]:
            print("Good 2 go")
        case _:
            print("Couldn't get all the lists. Try again :)")
            exit()

    worst_passwords = {}
    json_list = json.loads(content[0])
    for i in range(len(json_list)):
        worst_passwords[json_list[i]["Password"]] = json_list[i]["Time_to_crack"]

    worst_passwords = json.dumps(worst_passwords)

    def html_extract(html):
        soup = BeautifulSoup(html, "html.parser")
        name_count = len(soup.find_all("td", class_="sur"))
        print(name_count)
        names = np.array([])
        for name in range(name_count):
            names = np.append(
                names,
                soup.find_all("td", class_="sur")[name].contents[0].get_text(),
            )
        return names

    forenames = html_extract(content[1])
    surnames = html_extract(content[2])

    subdir = f"{os.getcwd()}/lists"

    try:
        if os.path.exists(subdir):
            confirm = input("Overwrite 'lists' directory? > ")
            if confirm.lower() not in affirm:
                print("Aborting.")
                exit()
            shutil.rmtree(subdir)
        os.mkdir(subdir)
    except OSError:
        print("Something went wrong in the process of generating 'lists/' :/")
        exit()
    else:
        with open(lists[0], "w") as f:
            f.write(worst_passwords)
        with open(lists[1], "w"):
            np.savetxt(lists[1], forenames, fmt="%s")
        with open(lists[2], "w"):
            np.savetxt(lists[2], surnames, fmt="%s")


class StrengthLevel:
    def __init__(
        self, passwd, feedback_id=None, w_passwords=None, forenames=None, surnames=None
    ):
        self.passwd = passwd
        self.feedback_id = feedback_id
        self.w_passwords = w_passwords
        self.forenames = forenames
        self.surnames = surnames

    def reader(self):
        with open(lists[0], "r") as f:
            self.w_passwords = f.read()
        self.w_passwords = json.loads(self.w_passwords)
        self.forenames = np.loadtxt(lists[1], delimiter="\t", dtype=str)
        self.surnames = np.loadtxt(lists[2], delimiter="\t", dtype=str)

    @staticmethod
    def formatter(names):
        names = np.char.lower(names)
        names = np.char.replace(names, " ", "-")
        return names

    def grab(self):
        self.reader()
        self.forenames = self.formatter(self.forenames)
        self.surnames = self.formatter(self.surnames)


class VeryWeak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 0

    def basics(self):
        """Does the password fail at any of the most basic considerations?"""
        self.grab()

        if len(self.passwd) < 5:
            self.feedback_id = 0.05
            return True
        elif "password" in self.passwd.lower():
            self.feedback_id = 0.1
            return True
        elif self.passwd.lower() in self.w_passwords:
            self.feedback_id = 0.2
            return True
        elif (self.passwd.lower() in self.forenames) or (
            self.passwd.lower() in self.surnames
        ):
            self.feedback_id = 0.3
            return True
        else:
            return False

    def clubs(self):
        """Is the password simply the name of a football/sports club or something related?"""
        if self.passwd.lower() in sportsclubs.teamlist:
            match self.passwd.lower():
                case "tottenham" | "tottenham1":
                    self.feedback_id = 0.4
                case "liverpool" | "liverpool1":
                    self.feedback_id = 0.5
                case "arsenal" | "arsenal1":
                    self.feedback_id = 0.6
                case _:
                    self.feedback_id = 0.7
            return True
        return False

    def verdict(self):
        self.basics()
        self.clubs()
        if (self.basics() is True) or (self.clubs() is True):
            return True
        return False


class Weak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 1

    def length(self):
        """Is the password's length inadequate?"""
        if len(self.passwd) < 10:
            self.feedback_id = 1.1
            return True
        return False

    def contains(self):
        """Does the password contain a personal or sports club name?"""
        self.grab()
        # Clean up very short names to prevent false positives here
        self.forenames = np.array([name for name in self.forenames if len(name) >= 4])
        self.surnames = np.array([name for name in self.surnames if len(name) >= 4])
        # print(self.forenames.shape)
        # print(self.surnames.shape)

        if any(team in self.passwd.lower() for team in sportsclubs.teamlist):
            self.feedback_id = 1.2
            return True
        elif any(name in self.passwd.lower() for name in self.forenames) or any(
            name in self.passwd.lower() for name in self.surnames
        ):
            self.feedback_id = 1.3
            return True
        else:
            return False

    def verdict(self):
        self.length()
        self.contains()
        if (self.length() is True) or (self.contains() is True):
            return True
        return False


class Decent(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 2

    def complexity(self):
        """Does the password exhibit a good complexity?"""
        length = len(self.passwd) >= 12
        mixed_case = not self.passwd.islower() and not self.passwd.isupper()
        symbols = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        mixed_cset = not self.passwd.isalnum() and any(
            c in symbols for c in self.passwd
        )
        p_entropy = findentropy.EntropyCalculate(self.passwd)
        entropy_good = p_entropy.entropy() >= 60

        if not length:
            self.feedback_id = 2.1
            return False
        elif not mixed_case and not mixed_cset:
            self.feedback_id = 2.2
            return False
        elif not entropy_good:
            self.feedback_id = 2.3
            return False
        else:
            return True

    def verdict(self):
        self.complexity()
        if self.complexity() is False:
            return True
        return False


class Strong(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)

    def consecutive(self):
        """Does the password contain a bad sequence?"""
        return False

    def verdict(self):
        self.consecutive()
        if self.consecutive() is True:
            self.feedback_id = 3
        else:
            self.feedback_id = 4
        return True


def evaluation(bools, tests):
    # Could also do feedback = lambda n: tests[n].feedback_id
    # But not recommended to assign to lambda as it defeats the point
    def feedback(n):
        return tests[n].feedback_id

    if bools[0] is True:
        print(feedback(0))
        print("You have a very weak password")
    elif bools[1] is True:
        print(feedback(1))
        print("You have a weak password")
    elif bools[2] is True:
        print(feedback(2))
        print(
            "You have an OK password that could be much stronger with some improvements"
        )
    elif bools[3] is True:
        print(feedback(3))
        print("You have a strong password")
    else:
        print("Something ain't right")
        exit()


def amazing_fact() -> str:
    """Shoutout Bonzi"""
    print(f"{sportsclubs.teamlist[4].capitalize()} get battered everywhere they go")
    return "COYS ;)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "-c",
        "--test",
        "--check",
        action="store",
        type=str,
        required=False,
        nargs=1,
        metavar="PASSWORD",
        help="enter the password to be tested upfront (no spaces!)",
    )

    args = parser.parse_args()
    password = args.test

    while check_4_lists() is False:
        collect_lists()

    if password is None:
        password = getpass("Password you'd like to test: ")
    else:
        password = args.test[0]

    password = password.strip()
    print(password)
    print(type(password))

    if " " in password:
        print("Not valid. Come again :)")
        exit()

    veryweak_p = VeryWeak(password)
    weak_p = Weak(password)
    decent_p = Decent(password)
    strong_p = Strong(password)

    scenarios = np.array([veryweak_p, weak_p, decent_p, strong_p])

    # I love this line, I discuss it in the README
    results = [(lambda p_test: p_test.verdict())(criteria) for criteria in scenarios]

    print(results)
    evaluation(results, scenarios)

    caches = f"{os.getcwd()}/__pycache__"
    if os.path.exists(caches):
        rm_cache = input("Found Python cache. Do you want to clear it? > ")
        if rm_cache.lower() in affirm:
            shutil.rmtree(caches)

    if args.test is None:
        if input("Go again? > ").lower() in affirm:
            main()


if __name__ == "__main__":
    main()
