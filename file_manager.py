import os


class PersistentSet:
    """
    PersistentSet

    Class representing a set of items loaded from a file.

    Attributes:
        _filename (str): The name of the file to load and save the set from.
        _set (set): The set of items loaded from the file.

    Methods:
        __init__(self, filename)
            Initializes a new instance of the File2Set class with the given filename.
            The set is initialized empty and then loaded from the file.

        load(self)
            Loads the set from the file.
            If the file exists, it opens it and reads each line into the set after stripping any leading or trailing whitespace.

        check(self, item_name)
            Checks if the given item_name is present in the set.
            Returns True if the item_name is found in the set, otherwise returns False.

        add(self, item_name)
            Adds the given item_name to the set.

        save(self)
            Saves the set to the file.
            Opens the file in write mode and writes each item in the set to a new line in the file.
    """
    def __init__(self, filename):
        self._filename = filename
        self._set = set()
        self.load()

    def load(self):
        if os.path.exists(self._filename):
            with open(self._filename, 'r') as file:
                self._set = set(line.strip() for line in file)

    def check(self, item_name):
        return item_name in self._set

    def add(self, item_name):
        self._set.add(item_name)

    def save(self):
        with open(self._filename, 'w') as file:
            file.writelines(f"{item_name}\n" for item_name in self._set)
