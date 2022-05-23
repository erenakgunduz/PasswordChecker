import os
import re
import sys
import json
import lxml
import cchardet
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, SoupStrainer
from getpass import getpass
import numpy as np
import findentropy
import scrapehelp
import sportsclubs
import shutil
import argparse
import logging


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
                refresh += 1
                if refresh_p.lower() in affirm:
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

    logging.debug(sys.getsizeof(urls))

    headers = scrapehelp.headers
    logging.debug(headers)

    status = []
    content = np.array([])
    for url in urls:
        response = requests.get(url, allow_redirects=True, headers=headers)
        status.append(response.status_code)
        content = np.append(content, response.text)

    logging.info(status)
    match status:
        case [200, 200, 200]:
            logging.info("Good 2 go")
        case _:
            sys.exit("Couldn't get all the lists. Try again :)")

    worst_passwords = {}
    json_list = json.loads(content[0])
    for i in range(len(json_list)):
        worst_passwords[json_list[i]["Password"]] = json_list[i]["Time_to_crack"]

    worst_passwords = json.dumps(worst_passwords)

    # Using range(len()) idiom here and above to iterate through just integers until total amount reached
    # enumerate() returns tuple as there are several layers of nesting involved, so not helpful for these cases
    def html_extract(html):
        strainer = SoupStrainer("td", attrs={"class": "sur"})
        soup = BeautifulSoup(html, "lxml", parse_only=strainer)
        get_names = soup.find_all("td", class_="sur")
        names = np.array([])
        for name in range(len(get_names)):
            names = np.append(names, get_names[name].contents[0].get_text())
        return names

    forenames = html_extract(content[1])
    surnames = html_extract(content[2])

    subdir = f"{os.getcwd()}/lists"

    try:
        if os.path.exists(subdir):
            confirm = input("Overwrite 'lists' directory? > ")
            if confirm.lower() not in affirm:
                sys.exit("Aborting.")
            shutil.rmtree(subdir)
        os.mkdir(subdir)
    except OSError:
        sys.exit("Something went wrong in the process of generating 'lists/' :/")
    else:
        with open(lists[0], "w") as f:
            f.write(worst_passwords)
        with open(lists[1], "w"):
            np.savetxt(lists[1], forenames, fmt="%s")
        with open(lists[2], "w"):
            np.savetxt(lists[2], surnames, fmt="%s")


class StrengthLevel(ABC):
    __slots__ = "passwd", "feedback_id", "w_passwords", "forenames", "surnames"

    def __init__(
        self,
        passwd: str,
        feedback_id=None,
        w_passwords=None,
        forenames=None,
        surnames=None,
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

    @abstractmethod
    def verdict(self):
        pass


class VeryWeak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        self.feedback_id = 0

    def basics(self):
        """Does the password fail at any of the most basic considerations?"""
        self.grab()
        logging.debug(len(self.w_passwords))
        logging.debug(type(self.w_passwords))
        logging.debug(sportsclubs.teamlist.shape)
        logging.debug(self.forenames.shape)
        logging.debug(self.surnames.shape)

        if len(self.passwd) < 5:
            self.feedback_id = 0.05
            return True
        elif "password" in self.passwd.lower():
            self.feedback_id = 0.1
            return True
        elif self.passwd.lower() in self.w_passwords:
            match self.passwd.lower():
                case "liverpool":
                    self.feedback_id = 0.5
                case _:
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
                case "liverpool1":
                    self.feedback_id = 0.5
                case "arsenal" | "arsenal1":
                    self.feedback_id = 0.6
                case "ronaldo7":
                    self.feedback_id = 0.7
                case _:
                    self.feedback_id = 0.8
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
        # Clean up short names to prevent false positives here
        self.forenames = np.array([name for name in self.forenames if len(name) >= 5])
        self.surnames = np.array([name for name in self.surnames if len(name) >= 5])
        logging.debug(self.forenames.shape)
        logging.debug(self.surnames.shape)

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
        just_num = self.passwd.isdigit()
        mixed_case = not self.passwd.islower() and not self.passwd.isupper()
        symbols = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        mixed_cset = not self.passwd.isalnum() and any(
            c in symbols for c in self.passwd
        )
        p_entropy = findentropy.EntropyCalculate(self.passwd)
        entropy_awful = p_entropy.entropy() < 8
        entropy_bad = p_entropy.entropy() < 24
        entropy_good = p_entropy.entropy() >= 60

        try:
            if not length:
                self.feedback_id = 2.1
                return False
            elif entropy_awful:
                self.feedback_id = 2.2
                return False
            elif just_num:
                self.feedback_id = 2.3
                return False
            elif not mixed_case and not mixed_cset:
                self.feedback_id = 2.4
                return False
            elif entropy_bad:
                self.feedback_id = 2.5
                return False
            elif not entropy_good:
                self.feedback_id = 2.6
                return False
            else:
                return True
        finally:
            logging.debug(p_entropy.entropy())
            logging.debug(p_entropy.entropy_ideal())
            logging.debug(p_entropy.avg_entropy())
            del p_entropy.string

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
        if re.search(r"(.)\1{3}", self.passwd):
            self.feedback_id = 3.1
            return True
        elif re.search(r"\d{4}", self.passwd):
            self.feedback_id = 3.2
            return True
        else:
            self.feedback_id = 4
            return False

    def length(self):
        """Is the password long? (20 chars or more)"""
        if len(self.passwd) >= 20:
            return True
        return False

    def verdict(self):
        self.consecutive()
        if (self.consecutive() is False) and (self.length() is True):
            self.feedback_id = 5
        return True


def evaluation(bools, tests):
    # Could also do feedback = lambda n: tests[n].feedback_id
    # But not recommended to assign to lambda as it defeats the point
    def feedback(n):
        return tests[n].feedback_id

    # Already implicity returns None, use annotation to make it known "this is like a procedure, should return nothing"
    def error_message() -> None:
        logging.info(bools)
        logging.error("No valid feedback ID")
        sys.exit("Something ain't right")

    if bools[0] is True:
        logging.debug(feedback(0))
        print("Password strength: Very weak")
        sportsteam = (
            "It seems your password is simply a football or sports club/related to one. This is a bad idea.\n",
            "These were collected from the most common lists for their respective countries.\n",
            "Someone who already knows which team you support could likely guess it very easily.\n",
            "We advise you to use something else :)",
        )
        match feedback(0):
            case 0.05:
                print("Your password is far too short (less than 5 characters)")
                print(
                    "Consider using one that's much longer - we recommend at least 12 characters for the length."
                )
            case 0.1:
                print("Your password contains the word 'password'")
                print(
                    "This is always a bad idea, as it's one of the first things anyone would guess."
                )
                print("We suggest you don't include that word at all.")
            case 0.2:
                passwd = tests[0].passwd.lower()
                print(
                    "Your password is on the 2021 list for the top 200 most common passwords worldwide."
                )
                print(
                    f"The password '{passwd}' can be cracked in {tests[0].w_passwords[passwd]}!"
                )
                print(
                    "You should come up with a different one & change it if you use it IMMEDIATELY :)"
                )
            case 0.3:
                print(
                    "Your password appears to be just a personal name. This is always bad."
                )
                print(
                    "When it comes to passwords, make sure they contain no personal information."
                )
                print(
                    "This includes things such as name, email address, phone or social security #, etc. (Source: Harvard guidelines)"
                )
            case 0.4:
                print("".join(sportsteam))
                print("Also, let's never forget:")
                print(amazing_fact())
            case 0.5:
                print("".join(sportsteam))
                print(
                    f"'{sportsclubs.teamlist[0]}' in particular is one of the top 200 most common passwords in the entire world!"
                )
                print(
                    "YNWA, because you alone won't be accessing your accounts if that's actually your password for anything ;D"
                )
            case 0.6:
                print("".join(sportsteam))
                if (
                    input("By the way, would you like to hear an amazing fact? > ")
                    in affirm
                ):
                    amazing_fact()
            case 0.7:
                print("".join(sportsteam))
                print("SIUUUUUUUU")
            case 0.8:
                print("".join(sportsteam))
            case _:
                error_message()
    elif bools[1] is True:
        logging.debug(feedback(1))
        print("Password strength: Weak")
        match feedback(1):
            case 1.1:
                print(
                    "Though your password seems to not fail the very basics, it is still too short."
                )
                print(
                    "We recommend at least 12 characters - for these purposes more is better."
                )
            case 1.2:
                print(
                    "Your password seems to contain a football/sports club or something related."
                )
                print(
                    "Since this can make it easier for someone who knows you to crack it, you should avoid this."
                )
            case 1.3:
                print("Your password appears to contain a personal name.")
                print("It is definitely best to avoid this for a number of reasons.")
            case _:
                error_message()
    elif bools[2] is True:
        logging.debug(feedback(2))
        print("Password strength: OK")
        match feedback(2):
            case 2.1:
                print("(Maybe)")
                print("Your password is a bit on the shorter side.")
                print(
                    "To achieve good complexity, consider making it at least a little longer."
                )
            case 2.2:
                print("(Sike it's actually not OK)")
                print("It seems your password has a very poor entropy.")
                print(
                    "You can think of it as a calculation of the unpredictability of your password's contents."
                )
                print("As it is now, it would most likely be very easy to crack.")
                print("Use something more creative instead :)")
            case 2.3:
                print(
                    "Your password appears to be composed of only digits. This is typically not a good idea."
                )
                print(
                    "You can add some more variety to make it not only easier to remember, but also stronger."
                )
            case 2.4:
                print(
                    "Your password contains only one case of letters. It may or may not contain numbers too."
                )
                print(
                    "However, with some small changes you could seriously improve it."
                )
                print(
                    "By that, we mean to consider also using mixed case and/or special characters."
                )
            case 2.5:
                print("(Not really)")
                print("Your password has a poor entropy.")
                print("Try spicing it up a little.")
            case 2.6:
                print(
                    "Though your password seems OK for the most part, the entropy isn't quite as high as we want."
                )
                print(
                    "To reach a level where your password is truly solid, try adding just a few more things to it."
                )
            case _:
                error_message()
    elif bools[3] is True:
        logging.debug(feedback(3))
        print("Password strength: Strong")
        harvardkey = "It's best to avoid this (Source: HarvardKey)."
        match feedback(3):
            case 3.1:
                print("Your password is probably strong as is.")
                print(
                    "However, it contains a sequence of the same character four consecutive times."
                )
                print(harvardkey)
            case 3.2:
                print("Your password is probably strong as is.")
                print("However, it contains a sequence of four digits back to back.")
                print(harvardkey)
            case 4:
                print(
                    "Congratulations, it seems your password is probably a strong one by all means!"
                )
                print(
                    "That said, one thing that could help you achieve maximum strength is for it to be even longer."
                )
                print(
                    "One great way to achieve this and still be able to remember it is to use a passphrase! (Source: Harvard)"
                )
            case 5:
                print("Congratulations, you seem to have a rather strong password!")
                print(
                    "If you are using a passphrase, that is a great strategy. Good thinking!"
                )
                print(
                    "Otherwise, it would be a good idea to use a password manager so you don't lose/forget this."
                )
            case _:
                error_message()
    else:
        error_message()


def amazing_fact() -> str:
    """Shoutout Bonzi"""
    print(f"{sportsclubs.teamlist[4].capitalize()} get battered everywhere they go 😈")
    return "⚪ COYS ⚪ ;)"


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

    fmt = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=fmt)

    while check_4_lists() is False:
        collect_lists()

    if password is None:
        password = getpass("Password you'd like to test: ")
    else:
        password = args.test[0]

    password = password.strip()
    logging.debug(password)
    logging.debug(type(password))

    if " " in password:
        sys.exit("Not valid. Come again :)")

    veryweak_p = VeryWeak(password)
    weak_p = Weak(password)
    decent_p = Decent(password)
    strong_p = Strong(password)

    scenarios = (veryweak_p, weak_p, decent_p, strong_p)

    # I love this line, I discuss it in the README
    results = [(lambda p_test: p_test.verdict())(criteria) for criteria in scenarios]

    logging.debug(results)
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
