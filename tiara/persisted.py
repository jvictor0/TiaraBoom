import cPickle
import os

class PersistedObject(object):
    def __init__(self, fn, default = None):
        self.file_name = os.path.join(os.path.dirname(__file__), "../persisted") + "/save." + fn
        try:
            self.object = cPickle.load(open(self.file_name, "rb"))
            self.initializedFromCache = True
        except IOError as e:
            assert e[0] == 2 and e[1] == 'No such file or directory'
            self.object = default
            self.initializedFromCache = False

    def Set(self, new_object):
        self.object = new_object
        cPickle.dump(self.object, open(self.file_name, "wb"))

    def Update(self):
        self.Set(self.object)

    def Get(self):
        return self.object

    def __len__(self):
        return len(self.object) # this might not work for all object types!

    def __contains__(self, obj):
        return obj in self.object # this might not work for all object types!


class PersistedDict(PersistedObject):
    def __init__(self, fn):
        super(PersistedDict, self).__init__(fn, {})

    def Lookup(self, key):
        return self.object[key]

    def Insert(self, key, new_val):
        self.object[key] = new_val
        self.Update()

class PersistedSet(PersistedObject):
    def __init__(self, fn):
        super(PersistedSet, self).__init__(fn, set([]))

    def Insert(self, key):
        self.object.add(key)
        self.Update()

class PersistedList(PersistedObject):
    def __init__(self, fn):
        super(PersistedList, self).__init__(fn, [])

    def Append(self, key):
        self.object.append(key)
        self.Update()

    def PopBack(self):
        self.object.pop(-1)
        self.Update()

    def PopFront(self):
        self.object.pop(0)
        self.Update()

    def At(self,i):
        return self.object[i]

    def Front(self):
        return self.At(0)

    def Back(self):
        return self.At(-1)
