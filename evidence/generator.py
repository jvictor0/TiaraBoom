import random
import pattern.en as pen
import snode
from unidecode import unidecode
import simplejson
import syntax_rewriter
import sys

def Reload():
    snode.Reload()
    syntax_rewriter.Reload()
    return reload(sys.modules[__name__])

P = snode.SNode

def PT(*nodes):
    if len(nodes) == 1:
        if isinstance(nodes[0],str):
            return P({"type":snode.SYNTAX}, nodes[0])
        else:
            return nodes[0]
    nodes = [PT(n) if isinstance(n,str) else n for n in nodes]
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
CONDITIONAL = "conditional"
CONTINUOUS = "continuous"
PERFECT = "perfect"
PERFECT_CONTINUOUS = "perfect_continuous"

INDICATIVE = "indicative"

WHY = "why"
HOW = "how"
EVIDENCE = "evidence"
SIMILAR = "similar"

MALE = "male"
FEMALE = "femalse"

THING = "thing"
PERSON = "person"
GROUP = "group"

class MtrException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "MtrException(%s)" % self.msg

def OpenContext(fname):
    ctx = Context()
    ctx.FromJSON(simplejson.load(open(fname,"r")))
    return ctx

class Context:
    def __init__(self, debug=False):
        self.entities  = {}
        self.facts     = {}
        self.relations = {}
        self.reverse_relations = {}
        self.debug = debug

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

    def SubjectPronoun(self, name):
        return self.GetEntity(name).SubjectPronoun()

    def ObjectPronoun(self, name):
        return self.GetEntity(name).SubjectPronoun()
    
    def PrintAllFacts(self, toText=True):
        for i, f in self.facts.iteritems():
            print "FACT", i
            f.PrintAllSimpleSentences(self, toText)

    def PrintAllRelations(self, toText=True, rewrite=True, times=1):
        for k,v in self.relations.iteritems():
            for vi in v:
                for _ in xrange(times):
                    snode = vi.Mtr(self)
                    if rewrite:
                        snode = syntax_rewriter.RewriteSyntax(self, snode)
                    if toText:
                        print snode.ToText()
                    else:
                        print snode
                if times > 1:
                    print ""

    def Justifications(self, factId):
        result = []
        if factId in self.relations:
            result.extend(self.relations[factId])
        if factId in self.reverse_relations:
            result.extend([r for r in self.reverse_relations[factId] if r.Type() in [SIMILAR]])
        return result

    def RandomRelation(self):
        return random.choice([r for _, rs in self.relations.iteritems() for r in rs])

    def RandomFact(self, entityName=None):
        facts = []
        if entityName is not None:
            facts = [f for f in self.facts if f.ReferencesEntity(entityName)]
        if len(facts) == 0:
            facts = self.facts        
        return random.choice(facts)
            
    def FactIds(self):
        return self.facts.keys()

    def EntityTags(self):
        return {t:n for n,e in self.entities.iteritems() for t in e.Tags()}
    
class Entity:
    def __init__(self, json):
        self.json = json

    def Tags(self):
        return [self.json["name"].lower()]

    def Name(self):
        return self.json["name"]
    
    def Mtr(self, ctx):
        return P({ "type" : snode.ENTITY, "name" : self.json["name"]},
                 self.json["name"])

    def Person(self):
        if "person" not in self.json:
            return 3
        return self.json["person"]

    def Number(self):
        if "type" not in self.json or self.json["type"] in [PERSON, THING]:
            return pen.SINGULAR
        if self.json["type"] in [GROUP]:
            return pen.PLURAL
        assert False, self.json

    def Gender(self):
        assert self.json["gender"] in [MALE,FEMALE], self.json
        return self.json["gender"]

    def Type(self):
        if "type" not in self.json:
            return THING
        assert self.json["type"] in [THING, PERSON, GROUP]
        return self.json["type"]
        
    def SubjectPronoun(self):
        if "type" not in self.json:
            return None
        if self.Type() == "person":
            return "he" if self.Gender() == MALE else "she"
        if self.Person() == 1:
            return "we" if self.Number() == pen.PLURAL else "I"
        return "it" if self.Number() == 1 else "they"        

    def ObjectPronoun(self):
        if "type" not in self.json:
            return None
        if self.Type() == "person":
            return "him" if self.Gender() == MALE else "her"
        if self.Person() == 1:
            return "us" if self.Number() == pen.PLURAL else "me"
        return "it" if self.Number() == 1 else "them"
        
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

    def Id(self):
        return self.json["id"]
        
    def Subject(self, ctx):
        return ctx.GetEntity(self.json["subject"])

    def Object(self, ctx):
        return ctx.GetEntity(self.json["object"])

    def ReferencesEntity(self, entityName):
        return self.json["subject"] == entityName or self.json["object"] == entityName

    def MtrSubject(self, ctx):
        return self.Subject(ctx).Mtr(ctx)

    def MtrObject(self, ctx):
        return self.Object(ctx).Mtr(ctx)

    def MtrVerbPhrase(self, ctx, tam):
        tense, aspect, mood = tam
        if tense is None or aspect is None or mood is None:
            raise MtrException("Cannot use TAM")
        assert aspect in [SIMPLE,PERFECT,CONTINUOUS], aspect
        assert mood in [INDICATIVE,CONDITIONAL]
        negated = False if "negated" not in self.json else self.json["negated"]
        person = self.Subject(ctx).Person()
        number = self.Subject(ctx).Number()
        negator = PT("not") if negated else P({})
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
                        helper = P({})
                    negator = TenseSwitch(tense, PT("didn't"), PT("doesn't"), PT("not")) if negated else P({})
                    return PT(helper , negator, PT(infinitive))
                else:
                    return PT(Conjugate(infinitive, tense, person, number))
            elif aspect == CONTINUOUS:
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
        elif mood == CONDITIONAL:
            if aspect in [SIMPLE,CONTINUOUS,PERFECT,PERFECT_CONTINUOUS]:
                # could run / can run / will be able to run
                helper = TenseSwitch(tense,PT("could", negator),PT("can", negator),PT("will", negator, "be able to"))
                return PT(helper, infinitive)
        

    def MtrAux(self, aux_type):
        aux_type = "aux_" + aux_type
        if aux_type in self.json:
            return PT(self.json[aux_type])
        else:
            return P({})
            
    def Modal(self, aspect):
        if aspect in [SIMPLE,CONTINUOUS]:
            return "will continue to" if self.IsOngoing() else "will"
        else:
            return "will still" if self.IsOngoing() else "will"

    def Mtr(self, ctx):
        return self.MtrSimpleSentence(ctx, self.RTAM())
        
    def MtrSimpleSentence(self, ctx, tam):
        return P({"type":snode.SENTENCE}, self.MtrSimple(ctx, tam), P({"type":snode.PUNCT}, random.choice(".!")))

    def MtrSimple(self, ctx, tam):
        return P({"type":snode.FACT, "id":self.json["id"]},
                 self.MtrAux("pre_sub"),
                 P({"type":snode.SUBJECT}, self.MtrSubject(ctx)),
                 self.MtrAux("pre_verb"),
                 P({"type":snode.VERB}, self.MtrVerbPhrase(ctx, tam)),
                 self.MtrAux("pre_obj"),
                 P({"type":snode.OBJECT}, self.MtrObject(ctx)),
                 self.MtrAux("post_obj"))

    def PrintAllSimpleSentences(self, ctx, toText=True):
        for tense in self.Tenses():
            for aspect in self.Aspects():
                for mood in self.Moods():
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
        return [INDICATIVE,CONDITIONAL]

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

    def MFC(self, tense=None, aspect=None):
        return MaterializableFact(self, tense, aspect=aspect, mood=CONDITIONAL)
    
    def MFSC(self, tense=None):
        return MaterializableFact(self, tense, aspect=SIMPLE, mood=CONDITIONAL)

    
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
        if "dep" in self.json:
            return ctx.GetFact(self.json["dep"])
        return None

    def Type(self):
        assert self.json["type"] in [EVIDENCE, WHY, SIMILAR, HOW]
        return self.json["type"]

    def FactIds(self):
        if "dep" in self.json:
            return [self.json["gov"],self.json["dep"]]
        return [self.json["gov"]]

    def Mtr(self, ctx):
        g = self.Gov(ctx)
        d = self.Dep(ctx)
        t = self.Type()

        gmfsi = g.MFSI()

        shared_tenses = list(set(g.Tenses()) & set(d.Tenses()))
        shared_tense = random.choice(shared_tenses) if len(shared_tenses) > 0 else PRESENT
        
        r = []
        
        def ra(l):
            r.append(l)            
            
        if t == EVIDENCE:
            ra(T(S(g.MFI()), S(d.MFI())))
            ra(T(S(g.MFI()), S(Cntr("You can tell because"), d.MFI())))
            ra(T(S(g.MFI()), S(Cntr("It's obvious"), PU(","), d.MFI())))
        elif t == WHY:
            dep_tenses = gmfsi.LE()
            ra(S(gmfsi, Cntr("because"), d.MFI(tense=dep_tenses)))
        elif t == HOW:
            ra(S(d.MFI(tense=shared_tense), Cntr("so that"), g.MFSC(tense=shared_tense)))
        elif t == SIMILAR:
            g,d = random.choice([(g,d),(d,g)])
            ra(T(S(g.MFI()), S(d.MFI())))
            ra(S(g.MFI(), Cntr("and"), d.MFI()))
                 
        return random.choice(r).Mtr(ctx)
