from util import *
import grammar as g
from nltk.corpus import wordnet as wn
from pattern.en import singularize, pluralize, conjugate
import pattern.en as pen
import random
from nltk.corpus import stopwords
import global_data as gd
import charicatures as c
import sys
import rewriter as r
from sentence_gen import ConstructSentence

allowed_tenses = [t for t in g._imperfect_tenses if g._is_pos([t])]

period_elt = { "type" : "punctuation", "element" : "." }
comma_elt = { "type" : "punctuation", "element" : "," }

def RewriteWord(g_data, w, word):
    if ' ' in word or '#' in word:
        word = word.split(' ')
        pre = []
        post = []
        the_word = None
        for s in word:
            if s[0] == '#':
                the_word = s[1:]
            else:
                (pre if the_word is None else post).append(s)
    else:
        pre = []
        post = []
        the_word = word
    rr = ''
    if w in ["(It)","(Ht)"]:
        rr = conjugate(the_word)
    if w in ["(Ifa)","(Hfa)"]:
        rr = conjugate(the_word, person=3)
    if w in ["(Ifb)","(Hfb)"]:
        rr = conjugate(the_word, tense = pen.PARTICIPLE)
    if w in ["(Ifc)","(Hfc)"]:
        rr = conjugate(the_word, tense = pen.PAST)
    if w in ["(Ifd)","(Hfd)"]:
        rr = conjugate(the_word, tense = pen.PAST+pen.PAST_PARTICIPLE)
    assert len(rr) != 0, (the_word, w)
    return g.phrase(pre + [rr] + post)
    assert False, (w,word)

def Rewrite(g_data, clause, words):
    assert CountWildcards(clause) == len(words), (words, clause, CountWildcards(clause))
    result = []
    i = 0
    for c in clause:
        if c[0] == '(':
            result.append(RewriteWord(g_data, c,words[i]))
            i = i + 1
        else:
            result.append(c)
    return g.phrase(result)

def RewriteNounPhrase(g_data,noun):
    return [RewriteNoun(g_data,t) for t in noun]

def RewriteNoun(g_data,noun):
    if noun[0].isupper():
        return noun
    if noun.lower() in stopwords.words('english'):
        return noun
    if noun[-1] == "_":
        return noun[:-1]
    res = RandomSynonym(g_data,noun,"n")
    return res

def CountWildcards(phrase):
    return len([a for a in phrase if a[0] == '('])

def JoinPhrase(d,p):
   return g.phrase([x for x in joinit([d],p)]) 

def Finalize(sentence_tree):
    if sentence_tree["type"] == "indep_clause":
        return g.phrase([JoinPhrase('and',sentence_tree["subject"]),
                         sentence_tree["verb"],
                         LKDS(sentence_tree,"object"),
                         LKDS(sentence_tree,"post_adjective")])
    if sentence_tree["type"] == "sentence":
        return r.Finalize(ConstructSentence(g.phrase([Finalize(e) for e in sentence_tree["elements"]])))
    if sentence_tree["type"] == "punctuation":
        return [sentence_tree["element"]]
    if sentence_tree["type"] == "clause":
        return sentence_tree["clause"]
    assert False, sentence_tree["type"]

def PickVerb(g_data, subj, tense, trans, parts):
    verb_infinitive = random.choice(parts["verbs"])
    ego = ["I"] in subj or ["we"] in subj
    plural = len(subj) > 1 or IsPlural(g_data, subj[0][-1])
    print (subj,plural)
    tvt = g.POS_TRANSITIVE_VERB if trans else g.POS_INTRANSITIVE_VERB
    if random.uniform(0,1) < 0.5 and "verb_adapters" in parts:
        verb_schema,the_tense = (g._adapted_verb_ego if ego else g._adapted_verb)(not plural, tense)(tvt)
        verb_schema = g.phrase([verb_schema])
        verb_words = [verb_infinitive] if CountWildcards(verb_schema) == 1 else [random.choice(parts["verb_adapters"]),verb_infinitive]
        return Rewrite(g_data, verb_schema, verb_words), the_tense
    else:
        verb_schema,the_tense = (g._verb_ego if ego else g._verb)(not plural, tense)(tvt)
        return Rewrite(g_data, g.phrase(verb_schema),[verb_infinitive]), the_tense
    
    
def IndepClause(g_data, info, tense=allowed_tenses,used=[]):
    name, parts = random.choice([(i,j) for i,j in info["interests"].items() if not i in used])
    trans = random.choice([True,True,False]) if (parts["trans"] == "both") else (parts["trans"] == "trans")
    subj = random.choice(parts["subjects"])
    if isinstance(subj,list):
        subj = [g.lit_phrase(t) for t in subj]
    else:
        subj = [g.lit_phrase(subj)]
    subj = [RewriteNounPhrase(g_data,t) for t in subj]
    verb, the_tense = PickVerb(g_data, subj, tense, trans, parts)

    result = {
        "type"  : "indep_clause",
        "tense" : the_tense,
        "verb" : verb,
        "subject" : subj,
        "data" : parts
        }
    
    if trans:
        result["object"] = RewriteNounPhrase(g_data,g.lit_phrase(random.choice(parts["objects"])))

    if "post_adjectives" in parts and random.uniform(0,1) < 0.3:
        result["post_adjective"] = g.lit_phrase(random.choice(parts["post_adjectives"]))
    
    return result

def RandomSynonym(g_data,word,sense):
    plural = False
    if sense == "n" and IsPlural(g_data,word):
        word = singularize(word)
        plural = True
    res = random.choice(Synonyms(word,sense))
    if sense == "n" and plural:
        return pluralize(res)
    if word.islower():
        res = res.lower()
    return res

def Synonyms(word,sense):
    syns = wn.synsets(word, sense) if not "." in word else [wn.synset(word)]
    if len(syns) == 0:
        return [word]
    return [w.name() for ws in syns[0].lemmas() for w in [ws]*(1+ws.count()) if not "_" in ws.name()]

def IsPlural(g_data, pluralForm):
    return "(Kf)" in g_data.DictLookup(pluralForm)

def WithTransformation(g_data, indep):
    assert indep["type"] == "indep_clause"
    if "I" in indep["subject"] and len(indep["subject"]) > 1:
        withs = [p for p in indep["subject"] if p != "I" and random.uniform(0,1) > 0.33]
        indep["subject"] = [i for i in indep["subject"] if i not in withs]
        if len(withs) > 0:
            if random.choice([True,False]):
                indep["post_adjective"] = g.phrase([LKDE(indep, "post_adjective"), "with",  JoinPhrase('and',withs)])
            else:
                indep["post_adjective"] = g.phrase(["with", JoinPhrase('and',withs),LKDS(indep, "post_adjective")])
            indep["verb"], _= PickVerb(g_data, indep["subject"], [indep["tense"]], "object" in indep, indep["data"])
    return indep

def BeingTargetTransformation(g_data, indep):
    return BeingTargetThisTransformation(g_data, BeingTargetSubjectTransformation(g_data,indep))

def BeingTargetSubjectTransformation(g_data, indep):
    if indep["type"] != "indep_clause":
        return indep
    if len(LKD(LKD(indep["data"],"being_targets",{}),"subject",[])) == 0 or random.uniform(0,1) < 0.6:
        return indep
    tense = indep["tense"]
    pro = Pronoun(g_data, indep["subject"], indep["data"])
    plural = pro in ["we","they"]
    ego    = pro in ["I","we"]
    if g._is_past_any([tense]):
        conj,vb1,vb2,vb3 = random.choice([("and","am","is","are"),
                                          ("and now","am","is","are"),
                                          ("until","was","was","were"),
                                          ("and soon","will be","will be","will be")])
    elif g._is_pres_any([tense]):
        conj,vb1,vb2,vb3 = random.choice([("and","am getting","is getting","are getting"),
                                          ("and now","am getting","is getting","are getting"),
                                          ("until","get","gets","get"),
                                          ("and soon","will be","will be","will be")])
    elif g._is_futr_any([tense]):
        conj,vb1,vb2,vb3 = random.choice([("until","get","gets","get"),
                                          ("and soon","will be","will be","will be")])
    else:
        assert False, tense
    vb = vb3 if plural else vb1 if ego else vb2
    snd_clause = g.phrase([conj,pro,vb,g.lit_phrase(random.choice(indep["data"]["being_targets"]["subject"]))])
    return { "type":"sentence", "elements":[indep,Clause(snd_clause)] }

def BeingTargetThisTransformation(g_data, indep):
    if indep["type"] != "indep_clause":
        return indep
    if len(LKD(LKD(indep["data"],"being_targets",{}),"this",[])) == 0 or random.uniform(0,1) < 0.6:
        return indep
    tense = indep["tense"]
    pro = "it"
    if g._is_past_any([tense]):
        conj,vb = random.choice([("and","was"),
                                 (".","was")])
    elif g._is_pres_any([tense]):
        conj,vb = random.choice([("and","is"),
                                (".","is")])
    elif g._is_futr_any([tense]):
        conj,vb = random.choice([("and","will be")])
    else:
        assert False, tense
    snd_clause = g.phrase([conj,pro,vb,g.lit_phrase(random.choice(indep["data"]["being_targets"]["this"]))])
    return { "type":"sentence", "elements":[indep,Clause(snd_clause)] }


def Pronoun(g_data, subj, parts):
    plural = len(subj) > 1 or IsPlural(g_data, subj[0][-1])
    ego = ["I"] in subj or ["we"] in subj
    if ego and plural:
        return "we"
    if ego and not plural:
        return "I"
    if not ego and plural:
        return "they"
    else:
        return LKD(LKD(parts,'pronouns',{}),subj[0][0],"it")

def Clause(cl):
    return {
        "type" : "clause",
        "clause" : cl
        }

def Sentence(indep):
    return {
        "type" : "sentence",
        "elements" : [indep, period_elt]
        }

def TestCharicature(char, reps=100):
    g_data = gd.GlobalData()
    for i in xrange(100):
        print RunCharicature(g_data, char)

def RunCharicature(g_data, char):
    return Finalize(Sentence(
            BeingTargetTransformation(g_data,
                                      WithTransformation(g_data,
                                                         IndepClause(g_data, char)))))
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
        TestCharicature(c.housewife)
    else:
        TestCharicature(c.socialbots[sys.argv[1]])
