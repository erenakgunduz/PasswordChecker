# PasswordChecker

A fun "little" project that has helped me immensely with getting back into the swing of things with the latest Python and all that it has to offer. I took care to incorporate the core tenets of object-oriented programming heavily, as well as all the various techniques with which I either already was or have now become familiar.

The verdict(): I still got it ;)

## Putting lambda+comprehension to use

By writing a lambda function passed to an immediately invoked function expression (IIFE) as part of a list comprehension for the simple iteration I'm using here, I was able to achieve the same outcome as I had with all these lines of code (which I used prior):

```python
def strength_checker(p_test):
    """Putting the polymorphic verdict() method to use"""
    return p_test.verdict()

results = []
for criteria in scenarios:
    results.append(strength_checker(criteria))
```

Using just this one line (line 587):

```python
results = [(lambda p_test: p_test.verdict())(criteria) for criteria in scenarios]
```

I am pleased with how efficient and "pythonic" (that's what they call it?) that turned out, and it seems to take on more of a functional and declarative dimension this way also.

## Usage

This is a command-line tool that requires Python 3.10+. Start by cloning this repository within the directory of your choice:

```bash
git clone https://github.com/erenakgunduz/PasswordChecker.git
```

You can simply use the provided pip requirements file to install the necessary packages in the respective virtual environment, after creating and activating one in whichever manner you prefer:

```bash
cd PasswordChecker
python3 -m pip install -r requirements.txt
```

Now you should be all set (use -h/--help for more info):

```bash
python3 passwordtool.py
```

---

Note that by default, as a consideration for both security and the end user experience, I have set the logging level to display errors only.

If you would like to see the debug information (was highly useful for me during testing), then all that's necessary is a very simple tweak: (on line 562, use this instead)

```python
logging.basicConfig(level=logging.DEBUG, format=fmt)
```
