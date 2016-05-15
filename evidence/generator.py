import random
import pattern.en as pen
import snode
from unidecode import unidecode
import simplejson
import syntax_rewriter
import sys
import argument_preprocess

def Reload():
    snode.Reload()
    syntax_rewriter.Reload()
    argument_preprocess.Reload()
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
CONTINUOUS = "continuous"
PERFECT = "perfect"
PERFECT_CONTINUOUS = "perfect_continuous"

INDICATIVE = "indicative"
CONDITIONAL_COULD = "conditional_could"
CONDITIONAL_SHOULD = "conditional_should"
CONDITIONAL_WOULD = "conditional_would"
SUBJUNCTIVE = "subjunctive"

WHY = "why"
HOW = "how"
EVIDENCE = "evidence"
SIMILAR = "similar"
IFTHEN = "ifthen"

MALE = "male"
FEMALE = "female"

THING = "thing"
PERSON = "person"
GROUP = "group"
UNCOUNTABLE_THING = "uncountable_thing"

POSSESSIVE = "possessive"
SET = "set"

class MtrException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "MtrException(%s)" % self.msg

def OpenContext(fname):
    ctx = Context()
    json = simplejson.load(open(fname,"r"))
    json = argument_preprocess.Preprocess(json)
    ctx.FromJSON(json)
    return ctx

class Context:
    def __init__(self, debug=False):
        self.entities  = {}
        self.facts     = {}
        self.relations = {}
        self.reverse_relations = {}
        self.justifies = {}
        self.debug = debug

    def AddEntity(self, json):
        self.entities[json["name"]] = Entity(json)

    def GetEntity(self, name):
        if name in self.entities:
            return self.entities[name]
        return Entity({"name":name, "type":THING})

    def AddFact(self, json):
        tid = json["id"]
        assert tid not in self.facts, (tid, self.facts)
        self.facts[tid] = Fact(json)

    def GetFact(self, tid):
        return self.facts[tid]

    def GetFactsByOriginalId(self, tid):
        return [self.GetFact(f) for f in self.facts if self.GetFact(f).OriginalId() == tid]
    
    def AddRelation(self, json):
        if json["gov"] not in self.relations:
            self.relations[json["gov"]] = []
        self.relations[json["gov"]].append(Relation(json))
        if json["dep"] not in self.reverse_relations:
            self.reverse_relations[json["dep"]] = []
        self.reverse_relations[json["dep"]].append(Relation(json))
        if "justifies" in json:
            for j in json["justifies"]:
                if j not in self.justifies:
                    self.justifies[j] = []
                self.justifies[j].append(Relation(json))
        
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
        return self.GetEntity(name).SubjectPronoun(self)

    def ObjectPronoun(self, name):
        return self.GetEntity(name).SubjectPronoun(self)
    
    def PrintAllFacts(self, toText=True):
        for i, f in self.facts.iteritems():
            print "FACT", i
            f.PrintAllSimpleSentences(self, toText)

    def PrintAllRelations(self, toText=True, rewrite=True, involving=None, times=1):
        for k,v in self.relations.iteritems():
            for vi in v:
                if involving is None or involving in [vi.json["gov"], vi.json["dep"], vi.Gov(self).OriginalId(), vi.Dep(self).OriginalId()]:
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
            result.extend([r for r in self.reverse_relations[factId] if r.Type() in [SIMILAR, IFTHEN]])
        if factId in self.justifies:
            result.extend(self.justifies[factId])
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
        return [(k,v.OriginalId()) for k,v in self.facts.iteritems()]

    def EntityTags(self):
        return {t:n for n,e in self.entities.iteritems() for t in e.Tags()}
    
class Entity(object):
    def __init__(self, json):
        self.json = json

    def Tags(self):
        result = self.Names()
        result = [r.replace("#","").replace("%","").replace("@","").replace("'","").replace('"',"").lower() for r in result]
        return result

    def Name(self):
        return self.json["name"]

    def Key(self):
        return self.Name()

    def Names(self):
        result = [] if ("anon" in self.json and self.json["anon"]) else [self.json["name"]]
        if "aliases" in self.json:
            for a in self.json["aliases"]:
                result.append(a)
        return result
    
    def Mtr(self, ctx, entity_type=None):
        if self.Type(ctx) in [PERSON,GROUP,THING,UNCOUNTABLE_THING]:
            tags = { "type" : snode.ENTITY, "key" : self.Key()}
            if entity_type is not None:
                tags["entity_type"] = entity_type
            return P(tags, random.choice(self.Names()))
        if "aliases" in self.json and random.choice([True,False]):
            tags = { "type" : snode.ENTITY, "key" : self.Key()}
            if entity_type is not None:
                tags["entity_type"] = entity_type
            return P(tags, random.choice(self.json["aliases"]))
        elif self.Type(ctx) in [POSSESSIVE]:
            mtrgov = self.Gov(ctx).Mtr(ctx, entity_type = entity_type)
            mtrdep = self.Dep(ctx).Mtr(ctx)
            return P({ "type" : snode.ENTITY, "key" : self.Key()},
                     mtrgov, P({"type" : snode.PUNCT}, "'s"), mtrdep)
        elif self.Type(ctx) in [SET]:
            premtrs = [ctx.GetEntity(m) for m in self.json["members"]]
            random.shuffle(premtrs)
            mtrs = [m for m in premtrs if random.choice([True,False])]
            # for gramatical reasons, we require at least two members of a set to be present
            #
            if len(mtrs) < 2:
                mtrs = [premtrs[0], premtrs[1]]
            mtrs = [m.Mtr(ctx, entity_type = entity_type) for m in mtrs]
            res = [mtrs[0]]
            for i in xrange(1,len(mtrs)):
                res.append(PT("and"))
                res.append(mtrs[i])
            return P({ "type" : snode.ENTITY, "key" : self.Key()}, *res)

    def Person(self, ctx):
        if "person" not in self.json:
            if self.json["type"] in [POSSESSIVE]:
                return self.Dep(ctx).Person(ctx)
            if self.json["type"] == SET:
                return min([ctx.GetEntity(m).Person(ctx) for m in self.json["members"]])
            else:
                return 3
        return self.json["person"]

    def Number(self, ctx):
        if "type" not in self.json or self.json["type"] in [PERSON, THING]:
            return pen.SINGULAR
        if self.json["type"] in [GROUP, UNCOUNTABLE_THING, SET]:
            return pen.PLURAL
        if self.json["type"] in [POSSESSIVE]:
            return self.Dep(ctx).Number(ctx)
        assert False, self.json

    def Gender(self, ctx):
        assert self.json["gender"] in [MALE,FEMALE], self.json
        return self.json["gender"]

    def Type(self, ctx):
        if "type" not in self.json:
            return THING
        assert self.json["type"] in [THING, PERSON, GROUP, UNCOUNTABLE_THING, POSSESSIVE, SET], self.json
        return self.json["type"]

    def Dep(self, ctx):
        return ctx.GetEntity(self.json["dep"])

    def Gov(self, ctx):
        return ctx.GetEntity(self.json["gov"])

    def KnownType(self, ctx):
        return "type" in self.json
    
    def SubjectPronoun(self, ctx):
        if not self.KnownType(ctx):
            return None
        if self.Type(ctx) == "person":
            return "he" if self.Gender(ctx) == MALE else "she"
        if self.Person(ctx) == 1:
            return "we" if self.Number(ctx) == pen.PLURAL else "I"
        return "it" if self.Number(ctx) == 1 else "they"        

    def ObjectPronoun(self, ctx):
        if not self.KnownType(ctx):
            return None
        if self.Type(ctx) == "person":
            return "him" if self.Gender(ctx) == MALE else "her"
        if self.Person(ctx) == 1:
            return "us" if self.Number(ctx) == pen.PLURAL else "me"
        return "it" if self.Number(ctx) == 1 else "them"
        
    def __eq__(self, other):
        return self.Key() == other.Key()
    
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

    def OriginalId(self):
        return self.json["original_id"] if "original_id" in self.json else None
    
    def Subject(self, ctx):
        return ctx.GetEntity(self.json["subject"])

    def Object(self, ctx):
        return ctx.GetEntity(self.json["object"])

    def ReferencesEntity(self, entityName):
        return self.json["subject"] == entityName or self.json["object"] == entityName

    def MtrSubject(self, ctx):
        return self.Subject(ctx).Mtr(ctx, entity_type = snode.PRIMARY_SUBJECT)

    def MtrObject(self, ctx):
        if "object" in self.json:
            return self.Object(ctx).Mtr(ctx, entity_type = snode.PRIMARY_OBJECT)
        return P({})

    def MtrVerbPhrase(self, ctx, tam, negated=False):
        tense, aspect, mood = tam
        if tense is None or aspect is None or mood is None:
            raise MtrException("Cannot use TAM")
        assert aspect in [SIMPLE,PERFECT,CONTINUOUS], aspect
        assert mood in [INDICATIVE,CONDITIONAL_COULD,CONDITIONAL_WOULD,CONDITIONAL_SHOULD,SUBJUNCTIVE]
        if "negated" in self.json and self.json["negated"]:
            negated = not negated
        person = self.Subject(ctx).Person(ctx)
        number = self.Subject(ctx).Number(ctx)
        negator = PT("not") if negated else P({})
        post_inf = P({})
        if self.Relation() == DID:
            infinitive = self.json["infinitive"]
        elif self.Relation() == BE:
            infinitive = "be"
            if number == pen.SINGULAR and self.Object(ctx).Type(ctx) == GROUP:
                post_inf = PT("in")
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
                    if number == pen.SINGULAR:
                        negator = TenseSwitch(tense, PT("didn't"), PT("doesn't"), PT("not")) if negated else P({})
                    else:
                        negator = TenseSwitch(tense, PT("didn't"), PT("don't"), PT("not")) if negated else P({})
                    return PT(helper , negator, PT(infinitive), post_inf)
                else:
                    return PT(Conjugate(infinitive, tense, person, number), post_inf)
            elif aspect == CONTINUOUS:
                # was running / is running / will be running
                vb = PT(PresentParticiple(infinitive))
                if tense == FUTURE:
                    vb = PT(PT("be"), vb)
                    hw = self.Modal(aspect)
                else:
                    hw = Conjugate("be", tense, person, number)
                helper = PT(hw)
                return PT(helper, negator, vb, post_inf)
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
                return PT(helper, negator, vb, post_inf)
        elif mood in [CONDITIONAL_COULD,CONDITIONAL_WOULD, CONDITIONAL_SHOULD]:
            if aspect in [SIMPLE,CONTINUOUS,PERFECT,PERFECT_CONTINUOUS]:
                # could run / can run / will be able to run
                if mood == CONDITIONAL_COULD:
                    helper = TenseSwitch(tense,PT("could", negator),PT("can", negator),PT("will", negator, "be able to"))
                # would have ran / would run / will run
                elif mood == CONDITIONAL_WOULD:
                    helper = TenseSwitch(tense,PT("would", negator, "have"),PT("would", negator),PT("will", negator))
                # should have ran, should run, shall run
                elif mood == CONDITIONAL_SHOULD:
                    helper = TenseSwitch(tense,PT("should", negator, "have"),PT("should", negator),PT("shall", negator))
                vb = infinitive
                if tense == PAST and mood in [CONDITIONAL_SHOULD,CONDITIONAL_WOULD]:
                    vb = Conjugate(infinitive, tense, person, number)
                return PT(helper, vb, post_inf)
        elif mood == SUBJUNCTIVE:
            if aspect in [SIMPLE,CONTINUOUS,PERFECT,PERFECT_CONTINUOUS]:
                # had ran / were running / would be running
                if self.Relation() == BE:
                    helper = TenseSwitch(tense, PT("were", negator, post_inf), PT(negator, "were", post_inf), PT("would", negator, "be", post_inf))
                    return helper
                else:
                    helper = TenseSwitch(tense, PT("had", negator, post_inf), PT(negator, "were", post_inf), PT("would", negator, "be", post_inf))
                    return PT(helper, TenseSwitch(tense, Conjugate(infinitive, tense, person, number), PresentParticiple(infinitive), PresentParticiple(infinitive)))
                

    def MtrAux(self, aux_type):
        aux_type = "aux_" + aux_type
        if aux_type in self.json:
            assert isinstance(self.json[aux_type], list), self.json
            return PT(random.choice(self.json[aux_type]))
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

    def MtrSimple(self, ctx, tam, negated=False):
        return P({"type":snode.FACT, "id":self.json["id"]},
                 self.MtrAux("pre_sub"),
                 P({"type":snode.SUBJECT}, self.MtrSubject(ctx)),
                 self.MtrAux("pre_verb"),
                 P({"type":snode.VERB}, self.MtrVerbPhrase(ctx, tam, negated)),
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
            mood = [m for m in self.Moods() if m != SUBJUNCTIVE]
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

    def IsAvailable(self):
        return "available" not in self.json or self.json["available"]
    
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
        return [INDICATIVE,CONDITIONAL_COULD,CONDITIONAL_WOULD,CONDITIONAL_SHOULD,SUBJUNCTIVE]

    def MF(self, tense=None, aspect=None, mood=None):
        return MaterializableFact(self, tense, aspect, mood)

    def MFI(self, tense=None, aspect=None):
        return MaterializableFact(self, tense, aspect, mood=INDICATIVE)

    def MFSI(self, tense=None, negated=False):
        return MaterializableFact(self, tense, aspect=SIMPLE, mood=INDICATIVE, negated=negated)
    
    def MFPI(self, tense=None):
        return MaterializableFact(self, tense, aspect=PERFECT, mood=INDICATIVE)

    def MFCI(self, tense=None):
        return MaterializableFact(self, tense, aspect=CONTINUOUS, mood=INDICATIVE)

    def MFC(self, tense=None, aspect=None):
        return MaterializableFact(self, tense, aspect=aspect, mood=CONDITIONAL_COULD)
    
    def MFS(self, tense=None, mood=None, negated=False):
        return MaterializableFact(self, tense, aspect=SIMPLE, mood=mood, negated=negated)

    
class MaterializableFact:
    def __init__(self, f, tense=None, aspect=None, mood=None, negated=False):
        self.f = f
        self.tam = f.RTAM(tense, aspect, mood)
        self.negated = negated

    def Mtr(self, ctx):
        return self.f.MtrSimple(ctx, self.tam, negated=self.negated)

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

def Q(*ls):
    return MtrList(snode.SENTENCE, list(ls) + [random.choice([PU("?")])])

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
        assert self.json["type"] in [EVIDENCE, WHY, SIMILAR, HOW, IFTHEN], self.json
        return self.json["type"]

    def FactIds(self, ctx):
        res = [ctx.GetFact(self.json["gov"])]
        if "dep" in self.json:
            res.append(ctx.GetFact(self.json["dep"]))
        return [(f.Id(), f.OriginalId()) for f in res]

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
            ra(S(d.MFI(tense=shared_tense), Cntr("so that"), g.MFS(tense=shared_tense,mood=CONDITIONAL_COULD)))
        elif t == SIMILAR:
            g,d = random.choice([(g,d),(d,g)])
            ra(T(S(g.MFI()), S(d.MFI())))
            ra(S(g.MFI(), Cntr("and"), d.MFI()))
        elif t == IFTHEN:
            ra(S(Cntr("if"), g.MFS(tense=[PAST,PRESENT], mood=SUBJUNCTIVE), PU(","), d.MFS(tense=None, mood=CONDITIONAL_WOULD, negated=True)))
            ra(Q(Cntr("if"), g.MFS(tense=[PAST,PRESENT], mood=SUBJUNCTIVE), PU(","), Cntr("how come"), d.MFSI(tense=[PAST,PRESENT])))
        
        return random.choice(r).Mtr(ctx)
