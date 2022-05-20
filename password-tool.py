import os
import json
import requests
from bs4 import BeautifulSoup
import numpy as np
import findentropy
import scrapehelp
import sportsclubs
import shutil
import argparse


lists = np.array(["lists/passwords.json", "lists/forenames.gz", "lists/surnames.gz"])
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
                if refresh_p.lower() in ["yes", "yeah", "yea", "y"]:
                    refresh += 1
                    break
                else:
                    return True
    return False


def collect_lists():
    urls = np.array(
        [
            "https://nordpass.com/json-data/top-worst-passwords/findings/all.json",
            "https://forebears.io/earth/forenames",
            "https://forebears.io/earth/surnames",
        ]
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

    cwd = os.getcwd()
    subdir = f"{cwd}/lists"

    try:
        if os.path.exists(subdir):
            confirm = input("Overwrite 'lists' directory? > ")
            if confirm.lower() not in ["yes", "yeah", "yea", "y"]:
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
    def __init__(self, passwd, feedback_id=None):
        self.passwd = passwd
        self.feedback_id = feedback_id


class VeryWeak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 0

    def basics(self):
        with open(lists[0], "r") as f:
            w_passwords = f.read()
        w_passwords = json.loads(w_passwords)
        forenames = np.loadtxt(lists[1], delimiter="\t", dtype=str)
        surnames = np.loadtxt(lists[2], delimiter="\t", dtype=str)
        print(type(w_passwords))
        print(forenames.shape)
        print(surnames.shape)

    def clubs(self):
        return False

    def verdict(self):
        self.basics()
        self.clubs()
        if self.basics() is True or self.clubs() is True:
            return True
        else:
            return False


class Weak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 1

    def contains(self):
        return False

    def length(self):
        return True

    def verdict(self):
        self.contains()
        self.length()
        if self.contains() is True or self.length() is False:
            return True
        else:
            return False


class Decent(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 2

    def complexity(self):
        return True

    def verdict(self):
        self.complexity()
        if self.complexity() is False:
            return True
        else:
            return False


class Strong(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)

    def consecutive(self):
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
        feedback(0)
        print("You have a very weak password")
    elif bools[1] is True:
        feedback(1)
        print("You have a weak password")
    elif bools[2] is True:
        feedback(2)
        print(
            "You have an OK password that could be much stronger with some improvements"
        )
    elif bools[3] is True:
        print(feedback(3))
        print("You have a strong password")
    else:
        print("Something ain't right")
        exit()


def easter_egg() -> str:
    print(f"{(sportsclubs.teamlist[4]).capitalize()} get battered everywhere they go")
    return "COYS"


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
        password = input("Password you'd like to test: ")
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


if __name__ == "__main__":
    main()
