import copy
import snode
import sys

def Reload():
    snode.Reload()
    return reload(sys.modules[__name__])

class Preprocessor:
    def __init__(self, json):
        self.json = json
        self.next_fact_id = len(self.json["facts"])
        while self.next_fact_id in [f["id"] for f in self.json["facts"] if "id" in f]:
            self.next_fact_id += 1

    def GetFactId(self):
        r = self.next_fact_id
        self.next_fact_id += 1
        return r

    def MakeIds(self):
        for f in self.json["facts"]:
            if "id" not in f:
                f["id"] = self.GetFactId()
            f["original_id"] = f["id"]
    
    def PopFact(self, fid):
        self.json["facts"] = [f for f in self.json["facts"] if f["id"] != fid]
        self.json["relations"] = [r for r in self.json["relations"] if r["dep"] != fid and r["gov"] != fid]

    def CopyFact(self, f):
        fcopy = copy.deepcopy(f)
        fcopy["id"] = self.GetFactId()
        self.json["facts"].append(fcopy)
        
        for r in copy.copy(self.json["relations"]):
            for k in ["dep","gov"]:
                if r[k] == f["id"]:
                    rcopy = copy.deepcopy(r)
                    rcopy[k] = fcopy["id"]
                    self.json["relations"].append(rcopy)

        return fcopy
                    
    def ExpandMultiEntities(self, singular):
        plural = "preproc_" + singular + "s"
        for f in copy.copy(self.json["facts"]):
            if plural in f:
                assert singular not in f, "Fact with %s and %s" % (singular, plural)
                for ent in f[plural]:
                    fcopy = self.CopyFact(f)
                    fcopy[singular] = ent
                    del fcopy[plural]
                self.PopFact(f["id"])

    def Preprocess(self):
        self.MakeIds()
        self.ExpandMultiEntities("subject")
        self.ExpandMultiEntities("object")

def Preprocess(json):
    preproc = Preprocessor(json)
    preproc.Preprocess()
    return preproc.json