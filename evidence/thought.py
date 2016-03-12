import random
import pattern.en as pen
import snode
from unidecode import unidecode

P = snode.SNode

def PT(*nodes):
    return P({"type":snode.SYNTAX}, *nodes)

ONGOING = "ongoing"
RECURRING = "recurring"
EVENT = "event"

PAST = "past"
PRESENT = "present"
FUTURE = "future"

DID = "did"
BE = "be"

SIMPLE = "simple"
CONTINUOUS = "continuous"
PERFECT = "perfect"
PERFECT_CONTINUOUS = "perfect_continuous"

INDICATIVE = "indicative"

WHY = "why"
EVIDENCE = "evidence"
SIMILAR = "similar"

class MtrException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "MtrException(%s)" % self.msg

class Context:
    def __init__(self):
        self.entities  = {}
        self.facts     = {}
        self.relations = {}
        self.reverse_relations = {}

    def AddEntity(self, json):
        self.entities[json["name"]] = Entity(json)

    def GetEntity(self, name):
        if name in self.entities:
            return self.entities[name]
        return Entity({"name":name})

    def AddFact(self, json):
        if "id" not in json:
            tid = len(self.facts)
            while tid in self.facts:
                tid = tid + 1
                json["id"] = tid
        tid = json["id"]
        assert tid not in self.facts, (tid, self.facts)
        self.facts[tid] = Fact(json)

    def GetFact(self, tid):
        return self.facts[tid]
        
    def AddRelation(self, json):
        if json["gov"] not in self.relations:
            self.relations[json["gov"]] = []
        self.relations[json["gov"]].append(Relation(json))
        if json["dep"] not in self.reverse_relations:
            self.reverse_relations[json["dep"]] = []
        self.reverse_relations[json["dep"]].append(Relation(json))
        
    def FromJSON(self, json):
        for k in ["entities","facts","relations"]:
            if k not in json:
                json[k] = []
        for e in json["entities"]:
            self.AddEntity(e)
        for f in json["facts"]:
            self.AddFact(f)
        for r in json["relations"]:
            self.AddRelation(r)

    def PrintAllFacts(self, toText=True):
        for _, f in self.facts.iteritems():
            f.PrintAllSimpleSentences(self, toText)

    def PrintAllRelations(self, toText=True, times=1):
        for k,v in self.relations.iteritems():
            for vi in v:
                for _ in xrange(times):
                    if toText:
                        print vi.Mtr(self).ToText()
                    else:
                        print vi.Mtr(self)
                if times > 1:
                    print ""
                    
class Entity:
    def __init__(self, json):
        self.json = json

    def Mtr(self, ctx):
        return P({ "type" : snode.ENTITY, "name" : self.json["name"]},
                 self.json["name"])

    def Person(self, ctx):
        if "person" not in self.json:
            return 3
        return self.json["person"]

    def Number(self, ctx):
        if "type" not in self.json or self.json["type"] in ["person"]:
            return pen.SINGULAR
        if self.json["type"] in ["group"]:
            return pen.PLURAL
        assert False, self.json

    def __eq__(self, other):
        return self.json["name"] == other.json["name"]

        
def TenseSwitch(tense, past, present, future):
    if tense == PAST:
        return past
    if tense == PRESENT:
        return present
    if tense == FUTURE:
        return future

def TenseCmp(t1, t2):
    if t1 == t2:
        return 0
    if t1 == PAST or t2 == FUTURE:
        return -1
    if t2 == PAST or t1 == FUTURE:
        return 1
    
def Unidecode(word):
    if isinstance(word, unicode):
        return unidecode(word)
    return word
    
def PresentParticiple(word):
    return Unidecode(pen.conjugate(word, aspect="progressive"))

def PastParticiple(word):
    return Unidecode(pen.conjugate(word, tense="past", aspect="progressive"))

def Conjugate(word, tense, person, number):
    return Unidecode(pen.conjugate(word, tense=tense, person=person, number=number))

class Fact:
    def __init__(self, json):
        self.json = json

    def Subject(self, ctx):
        return ctx.GetEntity(self.json["subject"])

    def Object(self, ctx):
        return ctx.GetEntity(self.json["object"])

    def MtrSubject(self, ctx):
        return self.Subject(ctx).Mtr(ctx)

    def MtrObject(self, ctx):
        return self.Object(ctx).Mtr(ctx)

    def MtrVerbPhrase(self, ctx, tam):
        tense, aspect, mood = tam
        if tense is None or aspect is None or mood is None:
            raise MtrException("Cannot use TAM")
        assert aspect in [SIMPLE,PERFECT,CONTINUOUS], aspect
        assert mood in [INDICATIVE]
        negated = False if "negated" not in self.json else self.json["negated"]
        person = self.Subject(ctx).Person(ctx)
        number = self.Subject(ctx).Number(ctx)
        negator = PT("not") if negated else P({},"")
        if self.Relation() == DID:
            infinitive = self.json["infinitive"]
        elif self.json["relation"] == BE:
            infinitive = "be"
        else:
            assert False, ("cannot conjugate ", self.json)
        if mood == INDICATIVE:
            if aspect == SIMPLE:
                # ran / runs / will run
                if tense == FUTURE or negated:
                    if tense == "future":
                        helper = PT(self.Modal(aspect))
                    else:
                        helper = P({},"")
                    negator = TenseSwitch(tense, PT("didn't"), PT("doesn't"), PT("not")) if negated else P({},"")
                    return PT(helper , negator, PT(infinitive))
                else:
                    return PT(Conjugate(infinitive, tense, person, number))
            if aspect == CONTINUOUS:
                # was running / is running / will be running
                vb = PT(PresentParticiple(infinitive))
                if tense == FUTURE:
                    vb = PT(PT("be"), vb)
                    hw = self.Modal(aspect)
                else:
                    hw = Conjugate("be", tense, person, number)
                helper = PT(hw)
                return PT(helper, negator, vb)
            elif aspect in [PERFECT,PERFECT_CONTINUOUS]:
                # had run /  has run / will have run
                # had been running /  has been running / will have been running
                vb = PT(PastParticiple(infinitive))
                if aspect == PERFECT_CONTINUOUS:
                    vb = PT(PT("been"), PT(PresentParticiple(infinitive)))
                if tense == FUTURE:
                    vb = PT(PT("have"), vb)
                    hw = self.Modal(aspect)
                else:
                    hw = Conjugate("have", tense, person, number)
                helper = PT(hw)
                return PT(helper, negator, vb)

    def Modal(self, aspect):
        if aspect in [SIMPLE,CONTINUOUS]:
            return "will continue to" if self.IsOngoing() else "will"
        else:
            return "will still" if self.IsOngoing() else "will"
        
    def MtrSimpleSentence(self, ctx, tam):
        return P({"type":snode.SENTENCE}, self.MtrSimple(ctx, tam))

    def MtrSimple(self, ctx, tam):
        return P({"type":snode.FACT, "id":self.json["id"]},
                 P({"type":snode.SUBJECT}, self.MtrSubject(ctx)),
                 P({"type":snode.VERB},    self.MtrVerbPhrase(ctx, tam)),
                 P({"type":snode.OBJECT},  self.MtrObject(ctx)))

    def PrintAllSimpleSentences(self, ctx, toText=True):
        for tense in self.Tenses():
            for aspect in self.Aspects():
                for mood in self.Moods():
                    print tense, aspect, mood
                    if toText:
                        print "    ", self.MtrSimpleSentence(ctx, (tense, aspect, mood)).ToText()
                    else:
                        print self.MtrSimpleSentence(ctx, (tense, aspect, mood))

    def RTAM(self, tense=None, aspect=None, mood=None):
        if tense is None:
            tense = self.Tenses()
        elif isinstance(tense, str):
            tense = [tense]
        tense = [t for t in tense if t in self.Tenses()]
        if aspect is None:
            aspect = self.Aspects()
        elif isinstance(aspect, str):
            aspect = [aspect]
        aspect = [a for a in aspect if a in self.Aspects()]
        if mood is None:
            mood = self.Moods()
        elif isinstance(mood, str):
            mood = [mood]
        mood = [m for m in mood if m in self.Moods()]
        try:
            return (random.choice(tense), random.choice(aspect), random.choice(mood))
        except Exception as e:
            print e
            print tense, aspect, mood
            raise
            
    def Frequency(self):
        if "frequency" not in self.json:
            return ONGOING
        assert self.json["frequency"] in [EVENT,ONGOING,RECURRING], self.json
        return self.json["frequency"]

    def IsOngoing(self):
        return self.Frequency() == ONGOING
    
    def Relation(self):
        if "relation" not in self.json:
            return DID
        assert self.json["relation"] in [DID,BE]
        return self.json["relation"]
    
    def Tenses(self):
        if "tenses" not in self.json:
            return [PAST,PRESENT,FUTURE]
        for t in self.json["tenses"]:
            assert t in [PAST,PRESENT,FUTURE], t
        return self.json["tenses"]
                
    def Aspects(self):        
        if self.Relation() == DID:
            if not self.IsOngoing():
                return [SIMPLE,PERFECT]
            else:
                return [SIMPLE,CONTINUOUS]
            return [SIMPLE,CONTINUOUS,PERFECT]
        if self.Relation() == BE:
            if not self.IsOngoing():
                return [SIMPLE,PERFECT]
            return [SIMPLE]
            
    def Moods(self):
        return [INDICATIVE]

    def MF(self, tense=None, aspect=None, mood=None):
        return MaterializableFact(self, tense, aspect, mood)

    def MFI(self, tense=None, aspect=None):
        return MaterializableFact(self, tense, aspect, mood=INDICATIVE)

    def MFSI(self, tense=None):
        return MaterializableFact(self, tense, aspect=SIMPLE, mood=INDICATIVE)
    
    def MFPI(self, tense=None):
        return MaterializableFact(self, tense, aspect=PERFECT, mood=INDICATIVE)

    def MFCI(self, tense=None):
        return MaterializableFact(self, tense, aspect=CONTINUOUS, mood=INDICATIVE)

    
class MaterializableFact:
    def __init__(self, f, tense=None, aspect=None, mood=None):
        self.f = f
        self.tam = f.RTAM(tense, aspect, mood)

    def Mtr(self, ctx):
        return self.f.MtrSimple(ctx, self.tam)

    def Tense(self):
        return self.tam[0]
    
    def LE(self):
        return [a for a in [PAST,PRESENT,FUTURE] if TenseCmp(a, self.tam[0]) <= 0]

    def LT(self):
        return [a for a in [PAST,PRESENT,FUTURE] if TenseCmp(a, self.tam[0]) < 0]
    
    def GE(self):
        return [a for a in [PAST,PRESENT,FUTURE] if TenseCmp(a, self.tam[0]) >= 0]

    def GT(self):
        return [a for a in [PAST,PRESENT,FUTURE] if TenseCmp(a, self.tam[0]) > 0]

    
class Cntr:
    def __init__(self, text):
        self.text = text

    def Mtr(self, ctx):
        return PT(self.text)

class MtrList:
    def __init__(self, pos, lst):
        self.pos = pos
        self.lst = lst

    def Mtr(self, ctx):
        return P({"type":self.pos}, *[a.Mtr(ctx) for a in self.lst])

class LP:
    def __init__(self, pos, *ls):
        self.pos = pos
        self.ls = ls

    def Mtr(self, ctx):
        return P({"type":self.pos}, *self.ls)

def PU(punc):
    return LP(snode.PUNCT, punc)
    
def S(*ls):
    return MtrList(snode.SENTENCE, list(ls) + [random.choice([PU("."), PU("!")])])

def T(*ls):
    return MtrList(snode.SYNTAX, list(ls))

class Relation:
    def __init__(self, json):
        self.json = json

    def Gov(self, ctx):
        return ctx.GetFact(self.json["gov"])
    
    def Dep(self, ctx):
        return ctx.GetFact(self.json["dep"])

    def Type(self):
        assert self.json["type"] in [EVIDENCE, WHY, SIMILAR]
        return self.json["type"]

    def Mtr(self, ctx):
        g = self.Gov(ctx)
        d = self.Dep(ctx)
        t = self.Type()
        
        gmfsi = g.MFSI()
        r = []
        
        def ra(l):
            r.append(l)            
            
        if t == EVIDENCE:
            ra(T(S(g.MFI()), S(d.MFI())))
            ra(T(S(g.MFI()), S(Cntr("You can tell because"), d.MFI())))
            ra(T(S(g.MFI()), S(Cntr("It's obvious"), PU(","), d.MFI())))
        if t == WHY:
            dep_tenses = gmfsi.LE()
            ra(S(gmfsi, Cntr("because"), d.MFI(tense=dep_tenses)))
        if t == SIMILAR:
            g,d = random.choice([(g,d),(d,g)])
            ra(T(S(g.MFI()), S(d.MFI())))
            ra(S(g.MFI(), Cntr("and"), d.MFI()))

        return random.choice(r).Mtr(ctx)
