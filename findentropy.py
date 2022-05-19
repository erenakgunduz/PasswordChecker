from functools import cache
import math


class EntropyCalculate:
    def __init__(self, string):
        self._string = string

    @property
    def string(self):
        """Gets string, but using property to add encapsulation"""
        # No custom functionality here (in the getter)
        return self._string

    @string.setter
    def string(self, new_value):
        """Sets a new value to string"""

        print(f"Changing string to {new_value}")
        self._string = new_value

    @string.deleter
    def string(self):
        """Deletes the string"""
        # Nor here in the deleter, but we have it set up so that we could implement it if needed
        del self._string

    def entropy(self):
        """Calculates the Shannon entropy of a string"""

        # Determines probability of chars in string
        prob = [
            float(self.string.count(c)) / len(self.string)
            for c in dict.fromkeys(list(self.string))
        ]

        # Calculates entropy
        @cache
        def entropy_per_char():
            return -sum([p * math.log(p) / math.log(2) for p in prob])

        return entropy_per_char() * len(self.string)

    def entropy_ideal(self):
        """Calculates the ideal Shannon entropy of a string with given length"""

        prob = 1.0 / len(set(self.string))

        @cache
        def entropy_ideal_per():
            return -1.0 * len(set(self.string)) * prob * math.log(prob) / math.log(2)

        return entropy_ideal_per() * len(self.string)

    def avg_entropy(self):
        return (self.entropy() + self.entropy_ideal()) / 2
