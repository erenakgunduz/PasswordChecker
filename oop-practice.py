class StrengthLevel:
    # Defining the default value of the instance attribute so you don't have to explicity set one if you don't want to
    def __init__(self, password_strength=None):
        self.password_strength = password_strength


class VeryWeak(StrengthLevel):
    # A class attribute. This is unique/limited to this class ONLY
    # One upside is that you don't need to set an instance (create an object of said class) to be able to use it
    some_var = "test string"

    def __init__(self, passwd):
        # Inherit all the constructed attributes of the parent class
        super().__init__()
        self.passwd = passwd

    # Altering how the class is represented
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.passwd})"

    # Can access class attribute within that same class
    def testing(self):
        return self.some_var

    # Can also do it with the cls parameter
    # Class methods can be especially helpful for certain things, like creating more "copies" (instances) of the class:
    @classmethod
    def insert(cls):
        print(f"This is the {cls.some_var}")
        return cls("thispasswdisveryweak")

    # Easiest to understand, still can be helpful for encapsulation
    @staticmethod
    def quickmafs():
        return 2 + 2


# Creating instances of the child and parent class
stronk = VeryWeak("example")
stronf = StrengthLevel()

# This attribute was inherited from the superclass, but by changing it for this instance
stronk.password_strength = 21

# Now the values are different
print(stronk.password_strength)
print(stronf.password_strength)

# Putting the class method to use
print(stronk.insert())

# The class method used here doesn't actually change the already defined value of the passwd attribute for this instance
print(stronk.passwd)

# But it allows us to do this
example_weakp = stronk.insert()

# Now we've created another fully valid instance, just with the different value for passwd specified in insert() method
print(example_weakp.passwd)
print(example_weakp.quickmafs())
print(example_weakp.testing())

# Direct access to all of these is possible
print(VeryWeak.some_var)  # Class attribute
print(VeryWeak.quickmafs())  # Static method
print(VeryWeak.insert())  # Class method

# But not to this, since it requires the self argument which only an instance can provide
try:
    print(VeryWeak.testing())
except TypeError:
    print("Got 'em")
