import random

def phrase(l):
    if isinstance(l,list):
        result = [item for sublist in l for item in phrase(sublist) if item != ""]
        assert all([not a is None for a in result])
        return result
    return [l]

def rand_word(a,b,c=""):
    if b == True:
        b = "t"
    if b == False:
        b = "f"
    return "(" + a + b + c + ")"

def cm_lit_phrase(str):
    return phrase([_comma, lit_phrase(str)])

def lit_phrase(str):
    return phrase(str.replace(","," ,").replace("."," .").replace("?"," ?").replace("!"," !").replace(";"," ;").split(' '))

def RandomChoice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False

def RandomFilteredChoice(choices):
    total = sum([w if b else 0 for b, c, w in choices])
    r = random.uniform(0, total)
    upto = 0
    for b, c, w in choices:
        if not b:
            continue
        if upto + w > r:
            return c
        upto += w
    print choices
    assert False


you = "you"
me = "me"
I = "I"
we = "we"
they = "they"
he = "he"
she = "she"
it = "it"
sing = "sing"
plural = "plural"
them = "then"

def fix_helper(adverb, verb):
    result = []
    for i,v in enumerate(verb):
        if not is_helper(v):
            break
    return phrase([verb[:i],adverb,verb[i:]])


_comma = lit_phrase(",")
_question = lit_phrase("?")
_hyphen = lit_phrase("-")


POS_VERBER = '_Kv'

POS_ANOMALOUS_VERB = 'G'

POS_TRANSITIVE_VERB = 'H'

POS_INTRANSITIVE_VERB = 'I'

POS_TRANS_INTRANS_VERB = 'J'

POS_COUNTABLE_NOUN = 'K'

POS_UNCOUNTABLE_NOUN = 'L'

POS_COUNT_UNCOUNT_NOUN = 'M'

POS_PROPER_NOUN = 'N'

POS_ADJECTIVE = 'O'

POS_ADVERB = 'P'

POS_PRONOUN = 'Q'

POS_DEFINITE_ARTICLE = 'R'

POS_INDEFINITE_ARTICLE = 'S'

POS_PREPOSITION = 'T'

POS_PREFIX = 'U'

POS_CONJUNCTION = 'V'

POS_INTERJECTION = 'W'

POS_PARTICLE = 'X'

POS_ABBREVIATION = 'Y'

POS_NOT_CLASSIFIED = 'Z'

POS_FIRST = POS_ANOMALOUS_VERB

POS_LAST = POS_NOT_CLASSIFIED

VERB_INFINITIVE = 't'

VERB_CONJUGATED = 'f'

CONJ_3RD_SING = 'a'

CONJ_PRESENT_PART = 'b'

CONJ_PAST = 'c'

CONJ_PAST_PART = 'd'

CONJ_UNKNOWN = 'e'

CONJ_CONTRACT_PRONOUN = 'f'

CONJ_CONTRACT_NOT = 'g'

CONJ_OTHER_CONTRACTION = 'h'

NOUN_SINGULAR = True

NOUN_PLURAL = False

PROPER_NOUN_FORENAME = 'l'

PROPER_NOUN_REGION = 'm'

PROPER_NOUN_CITY = 'n'

PROPER_NOUN_OTHER = 'o'

ADJECTIVE_PREDICATE = 'p'

ADJECTIVE_ATTRIBUTE = 'q'

ADJECTIVE_COMPARE = 'r'

ADJECTIVE_SUPERLATIVE = 's'

ADJECTIVE_HYPHEN = 't'

ADJECTIVE_OTHER = 'f'

ADJECTIVE_GOOD = 't'

ADVERB_NORMAL = 'u'

ADVERB_CONJUNCTIVE = '^'

ADVERB_INTERROGATIVE = 'v'

ADVERB_RELATIVE = 'w'

ADVERB_PARTICLE = '_'

CONJUNCTION_COORDINATING = '~'

CONJUNCTION_SUBORDINATING = '^'

CONJUNCTION_OTHER = '_'

PRONOUN_NORMAL = 'x'

PRONOUN_INTERROGATIVE = 'y'

PRONOUN_RELATIVE = 'z'

PRONOUN_POSSESSIVE = 'A'

_blank = lit_phrase("")

_nil = ""

def _nil_func0():
    return _nil

def _nil_func2(x, y):
    return _nil

_period = lit_phrase(".")

_dotdotdot = lit_phrase("...")

_exclamation = lit_phrase("!")

_semicolon = lit_phrase(";")

_and = lit_phrase("and")

_or = lit_phrase("or")

_that = lit_phrase("that")

_which = lit_phrase("which")

_not = lit_phrase("not")

_I = lit_phrase("I")

_we = lit_phrase("we")

_a = lit_phrase("a")

_an = lit_phrase("an")

_the = lit_phrase("the")

_than = lit_phrase("than")

_some = lit_phrase("some")

_those = lit_phrase("those")

_would = lit_phrase("would")

_wouldnt = lit_phrase("wouldn't")

_will = lit_phrase("will")

_should = lit_phrase("should")

_may = lit_phrase("may")

_might = lit_phrase("might")

_could = lit_phrase("could")

_must = lit_phrase("must")

_am = lit_phrase("am")

_is = lit_phrase("is")

_isnt = lit_phrase("isn't")

_arent = lit_phrase("aren't")

_like = lit_phrase("like")

_are = lit_phrase("are")

_was = lit_phrase("was")

_wasnt = lit_phrase("wasn't")

_were = lit_phrase("were")

_werent = lit_phrase("weren't")

_to = lit_phrase("to")

_be = lit_phrase("be")

_been = lit_phrase("been")

_has = lit_phrase("has")

_have = lit_phrase("have")

_had = lit_phrase("had")

_one = lit_phrase("one")

_two = lit_phrase("two")

_three = lit_phrase("three")

_four = lit_phrase("four")

_five = lit_phrase("five")

_six = lit_phrase("six")

def _possible_sub_clause(begin, end):
    return RandomChoice([(_nil,12),
                         (phrase([begin, _subordinating_conjunction(), _indep_clause(None)[0],end]),1)])

def _possible_adverb(begin, end):
    return RandomChoice([(phrase([rand_word(POS_ADVERB, ADVERB_NORMAL), end]),1),
                         (_nil,3000000000)])


def rand_plural():
    return RandomChoice([(True,2),
                         (False,1)])

def _indep_clause(tense):
    return _indep_clause_pl(rand_plural(), tense)

def _subjunctive_clause():
    return _subjunctive_clause_pl(rand_plural())

def _conditional_clause():
    return _conditional_clause_pl(rand_plural())

def _indep_clause_pl(p,t):
    if t == "command_pos" or t == "command_neg":
        return _command(p)
    if t == "being_cond":
        return _being_clause_conditional(p), t
    return RandomFilteredChoice([(True,lambda: _indep_clause_pl_intrans_3(p,t),2),
                                 (True,lambda: _indep_clause_pl_trans_3(p,t),3),
                                 (True,lambda: _indep_clause_pl_intrans_ego_3(p,t),2),
                                 (True,lambda: _indep_clause_pl_trans_ego_3(p,t),3),
                                 (_is_cont(t),lambda: _being_clause(p,t),5)])()

def _command():
    return RandomChoice([(lambda : phrase([rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), you), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([_possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), you)]),1),
                         (lambda : phrase([_be, _being_target(you)]),2)])()

def _present_question():
    sub_and_tag = _subject_and_tag(rand_plural())
    return phrase([_present_question_word(sub_and_tag[1]), sub_and_tag[0], _present_question_suffix(sub_and_tag[1]), _question])

def _transitive_question():
    sub_and_tag = _subject_and_tag(rand_plural())
    return phrase([_transitive_question_word(), rand_word(POS_COUNTABLE_NOUN, NOUN_SINGULAR), _simple_question_word(sub_and_tag[1]), sub_and_tag[0], rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _likely_prepositional_phrase(), _transitive_question_suffix(), _question])

def _possible_advice_sub_clause(tense):
    pre,con,post,tn = _conjunction(tense)
    assert pre == _nil
    return RandomChoice([(lambda : _nil,7),
                         (lambda : phrase([con, _indep_clause(tn)[0], post]),5),
                         (lambda : phrase([_coordinating_conjunction_advice(), _command()]),5)])()

def _being_question_suffix(pl,pron):
    return RandomChoice([(lambda : _nil,20),
                         (lambda : lit_phrase("or am I crazy"),1),
                         (lambda : lit_phrase("or am I dumb"),1),
                         (lambda : lit_phrase("or am I on crack"),1),
                         (lambda : lit_phrase("or am I on wrong"),1),
                         (lambda : phrase([lit_phrase("or am I "), _being_target(I)]),5),
                         (lambda : phrase([lit_phrase("or are you "), _being_target(you)]),5),
                         (lambda : phrase([_or, _being_target(pron)]),5),
                         (lambda : phrase([lit_phrase("or just"), _being_target(pron)]),5)])()

def _being_question_past_suffix(pl,pron):
    return RandomChoice([(lambda : _nil,40),
                         (lambda : lit_phrase("or am I crazy"),1),
                         (lambda : lit_phrase("or am I dumb"),1),
                         (lambda : lit_phrase("or am I on crack"),1),
                         (lambda : lit_phrase("or am I on wrong"),1),
                         (lambda : phrase([lit_phrase("or am I "), _being_target(I)]),10),
                         (lambda : phrase([lit_phrase("or are you "), _being_target(you)]),10),
                         (lambda : lit_phrase("yesterday"),1),
                         (lambda : lit_phrase("just yesterday"),1),
                         (lambda : lit_phrase("since yesterday"),1),
                         (lambda : lit_phrase("last weak"),1),
                         (lambda : lit_phrase("just last weak"),1),
                         (lambda : lit_phrase("last year"),1),
                         (lambda : lit_phrase("just last year"),1),
                         (lambda : lit_phrase("last Tuesday"),1),
                         (lambda : lit_phrase("since Sunday"),1),
                         (lambda : lit_phrase("just last Friday"),1),
                         (lambda : phrase([_or, _being_target(pron)]),10),
                         (lambda : phrase([lit_phrase("or just"), _being_target(pron)]),10),
                         (lambda : _being_question_smart_suffix(pl, pron),10)])()

def _being_question_smart_suffix(pl, pron):
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_or, _to_be_pos(subj_and_tag[1]), subj_and_tag[0], _being_target(subj_and_tag[1])])

def _being_question():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_fix_am_not(_to_be(subj_and_tag[1], None))[0], subj_and_tag[0], _being_target(subj_and_tag[1]), _being_question_suffix(plurality, subj_and_tag[1]), _question])

def _being_question_alt():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    target = _being_target(subj_and_tag[1])
    return phrase([_fix_am_not(_to_be_pos(subj_and_tag[1])), subj_and_tag[0], target, _or, _fix_am_not(_to_be_pos(subj_and_tag[1])), subj_and_tag[0], target, _question])

def _being_question_past():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_fix_am_not(_to_be_past(subj_and_tag[1]))[0], subj_and_tag[0], _being_target(subj_and_tag[1]), _being_question_past_suffix(plurality, subj_and_tag[1]), _question])

def _fix_am_not(p):
    return (lit_phrase("aren't") if p == lit_phrase("am not") else p)

def _present_question_word(pronoun):
    return RandomChoice([(lambda : lit_phrase("did"),1),
                         (lambda : lit_phrase("when did"),1),
                         (lambda : lit_phrase("where did"),1),
                         (lambda : lit_phrase("why did"),1),
                         (lambda : lit_phrase("how did"),1),
                         (lambda : lit_phrase("didn't"),1),
                         (lambda : lit_phrase("why didn't"),1),
                         (lambda : lit_phrase("why can't"),1),
                         (lambda : lit_phrase("can't"),1),
                         (lambda : lit_phrase("can"),1),
                         (lambda : lit_phrase("how can"),1),
                         (lambda : lit_phrase("where can"),1),
                         (lambda : lit_phrase("when can"),1),
                         (lambda : _do_verb(pronoun),2),
                         (lambda : phrase([lit_phrase("why"), _do_verb(pronoun)]),1),
                         (lambda : phrase([lit_phrase("where"), _do_verb_pos(pronoun)]),1),
                         (lambda : phrase([lit_phrase("how"), _do_verb_pos(pronoun)]),1),
                         (lambda : phrase([lit_phrase("when"), _do_verb_pos(pronoun)]),1)])()

def _simple_question_word(pronoun):
    return RandomChoice([(lambda : lit_phrase("did"),1),
                         (lambda : lit_phrase("didn't"),1),
                         (lambda : lit_phrase("can't"),1),
                         (lambda : lit_phrase("can"),1),
                         (lambda : _do_verb(pronoun),2)])()

def _transitive_question_word():
    return RandomChoice([(lambda : lit_phrase("which"),1),
                         (lambda : lit_phrase("whose"),1),
                         (lambda : lit_phrase("what"),1)])()

def _do_verb(pronoun):
    return RandomChoice([(lambda : _do_verb_pos(pronoun),4),
                         (lambda : _do_verb_(pronoun),1)])()

def _do_verb_pos(pronoun):
    if pronoun == I:
        return lit_phrase("do")
    if pronoun == you:
        return lit_phrase("do")
    if pronoun == he:
        return lit_phrase("does")
    if pronoun == she:
        return lit_phrase("does")
    if pronoun == it:
        return lit_phrase("does")
    if pronoun == they:
        return lit_phrase("do")
    if pronoun == we:
        return lit_phrase("do")
    if pronoun == sing:
        return lit_phrase("does")
    if pronoun == plural:
        return lit_phrase("do")

def _do_verb_(pronoun):
    if pronoun == I:
        return lit_phrase("don't")
    if pronoun == you:
        return lit_phrase("don't")
    if pronoun == he:
        return lit_phrase("doesn't")
    if pronoun == she:
        return lit_phrase("doesn't")
    if pronoun == it:
        return lit_phrase("doesn't")
    if pronoun == they:
        return lit_phrase("don't")
    if pronoun == we:
        return lit_phrase("don't")
    if pronoun == sing:
        return lit_phrase("doesn't")
    if pronoun == plural:
        return lit_phrase("don't")

def _present_question_suffix(pronoun):
    return RandomChoice([(lambda : phrase([rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), pronoun), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([_possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), pronoun)]),1)])()

def _subjunctive_clause_pl_random():
    return RandomChoice([(_subjunctive_clause_pl_intrans,5),
                         (_subjunctive_clause_pl_trans,8),
                         (_subjunctive_clause_pl_infin_intrans,5),
                         (_subjunctive_clause_pl_infin_trans,8),
                         (_being_clause_subjunctive,3)])

def _conditional_clause_pl_random():
    return RandomChoice([(_conditional_clause_pl_intrans,5),
                         (_conditional_clause_pl_trans,8),
                         (_conditional_clause_pl_infin_intrans,5),
                         (_conditional_clause_pl_infin_trans,8),
                         (_being_clause_conditional,3)])

def _subjunctive_clause_pl(plural_):
    return _subjunctive_clause_pl_random()(plural_)

def _conditional_clause_pl(plural_):
    return _conditional_clause_pl_random()(plural_)

def _conditional_helper():
    return phrase([_would_or_wouldnt(), _possible_conditional_filler()])

def _would_or_wouldnt():
    return RandomChoice([(_would,8),
                         (_wouldnt,2),
                         (lit_phrase("would never"),1),
                         (lit_phrase("would maybe"),2),
                         (lit_phrase("would perhaps"),1),
                         (lit_phrase("would always"),1),
                         (lit_phrase("would almost surely"),1),
                         (lit_phrase("would almost always"),1),
                         (lit_phrase("would at least sometimes"),1),
                         (lit_phrase("would at least occasionally"),1)])

def _possible_conditional_filler():
    return RandomChoice([(_nil,15),
                         (lit_phrase("be able to"),2),
                         (lit_phrase("have enough to"),1),
                         (lit_phrase("have what it takes to"),1),
                         (lit_phrase("want to"),2),
                         (lit_phrase("refuse to"),1),
                         (lit_phrase("need to"),2),
                         (lit_phrase("have to"),1),
                         (lit_phrase("get to"),1),
                         (lit_phrase("try to"),1),
                         (lit_phrase("think I could"),1),
                         (lit_phrase("think I should"),1)])

def _indep_clause_pl_intrans_3(plural_, tense):
    vb, res = _verb(plural_, tense)(POS_INTRANSITIVE_VERB)
    return phrase([_noun(plural_), vb, _possible_adverb(_nil, _nil), _possible_prepositional_phrase()]), res

def _subjunctive_clause_pl_intrans(plural_):
    return phrase([_subject(plural_), _were, rand_word(POS_INTRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_infin_intrans(plural_):
    return phrase([_subject(plural_), _were, _to, rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _conditional_clause_pl_intrans(plural_):
    return phrase([_subject(plural_), _conditional_helper(), _be, rand_word(POS_INTRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART),  _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _conditional_clause_pl_infin_intrans(plural_):
    return phrase([_subject(plural_), _conditional_helper(), rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_ego_3(plural_, tense):
    vb, res = _verb_ego(plural_, tense)(POS_INTRANSITIVE_VERB)
    return phrase([(_I if plural_ else _we), vb, _possible_adverb(_nil, _nil), _possible_prepositional_phrase()]) , res

def _indep_clause_pl_trans_3(plural_, tense):
    vb, res = _verb(plural_, tense)(POS_TRANSITIVE_VERB)
    return phrase([_noun(plural_),vb, _object(rand_plural(), False), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()]), res

def _subjunctive_clause_pl_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _were, rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _object(rand_plural(), subj_and_tag[1]),  _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_infin_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _were, _to, rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), subj_and_tag[1]), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _conditional_clause_pl_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _conditional_helper(), _be, rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _object(rand_plural(), subj_and_tag[1]), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _conditional_clause_pl_infin_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _conditional_helper(), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), subj_and_tag[1]),  _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_ego_3(plural_, tense):
    vb, res = _verb_ego(plural_, tense)(POS_TRANSITIVE_VERB)
    return phrase([(_I if plural_ else _we), vb, _object(rand_plural(), (I if plural_ else we)), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()]), res

def _being_clause(plurality, tense):
    subj_and_tag = _subject_and_tag(plurality)
    tobe, t = _to_be(subj_and_tag[1], tense)
    return phrase([subj_and_tag[0], tobe, _being_target(subj_and_tag[1])]), t

def _being_clause_subjunctive(plurality):
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([subj_and_tag[0], _were, _being_target(subj_and_tag[1])])

def _being_clause_conditional(plurality):
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([subj_and_tag[0], _conditional_helper(), _be, _being_target(subj_and_tag[1])])

def _to_be(tag, tense):
    if not tense is None and _is_past_cont([tense]):
        return _to_be_past(tag)
    if not tense is None and _is_futr_cont([tense]):
        return RandomChoice([((phrase([_will,_be]),"futr_cont_pos"),4),
                             ((phrase[_wont,_be],"futr_cont_neg"),1)])
    return RandomChoice([(lambda : (_to_be_pos(tag),"pres_cont_pos"),3),
                         (lambda : (_to_be_neg(tag), "pres_cont_neg"),1)])()

def _to_be_pos(tag):
    if tag == I:
        return _am
    if tag == sing:
        return _is
    if tag == he:
        return _is
    if tag == she:
        return _is
    if tag == it:
        return _is
    if tag == plural:
        return _are
    if tag == you:
        return _are
    if tag == they:
        return _are
    if tag == we:
        return _are

def _to_be_neg(tag):
    if tag == I:
        return lit_phrase("am not")
    if tag == sing:
        return _isnt
    if tag == he:
        return _isnt
    if tag == she:
        return _isnt
    if tag == it:
        return _isnt
    if tag == plural:
        return _arent
    if tag == you:
        return _arent
    if tag == they:
        return _arent
    if tag == we:
        return _arent

def _to_be_past(tag):
    return RandomChoice([(lambda : (_to_be_past_pos(tag),"past_cont_pos"),3),
                         (lambda : (_to_be_past_neg(tag),"past_cont_neg"),1)])()

def _to_be_past_pos(tag):
    if tag == I:
        return _was
    if tag == sing:
        return _was
    if tag == he:
        return _was
    if tag == she:
        return _was
    if tag == it:
        return _was
    if tag == plural:
        return _were
    if tag == you:
        return _were
    if tag == they:
        return _were
    if tag == we:
        return _were

def _to_be_past_neg(tag):
    if tag == I:
        return _wasnt
    if tag == sing:
        return _wasnt
    if tag == he:
        return _wasnt
    if tag == she:
        return _wasnt
    if tag == it:
        return _wasnt
    if tag == plural:
        return _wasnt
    if tag == you:
        return _werent
    if tag == they:
        return _werent
    if tag == we:
        return _werent

def _me_object(pronoun, plurality):
    if pronoun == I:
        return lit_phrase("myself")
    if pronoun == we:
        return lit_phrase("ourselves")
    else:
        return (lit_phrase("me") if plurality else lit_phrase("us"))

def _you_object(pronoun, plurality):
    if pronoun == you:
        return lit_phrase("yourself")
    else:
        return lit_phrase("you") if plurality else _being_target(pronoun)

def _pronoun_plurality(pronoun):
    return pronoun in [I,he,she,it,you,me,sing]

def _being_target(pronoun):
    plurality = _pronoun_plurality(pronoun)
    return RandomChoice([(lambda : _me_object(pronoun, plurality),1),
                         (lambda : _you_object(pronoun, plurality),1),
                         (lambda : phrase([_article(plurality), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, plurality)]),2),
                         (lambda : phrase([_like, _article(plurality), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, plurality)]),2),
                         (lambda : _prepositional_phrase(),3),
                         (lambda : _adj(),3),
                         (lambda : phrase([_adj_comparative(), _than, _object(plurality, pronoun)]),3),
                         (lambda : phrase([_adj_comparative_1(), _than, _object(plurality, pronoun), _and, _adj_comparative_1(), _than, _object(plurality, pronoun)]),3),
                         (lambda : phrase([_the, _adj_superlative(plurality)]),3)])()

def _noun(plural):
    return (_noun_sing() if plural else _noun_pl())

def _verb(plural, tense):
    return (_verb_sing_func(tense) if plural else _verb_pl_func(tense))

def _adapted_verb(plural, tense):
    return (_adapted_verb_sing_func(tense) if plural else _adapted_verb_pl_func(tense))

def _possible_prefix():
    return RandomChoice([(_nil,30),
                         (lit_phrase("I think"),2),
                         (lit_phrase("I'm bothered that"),2),
                         (lit_phrase("I believe that"),2),
                         (lit_phrase("I don't think"),2),
                         (phrase([lit_phrase("imo"), _comma]),1),
                         (phrase([lit_phrase("hey"), _comma]),1),
                         (phrase([lit_phrase("yo"), _comma]),1),
                         (phrase([lit_phrase("imho"), _comma]),1),
                         (lit_phrase("I heard"),2),
                         (lit_phrase("they say"),2),
                         (lit_phrase("no offense but"),2),
                         (phrase([lit_phrase("honestly"), _comma]),2),
                         (phrase([lit_phrase("you know what"), _comma]),2),
                         (phrase([lit_phrase("however"), _comma]),2),
                         (lit_phrase("but"),2),
                         (lit_phrase("I hate that"),2),
                         (lit_phrase("I love that"),2),
                         (phrase([lit_phrase("eww"), _comma]),1)])

def _second_conditional_prefix():
    return RandomChoice([(lit_phrase("if"),5),
                         (lit_phrase("if only"),1)])

def _transitive_question_suffix():
    return RandomChoice([(_nil,8),
                         (lit_phrase("and why"),1),
                         (lit_phrase("and what for"),1),
                         (lit_phrase("and for what"),1),
                         (phrase([_comma, lit_phrase("seriously")]),1),
                         (phrase([_comma, lit_phrase("really")]),1)])

def _subjunctive_prefix():
    return RandomChoice([(lit_phrase("but what if"),2),
                         (lit_phrase("imagine if"),2),
                         (lit_phrase("but imagine if"),2),
                         (lit_phrase("what would happen if"),2)])

def _possible_suffix():
    return RandomChoice([(_nil,25),
                         (phrase([_comma, lit_phrase("you know")]),1),
                         (phrase([_comma, lit_phrase("but I don't know why")]),1),
                         (phrase([_comma, lit_phrase("at least I think")]),1),
                         (phrase([_comma, lit_phrase("and I'm excited about it")]),1),
                         (phrase([_comma, lit_phrase("and I'm stoked")]),1),
                         (phrase([_comma, lit_phrase("and I don't care")]),1),
                         (phrase([_comma, lit_phrase("but don't take my word for it")]),1),
                         (phrase([_dotdotdot, lit_phrase("nevermind")]),1)])

def _question_adapted_prefix():
    return RandomChoice([(lit_phrase("do you think"),1),
                         (lit_phrase("do you believe"),1),
                         (lit_phrase("did you know"),1),
                         (lit_phrase("did you hear"),1),
                         (lit_phrase("are you saying that"),1),
                         (lit_phrase("why do you think"),1),
                         (lit_phrase("do you know if"),1),
                         (lit_phrase("don't you hate that"),1),
                         (lit_phrase("don't you love that"),1),
                         (lit_phrase("what if"),1)])

def _advice_prefix(positive):
    return _advice_prefix_pos() if positive else _advice_prefix_neg()

def _advice_prefix_pos():
    return RandomChoice([(lit_phrase("I think you should"),1),
                         (lit_phrase("you should"),1),
                         (lit_phrase("you ought to"),1),
                         (lit_phrase("you shouldn't"),1),
                         (lit_phrase("perhaps you should"),1),
                         (lit_phrase("perhaps you ought to"),1),
                         (lit_phrase("please"),2),
                         (lit_phrase("you need to"),1),
                         (lit_phrase("you gotta"),1),
                         (lit_phrase("perhaps you need to"),1),
                         (lit_phrase("perhaps you gotta"),1),
                         (lit_phrase("I have to ask you to"),1)])
def _advice_prefix_neg():
    return RandomChoice([(lit_phrase("you ought not"),1),
                         (lit_phrase("you shouldn't"),1),
                         (lit_phrase("perhaps you shouldn't"),1),
                         (lit_phrase("please don't"),1),
                         (lit_phrase("you don't have to"),1),
                         (lit_phrase("I have to ask you to not to"),1)])

                         
def _sentence():
    return RandomChoice([(lambda : phrase([_sentence_random(), _end_punc_random()]),8),
                         (lambda : phrase([_second_conditional_prefix(), _subjunctive_clause(), _comma, _conditional_clause(), _end_punc_random()]),1),
                         (lambda : phrase([_conditional_clause(), _second_conditional_prefix(), _subjunctive_clause(), _end_punc_random()]),1),
                         (lambda : phrase([_subjunctive_prefix(), _subjunctive_clause(), _question]),2),
                         (_advice,3),
                         (_question_sentence,4)])()


def _end_punc_random():
    return RandomChoice([(_exclamation,1),
                         (_period,7)])

def _sentence_random():
    return RandomChoice([(lambda : [_possible_prefix(),_sentence_single(None)[0]],3),
                         (lambda : [_sentence_single(None)[0],_possible_suffix()],2),
                         (_sentence_compound,2)])()

def _sentence_single(tense):
    ic,res = _indep_clause(tense)
    return phrase([_possible_sub_clause(_comma, _comma), ic, _possible_sub_clause(_comma, _nil), _comma]), res

def _sentence_compound():
    fst, tn = _indep_clause(None)
    pre, conj, post, tn2 = _conjunction(tn)
    if tn2 is None:
        tn2 = RandomChoice([(None,3),([tn],1)])
    snd, tn3 = _indep_clause(tn2)
    return phrase([pre, fst, conj, snd, post])

# the dog eats                    the dog ate              the dog will eat
# the dog is eating               the was eating           the dog will be eating
# the dog has eaten               the dog had eaten        the dog will have eaten
# the dog has been eating         the dog had been eating  the dog will have been eating
def _conjunction(t):
    ts = _strip_polarity(t)
    return RandomFilteredChoice([
        (True,(_nil,[_comma,"and"],_nil,None),6),
        (ts != "command",("either",[_comma,"or"],_nil,None),4),        
        (ts == "futr" or ts == "command" or not _is_futr_any([t]),(_nil,[_comma,"but"],_nil,None),3),
        (not _is_futr([t]),(_nil,[_comma, "yet"],_nil,_no_earlier(t)),1),
        (ts != "past_perf" and _is_past([t]),(_nil,[_comma,"then"],_nil,["past_pos","past_neg"]),1),
        (not _is_perf([t]),(_nil,[_comma,"so"],_nil, _futr_tenses + _cont_tenses+_perf_cont_tenses),2),
        (True,(_nil,[_period,
                     random.choice(["Also","Besides","Incidently","Indeed","Instead","Likewise",
                                    "Meanwhile","Moreover","Similarly"]),
                     _comma],_nil, None),4),
        (True,(_nil,[_period,
                     random.choice(["Anyways","However","Nevertheless","Accordingly",
                                    "Still","Therefore","Thus","Consequently","Furthermore"]),
                     _comma],_nil, _futr_tenses + _cont_tenses+_perf_cont_tenses),6),
        (True,(_nil,[_period,
                     random.choice(["Then","Thus"])],_nil, _futr_tenses + _cont_tenses+_perf_cont_tenses),1),
        (True,(_nil,[_period,
                     random.choice(["Now"])],_nil, _polarize(["pres_cont","pres","futr","futr_cont"])),2),
        (True,(_nil,[_period,
                     random.choice(["Otherwise"])],_nil, _futr_tenses),1),
        (True,(_nil,[_comma,_and,random.choice(["certainly"])],_nil,None),1),
        (True,(_nil,[_comma,_and,
                     random.choice(["consequently","finally","furthermore","hence","thus","therefore","still"])
                     ],_nil,_futr_tenses),3),
        (True,(_nil,[_comma, random.choice(["else"])],_nil,_futr_tenses),1),
        
        (ts == "command" or _is_base([t]) or _is_cont([t]),
         (_nil,random.choice(["until","after",[_comma,"as","if"],
                              [_comma,"as","though"],[_comma,"even","if"],[_comma,"even","though"],
                              "when","whenever","wherever","while","because","provided","before"]),_nil,
          _polarize([_get_time(t) if not _is_futr_any([t]) else "pres"])),4),
        
        (ts == "command" or _is_base([t]) or _is_cont([t]),
         (_nil,random.choice(["because","wherever",[_comma,"as","if"],[_comma,"as","if"],
                              [_comma,"even","if"],[_comma,"even","though"],[_comma,"provided"]]),_nil,
          _polarize(["past_cont","past"])),4),
        
        (not _is_past_any([t]) and (ts == "command" or _is_base([t]) or _is_cont([t])),
         (_nil,random.choice([["now","that"],"if","unless",
                              [_comma,"so","that"],[_comma,"as","long","as"],[_comma,"as","soon","as"]]),_nil,
          _polarize(["pres_cont","pres"])),4),
        (ts in ["command","futr","futr_cont","pres_cont"],
         (_nil,[_comma,_negatory_conjunction()],_nil,"being_cond"),6)
        
        ])

def _advice():
    positive = RandomChoice([("command_pos",3), ("command_neg",1)])
    return phrase([_advice_prefix(positive), _command(), _possible_advice_sub_clause(positive), _end_punc_random()])

def _question_sentence():
    return RandomChoice([(_present_question(),2),
                         (_transitive_question(),1),
                         (_being_question(),1),
                         (_being_question_past(),1),
                         (_being_question_alt(),1)])

def _prepositional_phrase():
    prep, punc = _preposition_sing()
    return phrase([prep, _noun_phrase_no_clause(rand_plural()), punc])

def _possible_prepositional_phrase():
    return RandomChoice([(lambda: phrase([_prepositional_phrase(),_comma]),1),
                         (_nil_func0,6)])()

def _likely_prepositional_phrase():
    return RandomChoice([(_prepositional_phrase,1),
                         (_nil_func0,1)])()

def _preposition_sing():
    return RandomChoice([((lit_phrase("across from"),_nil),1),
                         ((lit_phrase("around"),_nil),1),
                         ((lit_phrase("beyond"),_nil),1),
                         ((lit_phrase("by"),_nil),1),
                         ((lit_phrase("for"),_nil),2),
                         ((lit_phrase("like"),_nil),4),
                         ((lit_phrase("near"),_nil),1),
                         ((lit_phrase("with"),_nil),2),
                         ((lit_phrase("without"),_nil),2)])

def _article(plurality):
    return (_article_sing() if plurality else _article_pl())

def _article_pl():
    return RandomChoice([(_the,10),
                         (_some,4),
                         (_those,16),
                         (_two,1),
                         (_three,1),
                         (_four,1),
                         (_five,1),
                         (_six,1),
                         (lit_phrase("my"),8),
                         (lit_phrase("your"),8),
                         (lit_phrase("his"),3),
                         (lit_phrase("her"),3),
                         (lit_phrase("their"),4)])

def _article_sing():
    return RandomChoice([(_the,4),
                         (_a,3),
                         (_that,6),
                         (_some,1),
                         (lit_phrase("this"),3),
                         (lit_phrase("my"),7),
                         (lit_phrase("your"),7),
                         (lit_phrase("his"),2),
                         (lit_phrase("her"),2),
                         (lit_phrase("their"),4)])
def _possessive_pronoun():
    return RandomChoice([(_the,4),
                         (lit_phrase("my"),6),
                         (lit_phrase("your"),3),
                         (lit_phrase("his"),2),
                         (lit_phrase("her"),2),
                         (lit_phrase("their"),4)])


def _coordinating_conjunction_advice():
    return RandomChoice([(cm_lit_phrase("and"),1),
                         (cm_lit_phrase("and try to"),1),
                         (cm_lit_phrase("and you will"),1),
                         (cm_lit_phrase("and don't"),1),
                         (cm_lit_phrase("or"),1),
                         (cm_lit_phrase("or you won't be able to"),1),
                         (cm_lit_phrase("but"),1),
                         (cm_lit_phrase("but don't"),1),
                         (cm_lit_phrase("but try to"),1),
                         (lit_phrase("so you can"),1)])

def _subordinating_conjunction():
    return RandomChoice([(lit_phrase("after"),1),
                         (lit_phrase("till"),1),
                         (lit_phrase("if"),1),
                         (cm_lit_phrase("unless"),1),
                         (cm_lit_phrase("inasmuch as"),1),
                         (lit_phrase("until"),1),
                         (lit_phrase("as if"),1),
                         (lit_phrase("in order that"),1),
                         (lit_phrase("when"),1),
                         (lit_phrase("as long as"),1),
                         (cm_lit_phrase("lest"),1),
                         (lit_phrase("whenever"),1),
                         (lit_phrase("now that"),1),
                         (lit_phrase("as soon as"),1),
                         (cm_lit_phrase("provided"),1),
                         (lit_phrase("wherever"),1),
                         (lit_phrase("as though"),1),
                         (lit_phrase("since"),1),
                         (lit_phrase("while"),1),
                         (lit_phrase("because"),1),
                         (lit_phrase("so that"),1),
                         (lit_phrase("before"),1),
                         (lit_phrase("even if"),1),
                         (lit_phrase("even though"),1)])

def _negatory_conjunction():
    return RandomChoice([(lit_phrase("lest"),1),
                         (lit_phrase("provided"),1),
                         (lit_phrase("even if"),1),
                         (lit_phrase("even though"),1),
                         (lit_phrase("or else"),1)])

def _possible_adj():
    return RandomChoice([(_nil_func0,50),
                         (_adj_1,8),
                         (_adj_2,1),
                         (_adj_2_and,1)])()

def _adj():
    return RandomChoice([(_adj_1,8),
                         (_adj_2_and,3)])()

def _adj_1():
    return rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)

def _adj_2():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _comma, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)])

def _adj_2_and():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _and, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)])

def _adj_comparative_1():
    return rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_COMPARE)

def _adj_comparative_2():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_COMPARE), _and, rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_COMPARE)])

def _adj_comparative():
    return RandomChoice([(_adj_comparative_1,6),
                         (_adj_comparative_2,1)])()

def _adj_superlative(plural):
    return RandomChoice([(lambda : phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE)]),8),
                         (lambda : phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), _superlative_modify()]),1),
                         (lambda : phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), rand_word(POS_COUNTABLE_NOUN, plural), _superlative_modify()]),1),
                         (lambda : phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE)]),2)])()

def _superlative_modify():
    return RandomChoice([(lit_phrase("ever"),1),
                         (lit_phrase("anywhere"),1),
                         (lit_phrase("yet"),1),
                         (lit_phrase("I've seen"),1),
                         (lit_phrase("I've know"),1),
                         (lit_phrase("I've heard of"),1)])

def _noun_pl():
    return RandomChoice([(lambda : _noun_phrase(NOUN_PLURAL),5),
                         (lambda : phrase([_noun_phrase_no_clause(NOUN_SINGULAR), _and, _noun_phrase(NOUN_SINGULAR)]),1)])()

def _noun_sing():
    return _noun_phrase(NOUN_SINGULAR)

def _noun_phrase_no_clause(plurality):
    return (_noun_phrase_no_clause_sing() if plurality else _noun_phrase_no_clause_pl())

def _noun_phrase_no_clause_pl():
    return RandomChoice([(lambda : phrase([_article(False), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, False)]),4),
                         (lambda : phrase([_possessive_pronoun(), rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), rand_word(POS_COUNTABLE_NOUN, False)]),1),
                         (lambda : phrase([_article(False),  _possible_adj(), 
                                           rand_word(POS_COUNTABLE_NOUN, True), _hyphen, rand_word(POS_VERBER, False)]), 1)
                         ])()

def _noun_phrase_no_clause_sing():
    return RandomChoice([(lambda : phrase([_article(True), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),4),
                         (lambda : phrase([_possessive_pronoun(), rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), rand_word(POS_COUNTABLE_NOUN, True)]),1),
                         (lambda : rand_word(POS_PROPER_NOUN, PROPER_NOUN_FORENAME),1),
                         (lambda : phrase([_article(True),  _possible_adj(), 
                                           rand_word(POS_COUNTABLE_NOUN, True) , _hyphen, rand_word(POS_VERBER, True)]), 1)
                         ])()

def _noun_phrase(plurality):
    return _noun_phrase_no_clause(plurality)

def _object_sing(is_I):
    return RandomChoice([(lambda : _noun(True),60),
                         (lambda : (lit_phrase("myself") if is_I == I else (_object_sing(we) if is_I == we else lit_phrase("me"))),5),
                         (lambda : (lit_phrase("himself") if is_I == he else lit_phrase("him")),1),
                         (lambda : (lit_phrase("herself") if is_I == she else lit_phrase("her")),1),
                         (lambda : (lit_phrase("itself") if is_I == it else lit_phrase("it")),1),
                         (lambda : (lit_phrase("yourself") if is_I == you else lit_phrase("you")),5)])()

def _object_pl(is_we):
    return RandomChoice([(lambda : _noun_phrase(False),40),
                         (lambda : (lit_phrase("ourselves") if is_we == we else lit_phrase("us")),3),
                         (lambda : (lit_phrase("themselves") if is_we == them else lit_phrase("them")),2)
                         ])()

def _object(plurality, is_ego):
    return (_object_sing(is_ego) if plurality else _object_pl(is_ego))

def _subject_and_tag(plurality):
    return (_subj_and_tag_sing() if plurality else _subj_and_tag_pl())

def _subj_and_tag_sing():
    return RandomChoice([(lambda : (_noun(True), sing),10),
                         (lambda : (lit_phrase("I"), I),5),
                         (lambda : (lit_phrase("he"), he),1),
                         (lambda : (lit_phrase("she"), she),1),
                         (lambda : (lit_phrase("it"), it),2),
                         (lambda : (lit_phrase("you"), you),10)])()

def _subj_and_tag_pl():
    return RandomChoice([(lambda : (_noun(False), plural),10),
                         (lambda : (lit_phrase("we"), we),5),
                         (lambda : (lit_phrase("they"), they),3)])()

def _subject(plurality):
    return _subject_and_tag(plurality)[0]

def _print_and_fail(x):
    print "printing and failing %s" % x
    assert False

def _verb_pl_func(tense):
    return RandomFilteredChoice([(_is_pres(tense),_verb_simple_present_pl,4),
                                 (_is_past(tense),_verb_simple_past,4),
                                 (_is_futr(tense),_verb_simple_future(tense),3),
                                 (_is_pres_cont(tense),_verb_present_continuous_pl,3),
                                 (_is_past_cont(tense),_verb_past_continuous_pl,3),
                                 (_is_futr_cont(tense),_verb_future_continuous(tense),3),
                                 (_is_pres_perf(tense),_verb_present_perfect_pl,2),
                                 (_is_past_perf(tense),_verb_past_perfect,2),
                                 (_is_futr_perf(tense),_verb_future_perfect(tense),2),
                                 (_is_pres_perf_cont(tense),_verb_present_perfect_continuous_pl,1),
                                 (_is_past_perf_cont(tense),_verb_past_perfect_continuous,1),
                                 (_is_futr_perf_cont(tense),_verb_future_perfect_continuous(tense),1)])

def _verb_sing_func(tense):
    return RandomFilteredChoice([(_is_pres(tense),_verb_simple_present_sing,4),
                                 (_is_past(tense),_verb_simple_past,4),
                                 (_is_futr(tense),_verb_simple_future(tense),3),
                                 (_is_pres_cont(tense),_verb_present_continuous_sing,3),
                                 (_is_past_cont(tense),_verb_past_continuous_sing,3),
                                 (_is_futr_cont(tense),_verb_future_continuous(tense),3),
                                 (_is_pres_perf(tense),_verb_present_perfect_sing,2),
                                 (_is_past_perf(tense),_verb_past_perfect,2),
                                 (_is_futr_perf(tense),_verb_future_perfect(tense),2),
                                 (_is_pres_perf_cont(tense),_verb_present_perfect_continuous_sing,1),
                                 (_is_past_perf_cont(tense),_verb_past_perfect_continuous,1),
                                 (_is_futr_perf_cont(tense),_verb_future_perfect_continuous(tense),1)])

def _verb_ego_func(tense):
    return RandomFilteredChoice([(_is_pres(tense),_verb_simple_present_ego,4),
                                 (_is_past(tense),_verb_simple_past,4),
                                 (_is_futr(tense),_verb_simple_future(tense),3),
                                 (_is_pres_cont(tense),_verb_present_continuous_ego,3),
                                 (_is_past_cont(tense),_verb_past_continuous_sing,3),
                                 (_is_futr_cont(tense),_verb_future_continuous(tense),3),
                                 (_is_pres_perf(tense),_verb_present_perfect_ego,2),
                                 (_is_past_perf(tense),_verb_past_perfect,2),
                                 (_is_futr_perf(tense),_verb_future_perfect(tense),2),
                                 (_is_pres_perf_cont(tense),_verb_present_perfect_continuous_ego,1),
                                 (_is_past_perf_cont(tense),_verb_past_perfect_continuous,1),
                                 (_is_futr_perf_cont(tense),_verb_future_perfect_continuous(tense),1)])

def _verb_we_func(tense):
    return RandomFilteredChoice([(_is_pres(tense),_verb_simple_present_ego,4),
                                 (_is_past(tense),_verb_simple_past,4),
                                 (_is_futr(tense),_verb_simple_future(tense),3),
                                 (_is_pres_cont(tense),_verb_present_continuous_pl,3),
                                 (_is_past_cont(tense),_verb_past_continuous_pl,3),
                                 (_is_futr_cont(tense),_verb_future_continuous(tense),3),
                                 (_is_pres_perf(tense),_verb_present_perfect_ego,2),
                                 (_is_past_perf(tense),_verb_past_perfect,2),
                                 (_is_futr_perf(tense),_verb_future_perfect(tense),2),
                                 (_is_pres_perf_cont(tense),_verb_present_perfect_continuous_ego,1),
                                 (_is_past_perf_cont(tense),_verb_past_perfect_continuous,1),
                                 (_is_futr_perf_cont(tense),_verb_future_perfect_continuous(tense),1)])

def _adapted_verb_sing_func(tense, fallback = _verb_sing_func):
    return RandomFilteredChoice([(_is_pres(tense),_adapted_verb_simple_present_sing,4),
                                 (_is_past(tense),_adapted_verb_simple_past,4),
                                 (_is_pres_cont(tense),_adapted_verb_present_continuous_sing,3),
                                 (_is_past_cont(tense),_adapted_verb_past_continuous_sing,3),
                                 (True, fallback(tense), 1)])

def _adapted_verb_pl_func(tense, fallback = _verb_pl_func):
    return RandomFilteredChoice([(_is_pres(tense),_adapted_verb_simple_present_pl,4),
                                 (_is_past(tense),_adapted_verb_simple_past,4),
                                 (_is_pres_cont(tense),_adapted_verb_present_continuous_pl,3),
                                 (_is_past_cont(tense),_adapted_verb_past_continuous_pl,3),
                                 (True, fallback(tense), 1)])

def _adapted_verb_ego_func(tense):
    return _adapted_verb_pl_func(tense, _verb_ego_func)
def _adapted_verb_we_func(tense):
    return _adapted_verb_pl_func(tense, _verb_we_func)

def _cross(l1, l2):
    assert len(l1) > 0, l2
    assert len(l2) > 0, l1
    return [a + ("_" if b != "" else "") + b for a in l1 for b in l2]

def _polarize(s):
    assert s != [] and s != [""]
    return _cross(s,["pos","neg"])

_sub_tenses = ["","perf","cont","perf_cont"]
_past_tenses = _cross(["past_" + t for t in _sub_tenses],["pos","neg"])
_pres_tenses = _cross(["pres_" + t for t in _sub_tenses],["pos","neg"])
_futr_tenses = _cross(["futr_" + t for t in _sub_tenses],["pos","neg"])

_temp_tenses = ["past","pres","futr"]
_cont_tenses = _cross([t + "_cont" for t in _temp_tenses],["pos","neg"])
_perf_cont_tenses = _cross([t + "_perf_cont" for t in _temp_tenses],["pos","neg"])
_all_tenses = _polarize(_cross(_temp_tenses,_sub_tenses))
_imperfect_tenses = _polarize(_cross(_temp_tenses,["","cont"]))

def _no_earlier(t):
    if _is_futr_any([t]):
        return _past_tenses + _pres_tenses + _futr_tenses
    if _is_pres_any([t]):
        return _past_tenses + _pres_tenses
    if _is_past_any([t]):
        return _past_tenses

def _no_later(t):
    if _is_futr_any([t]):
        return _futr_tenses
    if _is_pres_any([t]):
        return _pres_tenses + _futr_tenses
    if _is_past_any([t]):
        return _past_tenses + _pres_tenses + _futr_tenses

def _strip_polarity(t):
    return t[:-4]


def _get_time(t):
    if t == "command_pos" or t == "command_neg":
        return "pres"
    res = t[0:4]
    assert res in ["past","pres","futr"]
    return res

def _is_pos(t):
    if t is None:
        return True
    return "pos" in [s[-3:] for s in t]
def _is_neg(t):
    if t is None:
        return True
    return "neg" in [s[-3:] for s in t]

def _is_base(tense):
    return _is_pres(tense) or _is_past(tense) or _is_futr(tense)
def _is_perf(tense):
    return _is_pres_perf(tense) or _is_past_perf(tense) or _is_futr_perf(tense)
def _is_perf_cont(tense):
    return _is_pres_perf_cont(tense) or _is_past_perf_cont(tense) or _is_futr_perf_cont(tense)
def _is_cont(tense):
    return _is_pres_cont(tense) or _is_past_cont(tense) or _is_futr_cont(tense)
def _is_pres(tense):
    return tense is None or "pres_pos" in tense or "pres_neg" in tense
def _is_past(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "past_pos" in tense or "past_neg" in tense
def _is_futr(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "futr_pos" in tense or "futr_neg" in tense
def _is_pres_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "pres_cont_pos" in tense or "pres_cont_neg" in tense
def _is_past_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "past_cont_pos" in tense or "past_cont_neg" in tense
def _is_futr_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "futr_cont_pos" in tense or "futr_cont_neg" in tense
def _is_pres_perf(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "pres_perf_pos" in tense or "pres_perf_neg" in tense
def _is_past_perf(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "past_perf_pos" in tense or "past_perf_neg" in tense
def _is_futr_perf(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "futr_perf_pos" in tense or "futr_perf_neg" in tense
def _is_pres_perf_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "pres_perf_cont_pos" in tense or "pres_perf_cont_neg" in tense
def _is_past_perf_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "past_perf_cont_pos" in tense or "past_perf_cont_neg" in tense
def _is_futr_perf_cont(tense):
    assert isinstance(tense,list) or tense is None, tense
    return tense is None or "futr_perf_cont_pos" in tense or "futr_perf_cont_neg" in tense
def _is_futr_any(tense):
    return _is_futr(tense) or _is_futr_cont(tense) or _is_futr_perf(tense) or _is_futr_perf_cont(tense)
def _is_past_any(tense):
    return _is_past(tense) or _is_past_cont(tense) or _is_past_perf(tense) or _is_past_perf_cont(tense)
def _is_pres_any(tense):
    return _is_pres(tense) or _is_pres_cont(tense) or _is_pres_perf(tense) or _is_pres_perf_cont(tense)

def is_helper(x):
    return phrase([x]) in [_not, _would, _will, _should, _may, _might, _could, _must, _is, _are, _am, _was, _were, _be, _has, _have, _had, _been]

def _verb_ego(plural, tense):
    return (_verb_ego_func(tense) if plural else _verb_we_func(tense))

def _adapted_verb_ego(plural, tense):
    return _adapted_verb_ego_func(tense) if plural else _adapted_verb_we_func(tense)

def _random_inflect(t):
    return RandomFilteredChoice([(_is_neg(t),lambda : (phrase([_random_modal(), _not]),"_neg"),2),
                                 (_is_pos(t),lambda : (_random_modal(),"_pos"),5)])()

def _random_modal():
    return RandomChoice([(_will,5),
                         (_would,3),
                         (_should,2),
                         (_may,1),
                         (_might,2),
                         (_could,2),
                         (_must,2)])
        

def _verb_simple_present_sing(trans):
    return rand_word(trans, VERB_CONJUGATED, CONJ_3RD_SING), "pres_pos"

def _adapted_verb_simple_present_sing(trans):
    return phrase([rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_3RD_SING), _to, rand_word(trans, VERB_INFINITIVE)]), "pres_pos"

def _verb_simple_present_pl(trans):
    return rand_word(trans, VERB_INFINITIVE), "pres_pos"

def _adapted_verb_simple_present_pl(trans):
    return phrase([rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _to, rand_word(trans, VERB_INFINITIVE)]), "pres_pos"

def _verb_simple_present_ego(trans):
    return rand_word(trans, VERB_INFINITIVE), "pres_pos"

def _verb_simple_past(trans):
    return rand_word(trans, VERB_CONJUGATED, CONJ_PAST), "past_pos"

def _adapted_verb_simple_past(trans):
    return phrase([rand_word(trans, VERB_CONJUGATED, CONJ_PAST), _to, rand_word(trans, VERB_INFINITIVE)]), "past_pos"

def _verb_simple_future(t):
    inf, mod = _random_inflect(t)
    return lambda trans: (phrase([inf, rand_word(trans, VERB_INFINITIVE)]), "futr" + mod)

def _verb_present_continuous_sing(trans):
    return phrase([_is, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_cont_pos"

def _verb_present_continuous_pl(trans):
    return phrase([_are, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_cont_pos"

def _verb_present_continuous_ego(trans):
    return phrase([_am, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_cont_pos"

def _adapted_verb_present_continuous_sing(trans):
    return phrase([rand_word(trans, VERB_CONJUGATED, CONJ_3RD_SING), rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_cont_pos"

def _adapted_verb_present_continuous_pl(trans):
    return phrase([rand_word(trans, VERB_INFINITIVE), rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_cont_pos"

def _verb_past_continuous_sing(trans):
    return phrase([_was, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "past_cont_pos"

def _verb_past_continuous_pl(trans):
    return phrase([_were, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "past_cont_pos"

def _adapted_verb_past_continuous_sing(trans):
    return phrase([rand_word(trans, VERB_CONJUGATED, CONJ_PAST), rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "past_cont_pos"

def _adapted_verb_past_continuous_pl(trans):
    return phrase([rand_word(trans, VERB_CONJUGATED, CONJ_PAST), rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "past_cont_pos"

def _verb_future_continuous(t):
    inf, mod = _random_inflect(t)
    return lambda trans: (phrase([inf, _be, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "futr_cont" + mod)

def _verb_present_perfect_sing(trans):
    return phrase([_has, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)]), "pres_perf_pos"

def _verb_present_perfect_pl(trans):
    return phrase([_have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)]), "pres_perf_pos"

def _verb_present_perfect_ego(trans):
    return phrase([_have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)]), "pres_perf_pos"

def _verb_past_perfect(trans):
    return phrase([_had, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)]), "past_perf_pos"

def _verb_future_perfect(t):
    inf, mod = _random_inflect(t)
    return lambda trans: (phrase([inf, _have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)]), "futr_perf" + mod)

def _verb_present_perfect_continuous_sing(trans):
    return phrase([_has, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_perf_cont_pos"

def _verb_present_perfect_continuous_pl(trans):
    return phrase([_have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_perf_cont_pos"

def _verb_present_perfect_continuous_ego(trans):
    return phrase([_have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "pres_perf_cont_pos"

def _verb_past_perfect_continuous(trans):
    return phrase([_had, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "past_perf_cont_pos"

def _verb_future_perfect_continuous(t):
    inf, mod = _random_inflect(t)
    return lambda trans: (phrase([inf, _have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)]), "futr_perf_cont" + mod)

def _insult_body():
    return RandomChoice([(lambda : phrase([_you_are(), _being_target(you)]),4),
                         (lambda : phrase([lit_phrase("you"), rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _comma, _and, _insult_body()]),1),
                         (lambda : phrase([_you_are(), lit_phrase("such a"), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),3),
                         (lambda : phrase([_you_are(), _a, rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),4),
                         (lambda : phrase([_I, rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), lit_phrase("you")]),2),
                         (lambda : phrase([_I, rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), lit_phrase("you")]),3)])()

def _you_are():
    return RandomChoice([(lit_phrase("you are"),1),
                         (lit_phrase("you're"),1),
                         (lit_phrase("I heard you're"),1),
                         (lit_phrase("you know  you're"),1)])

def _I_need():
    return RandomChoice([(lit_phrase("I need you to"),1),
                         (lit_phrase("I want you to"),1),
                         (lit_phrase("I wish that you d"),1),
                         (lit_phrase("I hope you"),1),
                         (lit_phrase("I think you should"),1),
                         (lit_phrase("please"),1)])

def _insult_tail():
    return RandomChoice([(lambda : _nil,8),
                         (lambda : phrase([_comma, lit_phrase("you"), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),1),
                         (lambda : phrase([_comma, lit_phrase("you"), rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),1),
                         (lambda : phrase([_comma, _and, _I_need(), rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE)]),1),
                         (lambda : phrase([_comma, _and, _I_need(), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), lit_phrase("yourself")]),1)])()

def _insult():
    return phrase([_insult_body(), _insult_tail()])

