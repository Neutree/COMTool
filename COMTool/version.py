
major = 3
minor = 1
dev   = 0

__version__ = "{}.{}.{}".format(major, minor, dev)

class Version:
    def __init__(self, major=major, minor=minor, dev=dev, name="", desc=""):
        self.major = major
        self.minor = minor
        self.dev   = dev
        self.name = name
        self.desc = desc

    def dump_dict(self):
        ret = {
            "major": self.major,
            "minor": self.minor,
            "dev": self.dev,
            "name": self.name,
            "desc": self.desc
        }
        return ret

    def load_dict(self, obj):
        self.major = obj['major']
        self.minor = obj['minor']
        self.mdev= obj['dev']
        self.name = obj['name']
        self.desc = obj['desc']

    def int(self):
        return self.major * 100 + self.minor * 10 + self.dev

    def __str__(self):
        return 'v{}.{}.{}, {}: {}'.format(self.major, self.minor, self.dev, self.name, self.desc)
