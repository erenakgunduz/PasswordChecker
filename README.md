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

Using just this one line (line 261):

```python
results = [(lambda p_test: p_test.verdict())(criteria) for criteria in scenarios]
```

I am pleased with how efficient and "pythonic" (that's what they call it?) that turned out, and it seems to take on more of a functional and declarative dimension this way also.
