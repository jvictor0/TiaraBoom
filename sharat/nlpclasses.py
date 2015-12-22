
import unidecode

class Opt:
    def __init__(self, tp):
        self.tp = tp
        
def IsPrimitive(val):
    return isinstance(val,str) or isinstance(val,int) or isinstance(val,bool) or val == None

def ValidateNonRecursive(schema, json):
    for k in schema.keys():
        if k in json and isinstance(json[k], unicode): json[k] = unidecode.unidecode(json[k])
        if isinstance(schema[k], Opt):
            assert k not in json or isinstance(json[k],schema[k].tp), (k, schema,json)
        else:
            assert k in json and isinstance(json[k],schema[k]), (k, schema,json)
    assert len(set(json.keys()) - set(schema.keys())) == 0, (set(json.keys()) - set(schema.keys()),json)

class Token:
    def __init__(self, json):
        self.json = json

    def __str__(self):
        return "Token(%s)" % self["word"]

    def __getitem__(self, at):
        if isinstance(self.json[at], unicode): self.json[at] = unidecode.unidecode(self.json[at])
        assert IsPrimitive(self.json[at]), (at,self.json)
        return self.json[at]

    def Equals(self, other):
        return self.json == other.json

    def __contains__(self, key):
        return key in self.json

    def Validate(self):
        schema = {"word"                 : str,
                  "characterOffsetBegin" : int,
                  "characterOffsetEnd"   : int,
                  "pos"                  : str,
                  "index"                : int,
                  "lemma"                : str,
                  "before"               : str,
                  "after"                : str,
                  "ner"                  : str,
                  "normalizedNER"        : Opt(str),
                  "speaker"              : str,
                  "originalText"         : str}
        ValidateNonRecursive(schema, self.json)

class Rel:
    def __init__(self, json):
        self.json = json
        
    def __str__(self):
        return "Rel(%s, %s, %s)" % (self["subject"], self["relation"], self["object"])

    def __getitem__(self, at):
        if isinstance(self.json[at], unicode): self.json[at] = unidecode.unidecode(self.json[at])
        assert at.endswith("Span") or IsPrimitive(self.json[at]), (at,self.json)
        return self.json[at]

    def __contains__(self, key):
        return key in self.json

    def Equals(self, other):
        return self.json == other.json

    def Validate(self):
        schema = {"subject"       : str,
                  "object"        : str,
                  "relation"      : str,
                  "subjectSpan"   : list,
                  "objectSpan"    : list,
                  "relationSpan"  : list}
        ValidateNonRecursive(schema, self.json)
        for k in [k for k in self.json.keys() if k.endswith("Span")]:
            assert len(self.json[k]) == 2 and isinstance(self.json[k][0],int) and isinstance(self.json[k][1],int), self.json

def PrintRelations(rels):
    if len(rels) == 0:
        return
    maxsublen = max([len(rels[i]["subject"]) for i in xrange(len(rels))])
    maxrellen = max([len(rels[i]["relation"]) for i in xrange(len(rels))])
    maxobjlen = max([len(rels[i]["object"]) for i in xrange(len(rels))])
    for i in xrange(len(rels)):
        r = rels[i]
        print "Rel(%s%s , %s%s , %s%s )" % (r["subject"], " " * (maxsublen - len(r["subject"])), r["relation"], " " * (maxrellen - len(r["relation"])), r["object"], " " * (maxobjlen - len(r["object"])))


class Sentence:
    def __init__(self, json):
        self.json = json
        
    def Rel(self, i):
        return Rel(self.json["openie"][i])

    def RelLen(self):
        return len(self.json["openie"])

    def Relations(self):
        return [self.Rel(i) for i in xrange(self.RelLen())]
        
    def PrintRelations(self):
        PrintRelations(self.Relations())

    def TokenLen(self):
        return len(self.json["tokens"])

    def Token(self, i):
        return Token(self.json["tokens"][i])

    def Tokens(self):
        return [self.Token(i) for i in xrange(self.TokenLen())]

    def Text(self):
        result = []
        for i in xrange(self.TokenLen()):
            tk = self.Token(i)
            assert i == 0 or result[-1] == tk["before"]
            result.append(tk["word"])
            result.append(tk["after"])                        
        return "".join(result)

    def __str__(self):
        return "Sentence(%s)" % self.Text()

    def Equals(self, other):
        return all([self.json["index"] == other.json["index"],
                    self.json["openie"] == other.json["openie"],
                    self.json["tokens"] == other.json["tokens"]])

    def __getitem__(self, at):
        if isinstance(self.json[at], unicode): self.json[at] = unidecode.unidecode(self.json[at])
        assert IsPrimitive(self.json[at]), (at,self.json)
        return self.json[at]

    def __contains__(self, key):
        return key in self.json

    def Validate(self):
        for tk in self.Tokens():
            tk.Validate()
        for r in self.Relations():
            r.Validate()
        assert "index" in self.json and isinstance(self["index"],int), self.json

class Coref:
    def __init__(self, json):
        self.json = json

    def __str__(self):
        return "Coref(%s)" % self["text"]

    def Equals(self, other):
        return self.json == other.json

    def __getitem__(self, at):
        if isinstance(self.json[at], unicode): self.json[at] = unidecode.unidecode(self.json[at])
        assert IsPrimitive(self.json[at]), (at,self.json)
        return self.json[at]

    def __contains__(self, key):
        return key in self.json

    def Validate(self):
        return True

class CorefSet:
    def __init__(self, json):
        self.json = json

    def __getitem__(self, i):
        return Coref(self.json[i])

    def __len__(self):
        return len(self.json)

    def __str__(self):
        return "[%s]" % ", ".join(map(str,map(Coref,self.json)))

    def Equals(self, other):
        return self.json == other.json

    def Validate(self):
        assert isinstance(self.json,list), self.json
        for i in xrange(len(self)):
            self[i].Validate()
            if i > 0:
                assert self[i]["id"] > self[i-1]["id"]


class Parse:
    def __init__(self, json):
        self.json = json

    def CorefLen(self):
        return len(self.json["corefs"])

    def CorefSets(self):
        return [CorefSet(v) for _,v in self.json["corefs"]]

    def CorefSetIds(self):
        return map(int,self.json["corefs"].keys())

    def CorefSet(self, i):
        return CorefSet(self.json["corefs"][str(i)])

    def SentenceLen(self):
        return len(self.json["sentences"])

    def Sentence(self, i):
        return Sentence(self.json["sentences"][i])
    
    def AllRelations(self):
        return [r for i in xrange(self.SentenceLen()) for r in self.Sentence(i).Relations()]

    def PrintRelations(self):
        PrintRelations(self.AllRelations())

    def Equals(self, other):
        return all([self.json["corefs"] == other.json["corefs"], 
                   self.SentenceLen() == other.SentenceLen(),
                   all([self.Sentence(i).Equals(other.Sentence(i)) for i in xrange(self.SentenceLen())])])

    def Validate(self):
        assert len(self.json) == 2
        for i in self.CorefSetIds():
            self.CorefSet(i).Validate()
            assert self.CorefSet(i)[0]["id"] == i
        for i in xrange(self.SentenceLen()):
            self.Sentence(i).Validate()
