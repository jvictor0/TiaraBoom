# A more general sentence generator
from util import *
import smart_sentence as ss
import sentence_gen as sg
import grammar as g
import rewriter as r
import random
import global_data as gd

# So the first smart sentence generator (written on the caltrain) is an interesting prototype, but a bit of a failure.
# Its too hard to use and too hard to extend and has tons of confusing bugs.
#
# For this reason Im going to create a more general sentence generator built of composable and replaceable parts.
# Should require very little expertise to add new types of sentences, etc.

# A SentenceGen is a list of Clause's.
# A clause is a function which takes g_data and an arguments dict and returns either json dict.
# The json dict should contain the fields "name" and "result", but may contain arbitrary other fields as well.
# The "name" field is a string which must be unique among the Clause's in that SentenceGen.
# The "result" field is a list of spaceless strings which, if concatinated with appropriate spacing, represented the output of that clause.
# The arguments dict shall contain a field for each name of a prior Clause function.
# The Clause's are evaluated left to right.
# A Clause may modify previous clauses, but test this heavier.  
# The following is an extremely simple example.


# notice drink_liquor_subject returns fields "singular" and "ego", which are read by drink_liquor_verb

def drink_liquor_subject(g_data, args):
    subj, singular, ego = random.choice([("Jimmy",True,False),
                                         ("Jimmy and I",False,True),
                                         ("I",True,True)])
    return {
        "name" : "subject",
        "result" : g.lit_phrase(subj),
        "singular" : singular,
        "ego"   : ego
        }

def drink_liquor_verb(g_data, args):
    verb_infinitive = random.choice(["drink","have"])
    verb, tense = ss.Verb(g_data, verb_infinitive, args["subject"]["ego"], args["subject"]["singular"])
    return {
        "name" : "verb",
        "result" : verb,
        "tense" : tense
        }

def drink_liquor_object(g_data, args):
    if args["subject"]["result"] == g.lit_phrase("Jimmy"):
        drink = "whisky"
    else:
        drink = "wine"
    return {
        "name" : "object",
        "result" : g.lit_phrase(drink),
        }    


def drink_liquor_when(g_data, args):
    if g._is_futr_any([args["verb"]["tense"]]):
        return SimpleResult("when", g.lit_phrase(random.choice(["tonight","tomorrow","this weekend"])))
    return EmptyResult("when")

drink_liquor_sentencegen = [drink_liquor_subject, drink_liquor_verb, drink_liquor_object,drink_liquor_when]

####################################
#### BEGIN ACTUAL CODE #############
####################################

def RunSentenceGen(g_data, sentence_gen, finalize=True):
    args = {}
    result = []
    for clause in sentence_gen:
        clause_instance = clause(g_data, args)
        assert "result" in clause_instance, "you forgot the result, gbop!"
        assert "name" in clause_instance, "you forgot the name, gbop!"
        if isinstance(clause_instance["result"],basestring):
            clause_instance["result"] = g.lit_phrase(clause_instance["result"])
            g_data.TraceWarn("I did you a favor, but you really should make result a list of strings instead of a string.  lit_phrase will even do this for you!  You're being a gbop!")
        assert isinstance(clause_instance["result"], list) and all(isinstance(t,basestring) for t in clause_instance["result"]), "result ought to be list of strings, not %s.  Did you forget to call lit_phrase?" % clause_instance["result"]
        assert not clause_instance["name"] in args, "the name %s was used twice!" % clause_instance["name"]
        args[clause_instance["name"]] = clause_instance
        result.append(clause_instance["name"])
    if finalize:
        return r.Finalize(sg.ConstructSentence(g.phrase([args[rg]["result"] for rg in result])))
    return g.phrase([args[rg]["result"] for rg in result])


#################################################
##### END ACTUAL CODE... WOW, THAT WAS EASY! ####
#################################################


# It would be a massive pain in the ass to generate all these functions by hand every time.
# Especially since most of them will be rather similar.
# Luckily, we can make clause generators to fix this lil problem!

def SimpleResult(name,result): # because DRY
    return {
        "name" : name,
        "result" : result
        }
def EmptyResult(name):
    return SimpleResult(name,[])

def EmptyClause(name):
    return lambda g_data, args: EmptyResult(name)


# actually does a bit of rewriting
# things of the form _name_field are replaced with args[name][field], for instance, _subject_pronoun
# Further, things starting with hashtags with _name are conjugated based on args[name][tense],
# for instance, #get_verb is conjugated to the same conjugation as the the verb clause,
# unless there is a third underscore, in which case that is the pronoun used,
# for instance #get_verb_it will be conjugated with the tense from verb but agreeing with subject pronoun "it"
#
def SimpleReferentialResult(g_data, args, name, result):
    for i in xrange(len(result)):
        if result[i][0] == "_":
            prior_name, field = result[i].split('_')
            result[i] = args[prior_name][field]
    return SimpleResult(name, result)
    
def subject_clause(subjects, suffix=""):
    def f(g_data, args):
        subj, singular, ego = random.choice(subjects)
        return {
            "name" : "subject" + suffix,
            "result" : subj if isinstance(subj,list) else g.lit_phrase(subj),
            "singular" : singular,
            "ego"   : ego
            }
    return f

def verb_clause(infinitives, suffix = "",subject = "subject", tenses = ss.allowed_tenses):
    def f(g_data, args):
        verb_infinitive = random.choice(infinitives)
        verb, tense = ss.Verb(g_data, verb_infinitive, args[subject]["ego"], args[subject]["singular"], tenses)
        return {
            "name" : "verb" + suffix,
            "result" : verb,
            "tense" : tense,
            "ego" : args[subject]["ego"],
            "singular" : args[subject]["singular"]
            }
    return f

def adapted_verb_clause(adapters, infinitives, suffix = "", subject = "subject",tenses = ss.allowed_tenses):
    def f(g_data, args):
        verb_infinitive = random.choice(infinitives)
        verb_adapter = random.choice(adapters)
        verb, tense = ss.AdaptedVerb(g_data, verb_infinitive, verb_adapter, args[subject]["ego"], args[subject]["singular"], tenses)
        return {
            "name" : "verb" + suffix,
            "result" : verb,
            "tense" : tense,
            "ego" : args[subject]["ego"],
            "singular" : args[subject]["singular"]
            }
    return f


def object_clause(objects, suffix=""):
    return lambda g_data, args: SimpleResult("object"+suffix,g.lit_phrase(random.choice(objects)))

# and our drink_liquor_example:
# Notice that we mix the reusable stuff with the custom code for making Jimmy drink whisky
#
drink_liquor_subject2 = subject_clause([("Jimmy",True,False),("Jimmy and I",False,True),("I",True,True)])
drink_liquor_verb2 = verb_clause(["drink","have"])
drink_liquor_sentencegen2 = [drink_liquor_subject2,drink_liquor_verb2,drink_liquor_object,drink_liquor_when]


# We can even take two SentenceGen's and smack em together to make a new one!
# (works so long as both clauses have difference names, of course, which is the reason for the suffix field above)
#
def SimpleConjunction(clause1, conjunction, clause2, preconj=",",postconj="",sufix=""):
    conj_result = g.phrase([prconj,g.lit_phrase(conjunction),postconj])
    conj = lambda g_data, args: SimpleResult("conjunction"+suffix,conj_result)
    return clause1 + [conj] + clause2


# Given a bunch of SentenceGens with weights, pick one and generate
#
def RunWeightedSentenceGens(g_data, sentences, finalize=True):
    return RunSentenceGen(g_data,g.RandomChoice(sentences),finalize)

# returns a Clause from a bunch of SentencesGens by randomly picking one and returning the result.
# Note this ignores prior args and returned args won't be visible, but thats ok.
#
def WeightedSentenceGensToClause(name, sentences):
    return lambda g_data, args: SimpleResult(name, RunWeightedSentenceGens(g_data, sentences, False))

def InterestToClause(g_data, interest):
    new_subjects = []
    for subj in interest["subjects"]:
        if isinstance(subj,list):
            subj = [g.lit_phrase(t) for t in subj]
        else:
            subj = [g.lit_phrase(subj)]
        ego = ["I"] in subj or ["we"] in subj
        plural = len(subj) > 1 or ss.IsPlural(g_data, subj[0][-1])
        subj = ss.JoinPhrase('and',subj)
        new_subjects.append((subj,not plural, ego))
    subject = subject_clause(new_subjects)
    verb = verb_clause(interest["verbs"])

    if "verb_adapters" in interest:
        verb_adapted = adapted_verb_clause(interest["verb_adapters"],interest["verbs"])
    else:
        verb_adapted = verb

    if interest["trans"] == "trans":
        obj = object_clause(interest["objects"])
    else:
        obj = EmptyClause("object")
    
    if "secondary_clauses" in interest:
        secondary = lambda g_data, args: \
            SimpleReferentialResult(g_data, args, "secondary_clause",
                                    random.choice([t for f,t in interest["secondary_clause"] if f(g_data,args)]))
    else:
        secondary = EmptyClause("secondary_clause")

    result = [
        ([subject,verb,obj],1),
        ([subject,verb_adapted,obj],1.5),
        ([subject,verb,obj,secondary],1.5),
        ([subject,verb_adapted,obj,secondary],2.5),
        ]
    return WeightedSentenceGensToClause("sentence", result)

def RunInterestFromClause(g_data,interest):
    if g_data is None:
        g_data = gd.GlobalData()
    return RunSentenceGen(g_data,[InterestToClause(g_data,interest)])
