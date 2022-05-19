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


lists = np.array(["lists/passwords.json", "lists/forenames.txt", "lists/surnames.txt"])
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
        with open(lists[1], "w") as f:
            f.write(content[1])
        with open(lists[2], "w") as f:
            f.write(content[2])


class StrengthLevel:
    def __init__(self, passwd, password_strength=None):
        self.passwd = passwd
        self.password_strength = password_strength


class VeryWeak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)
        # Can be useful to develop incremental adjustments to strength level for tailored feedback
        self.password_strength = 0

    def verdict(self):
        return False


class Weak(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)

    def verdict(self):
        return False


class Decent(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)

    def verdict(self):
        return False


class Strong(StrengthLevel):
    def __init__(self, passwd):
        super().__init__(passwd)

    def verdict(self):
        return True


def strength_checker(p_test):
    """Putting the polymorphic verdict() method to use"""
    return p_test.verdict()


def evaluation(bools):
    if bools[0] is True:
        print("You have a very weak password")
    elif bools[1] is True:
        print("You have a weak password")
    elif bools[2] is True:
        print("You have an OK password that could be strong with some improvements")
    elif bools[3] is True:
        print("You have a strong password")
    else:
        print("Something ain't right")


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

    results = []
    for criteria in scenarios:
        results.append(strength_checker(criteria))

    print(results)
    evaluation(results)


if __name__ == "__main__":
    main()
