import findentropy


def main():
    teststring = "some$tring"
    testing = findentropy.EntropyCalculate(teststring)

    print(len(testing.string))
    print(len(set(testing.string)))
    print(testing.avg_entropy())

    testing.string = "hypotheticallygoodpas$word"
    print(len(testing.string))
    print(len(set(testing.string)))

    print(testing.entropy())
    print(testing.entropy_ideal())
    print(testing.avg_entropy())
    print(type(testing.avg_entropy()))

    del testing.string

    try:
        print(type(testing.avg_entropy()))
    except AttributeError:
        print("Congratulations, we can't find your string anymore!")


if __name__ == "__main__":
    main()
