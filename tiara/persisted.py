import cPickle
import os

class PersistedObject(object):
    def __init__(self, fn, default = None):
        self.file_name = os.path.join(os.path.dirname(__file__), "../persisted") + "/save." + fn
        try:
            self.object = cPickle.load(open(self.file_name, "rb"))
        except IOError as e:
            assert e[0] == 2 and e[1] == 'No such file or directory'
            self.object = default

    def Set(self, new_object):
        self.object = new_object
        cPickle.dump(self.object, open(self.file_name, "wb"))

    def Update(self):
        self.Set(self.object)

    def Get(self):
        return self.object

class PersistedDict(PersistedObject):
    def __init__(self, fn):
        super(PersistedDict, self).__init__(fn, {})

    def Lookup(self, key):
        return self.object[key]

    def Insert(self, key, new_val):
        self.object[key] = new_val
        self.Update()

    
