
major = 2
minor = 0
dev   = 0

__version__ = "{}.{}.{}".format(major, minor, dev)

class Version:
    def __init__(self, major=major, minor=minor, dev=dev, name="", desc=""):
        self.major = major
        self.minor = minor
        self.dev   = dev
        self.name = name
        self.desc = desc

    def int(self):
        return self.major * 100 + self.minor * 10 + self.dev

    def __str__(self):
        return f'v{self.major}.{self.minor}.{self.dev}, {self.name}: {self.desc}'
