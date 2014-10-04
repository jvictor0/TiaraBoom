from grammar_util import *
from grammar_util import _comma, _question


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

NOUN_SINGULAR = 't'

NOUN_PLURAL = 'f'

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

def _adverb_punc(begin, end):
    return (phrase([rand_word(POS_ADVERB, ADVERB_NORMAL), end]) if _nil == begin else rand_word(POS_ADVERB, ADVERB_NORMAL))

def _sub_clause_punc(begin, end):
    return phrase([begin, _sub_clause(), end])

def _possible_sub_clause_func():
    return RandomChoice([(_sub_clause_punc,1),
                         (_nil_func2,12)])

def _possible_sub_clause(begin, end):
    return _possible_sub_clause_func()(begin, end)

def _possible_adverb_func():
    return RandomChoice([(_adverb_punc,1),
                         (_nil_func2,3)])

def _possible_adverb(begin, end):
    return _possible_adverb_func()(begin, end)

def _sub_clause_start():
    return RandomChoice([(lambda : _subordinating_conjunction(),1)])()

def _sub_clause():
    return phrase([_sub_clause_start(), _indep_clause()])

def rand_plural():
    return RandomChoice([(True,1),
                         (False,2)])

def _indep_clause():
    return _indep_clause_pl(rand_plural())

def _subjunctive_clause():
    return _subjunctive_clause_pl(rand_plural())

def _conditional_clause():
    return _conditional_clause_pl(rand_plural())

def _indep_clause_pl_random():
    return RandomChoice([(_indep_clause_pl_intrans_2,3),
                         (_indep_clause_pl_intrans_3,2),
                         (_indep_clause_pl_trans_2,6),
                         (_indep_clause_pl_trans_3,3),
                         (_indep_clause_pl_intrans_ego_2,5),
                         (_indep_clause_pl_intrans_ego_3,2),
                         (_indep_clause_pl_trans_ego_2,6),
                         (_indep_clause_pl_trans_ego_3,3),
                         (_being_clause,7)])

def _command():
    return RandomChoice([(lambda : phrase([rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), you), _possible_adverb(_nil, _nil)]),1),
                         (lambda : phrase([_possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), you)]),1),
                         (lambda : phrase([_be, _being_target(False, you)]),2)])()

def _present_question():
    sub_and_tag = _subject_and_tag(rand_plural())
    return phrase([_present_question_word(sub_and_tag[1]), sub_and_tag[0], _present_question_suffix(sub_and_tag[1]), _question])

def _transitive_question():
    sub_and_tag = _subject_and_tag(rand_plural())
    return phrase([_transitive_question_word(), rand_word(POS_COUNTABLE_NOUN, NOUN_SINGULAR), _simple_question_word(sub_and_tag[1]), sub_and_tag[0], rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _likely_prepositional_phrase(), _transitive_question_suffix(), _question])

def _possible_advice_sub_clause():
    return RandomChoice([(lambda : _nil,7),
                         (lambda : phrase([_subordinating_conjunction(), _indep_clause()]),5),
                         (lambda : phrase([_coordinating_conjunction_advice(), _command()]),5),
                         (lambda : phrase([_comma, _negatory_conjunction(), _being_clause_conditional(rand_plural())]),5)])()

def _being_question_suffix(pl,pron):
    return RandomChoice([(lambda : _nil,20),
                         (lambda : lit_phrase("or am I crazy"),1),
                         (lambda : lit_phrase("or am I dumb"),1),
                         (lambda : lit_phrase("or am I on crack"),1),
                         (lambda : lit_phrase("or am I on wrong"),1),
                         (lambda : phrase([lit_phrase("or am I "), _being_target(False, I)]),5),
                         (lambda : phrase([lit_phrase("or are you "), _being_target(False, you)]),5),
                         (lambda : phrase([_or, _being_target(pl, pron)]),5),
                         (lambda : phrase([lit_phrase("or just"), _being_target(pl, pron)]),5)])()

def _being_question_past_suffix(pl,pron):
    return RandomChoice([(lambda : _nil,40),
                         (lambda : lit_phrase("or am I crazy"),1),
                         (lambda : lit_phrase("or am I dumb"),1),
                         (lambda : lit_phrase("or am I on crack"),1),
                         (lambda : lit_phrase("or am I on wrong"),1),
                         (lambda : phrase([lit_phrase("or am I "), _being_target(False, I)]),10),
                         (lambda : phrase([lit_phrase("or are you "), _being_target(False, you)]),10),
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
                         (lambda : phrase([_or, _being_target(pl, pron)]),10),
                         (lambda : phrase([lit_phrase("or just"), _being_target(pl, pron)]),10),
                         (lambda : _being_question_smart_suffix(pl, pron),10)])()

def _being_question_smart_suffix(pl, pron):
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_or, _to_be_pos(subj_and_tag[1]), subj_and_tag[0], _being_target(plurality, subj_and_tag[1])])

def _being_question():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_fix_am_not(_to_be(subj_and_tag[1])), subj_and_tag[0], _being_target(plurality, subj_and_tag[1]), _being_question_suffix(plurality, subj_and_tag[1]), _question])

def _being_question_alt():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    target = _being_target(plurality, subj_and_tag[1])
    return phrase([_fix_am_not(_to_be_pos(subj_and_tag[1])), subj_and_tag[0], target, _or, _fix_am_not(_to_be_pos(subj_and_tag[1])), subj_and_tag[0], target, _question])

def _being_question_past():
    plurality = rand_plural()
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([_fix_am_not(_to_be_past(subj_and_tag[1])), subj_and_tag[0], _being_target(plurality, subj_and_tag[1]), _being_question_past_suffix(plurality, subj_and_tag[1]), _question])

def _fix_am_not(p):
    return (lit_phrase("aren't") if p == lit_phrase("am not") else p)

def _present_question_word(pronoun):
    return RandomChoice([(lambda : lit_phrase("did"),1),
                         (lambda : lit_phrase("when did"),1),
                         (lambda : lit_phrase("where did"),1),
                         (lambda : lit_phrase("why did"),1),
                         (lambda : lit_phrase("how did"),1),
                         (lambda : lit_phrase("didn t"),1),
                         (lambda : lit_phrase("why didn t"),1),
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
                         (lambda : lit_phrase("didn t"),1),
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

def _indep_clause_pl(plural_):
    return _indep_clause_pl_random()(plural_)

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

def _indep_clause_pl_trans_no_obj(plural_, no_adverb):
    return phrase([_noun(plural_, False), fix_helper(is_helper, (_possible_adverb(_nil, _nil) if no_adverb else _nil), _verb(plural_)(POS_TRANSITIVE_VERB))])

def _indep_clause_pl_intrans_1(plural_):
    return phrase([_possible_adverb(_nil, _nil), _noun(plural_, False), _verb(plural_)(POS_INTRANSITIVE_VERB), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_2(plural_):
    return phrase([_noun(plural_, False), fix_helper(is_helper, _possible_adverb(_nil, _nil), _verb(plural_)(POS_INTRANSITIVE_VERB)), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_3(plural_):
    return phrase([_noun(plural_, False), _verb(plural_)(POS_INTRANSITIVE_VERB), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_intrans(plural_):
    return phrase([_subject(plural_), _were, _possible_adverb(_nil, _nil), rand_word(POS_INTRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_infin_intrans(plural_):
    return phrase([_subject(plural_), _were, _to, _possible_adverb(_nil, _nil), rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_prepositional_phrase()])

def _conditional_clause_pl_intrans(plural_):
    return phrase([_subject(plural_), _conditional_helper(), _be, _possible_adverb(_nil, _nil), rand_word(POS_INTRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _possible_prepositional_phrase()])

def _conditional_clause_pl_infin_intrans(plural_):
    return phrase([_subject(plural_), _conditional_helper(), _possible_adverb(_nil, _nil), rand_word(POS_INTRANSITIVE_VERB, VERB_INFINITIVE), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_ego_1(plural_):
    return phrase([_possible_adverb(_nil, _nil), (_we if plural_ else _I), _verb_ego(plural_)(POS_INTRANSITIVE_VERB), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_ego_2(plural_):
    return phrase([(_we if plural_ else _I), fix_helper(is_helper, _possible_adverb(_nil, _nil), _verb_ego(plural_)(POS_INTRANSITIVE_VERB)), _possible_prepositional_phrase()])

def _indep_clause_pl_intrans_ego_3(plural_):
    return phrase([(_we if plural_ else _I), _verb_ego(plural_)(POS_INTRANSITIVE_VERB), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_1(plural_):
    return phrase([_possible_adverb(_nil, _nil), _indep_clause_pl_trans_no_obj(plural_, True), _object(rand_plural(), False), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_2(plural_):
    return phrase([_indep_clause_pl_trans_no_obj(plural_, False), _object(rand_plural(), False), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_3(plural_):
    return phrase([_indep_clause_pl_trans_no_obj(plural_, True), _object(rand_plural(), False), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _were, _possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _object(rand_plural(), subj_and_tag[1]), _possible_prepositional_phrase()])

def _subjunctive_clause_pl_infin_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _were, _to, _possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), subj_and_tag[1]), _possible_prepositional_phrase()])

def _conditional_clause_pl_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _conditional_helper(), _be, _possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_CONJUGATED, CONJ_PRESENT_PART), _object(rand_plural(), subj_and_tag[1]), _possible_prepositional_phrase()])

def _conditional_clause_pl_infin_trans(plural_):
    subj_and_tag = _subject_and_tag(plural_)
    return phrase([subj_and_tag[0], _conditional_helper(), _possible_adverb(_nil, _nil), rand_word(POS_TRANSITIVE_VERB, VERB_INFINITIVE), _object(rand_plural(), subj_and_tag[1]), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_ego_1(plural_):
    return phrase([_possible_adverb(_nil, _nil), (_we if plural_ else _I), _verb_ego(plural_)(POS_TRANSITIVE_VERB), _object(rand_plural(), (we if plural_ else I)), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_ego_2(plural_):
    return phrase([(_we if plural_ else _I), fix_helper(is_helper, _possible_adverb(_nil, _nil), _verb_ego(plural_)(POS_TRANSITIVE_VERB)), _object(rand_plural(), (we if plural_ else I)), _possible_prepositional_phrase()])

def _indep_clause_pl_trans_ego_3(plural_):
    return phrase([(_we if plural_ else _I), _verb_ego(plural_)(POS_TRANSITIVE_VERB), _object(rand_plural(), (we if plural_ else I)), _possible_adverb(_nil, _nil), _possible_prepositional_phrase()])

def _being_clause(plurality):
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([subj_and_tag[0], _to_be(subj_and_tag[1]), _being_target(plurality, subj_and_tag[1])])

def _being_clause_subjunctive(plurality):
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([subj_and_tag[0], _were, _being_target(plurality, subj_and_tag[1])])

def _being_clause_conditional(plurality):
    subj_and_tag = _subject_and_tag(plurality)
    return phrase([subj_and_tag[0], _conditional_helper(), _be, _being_target(plurality, subj_and_tag[1])])

def _to_be(tag):
    return RandomChoice([(lambda : _to_be_pos(tag),3),
                         (lambda : _to_be_(tag),1)])()

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

def _to_be_(tag):
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
    return RandomChoice([(lambda : _to_be_past_pos(tag),3),
                         (lambda : _to_be_past_(tag),1)])()

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

def _to_be_past_(tag):
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
        return (lit_phrase("us") if plurality else lit_phrase("me"))

def _you_object(pronoun, plurality):
    if pronoun == you:
        return lit_phrase("yourself")
    else:
        return (_being_target(plurality, pronoun) if plurality else lit_phrase("you"))

def _being_target(plurality,pronoun):
    return RandomChoice([(lambda : rand_word(POS_PROPER_NOUN, PROPER_NOUN_FORENAME),2),
                         (lambda : _me_object(pronoun, plurality),1),
                         (lambda : _you_object(pronoun, plurality),1),
                         (lambda : phrase([_article_indef(not(plurality)), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, not(plurality))]),2),
                         (lambda : phrase([_like, _article_indef(not(plurality)), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, not(plurality))]),2),
                         (lambda : _prepositional_phrase(),3),
                         (lambda : _adj(),3),
                         (lambda : phrase([_adj_comparative(), _than, _object(plurality, pronoun)]),3),
                         (lambda : phrase([_adj_comparative_1(), _than, _object(plurality, pronoun), _and, _adj_comparative_1(), _than, _object(plurality, pronoun)]),3),
                         (lambda : phrase([_the, _adj_superlative(not(plurality))]),3)])()

def _noun(plural, simple):
    return (_noun_pl(simple) if plural else _noun_sing(simple))

def _verb(plural):
    return (_verb_pl if plural == True else _verb_sing)

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

def _advice_prefix():
    return RandomChoice([(lit_phrase("I think you should"),1),
                         (lit_phrase("you should"),1),
                         (lit_phrase("you ought to"),1),
                         (lit_phrase("you ought not"),1),
                         (lit_phrase("you shouldn't"),1),
                         (lit_phrase("perhaps you should"),1),
                         (lit_phrase("perhaps you ought to"),1),
                         (lit_phrase("perhaps you shouldn't"),1),
                         (lit_phrase("please"),2),
                         (lit_phrase("please don't"),1),
                         (lit_phrase("you need to"),1),
                         (lit_phrase("you gotta"),1),
                         (lit_phrase("perhaps you need to"),1),
                         (lit_phrase("perhaps you gotta"),1),
                         (lit_phrase("you don't have to"),1),
                         (lit_phrase("I have to ask you to"),1)])

def _sentence():
    return RandomChoice([(lambda : phrase([_possible_prefix(), _sentence_random(), _end_punc_random()]),3),
                         (lambda : phrase([_sentence_random(), _possible_suffix(), _end_punc_random()]),2),
                         (lambda : phrase([_second_conditional_prefix(), _subjunctive_clause(), _comma, _conditional_clause(), _end_punc_random()]),3),
                         (lambda : phrase([_conditional_clause(), _second_conditional_prefix(), _subjunctive_clause(), _end_punc_random()]),3),
                         (lambda : phrase([_subjunctive_prefix(), _subjunctive_clause(), _question]),2),
                         (_advice,2),
                         (_question_sentence,3)])()

def _sentence_bother():
    return RandomChoice([(lambda : phrase([_possible_prefix(), _sentence_random(), _end_punc_random()]),3),
                         (lambda : phrase([_sentence_random(), _possible_suffix(), _end_punc_random()]),2),
                         (lambda : phrase([_second_conditional_prefix(), _subjunctive_clause(), _comma, _conditional_clause(), _end_punc_random()]),3),
                         (lambda : phrase([_conditional_clause(), _second_conditional_prefix(), _subjunctive_clause(), _end_punc_random()]),3),
                         (lambda : phrase([_subjunctive_prefix(), _subjunctive_clause(), _question]),2),
                         (_advice,12),
                         (_question_sentence,18)])()

def _end_punc_random():
    return RandomChoice([(_exclamation,1),
                         (_period,9)])

def _sentence_random():
    return RandomChoice([(_sentence_single,5),
                         (_sentence_compound,2)])()

def _sentence_single():
    return phrase([_possible_sub_clause(_comma, _comma), _indep_clause(), _possible_sub_clause(_comma, _nil), _comma])

def _sentence_compound_conjunction():
    return phrase([_sentence_single(), _coordinating_conjunction(), _sentence_single()])

def _sentence_compound_adverb():
    return phrase([_sentence_single(), _semicolon, rand_word(POS_ADVERB, ADVERB_CONJUNCTIVE), _comma, _sentence_single()])

def _sentence_compound():
    return RandomChoice([(_sentence_compound_conjunction,5),
                         (_sentence_compound_adverb,1)])()

def _advice():
    return phrase([_advice_prefix(), _command(), _possible_advice_sub_clause(), _end_punc_random()])

def _question_sentence():
    return RandomChoice([(_present_question(),2),
                         (_transitive_question(),1),
                         (_being_question(),1),
                         (_being_question_past(),1),
                         (_being_question_alt(),1)])

def _prepositional_phrase():
    return phrase([_preposition_sing(), _noun_phrase_no_clause(rand_plural())])

def _possible_prepositional_phrase():
    return RandomChoice([(_prepositional_phrase,1),
                         (_nil_func0,6)])()

def _likely_prepositional_phrase():
    return RandomChoice([(_prepositional_phrase,1),
                         (_nil_func0,1)])()

def _preposition_sing():
    return RandomChoice([(lit_phrase("across from"),1),
                         (lit_phrase("around"),1),
                         (lit_phrase("beyond"),1),
                         (lit_phrase("by"),1),
                         (lit_phrase("for"),2),
                         (lit_phrase("like"),3),
                         (lit_phrase("near"),1),
                         (lit_phrase("with"),1),
                         (lit_phrase("without"),1)])

def _article(plurality):
    return (_article_sing() if plurality else _article_pl())

def _article_indef(plurality):
    return (_article_sing_indef() if plurality else _article_pl_indef())

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

def _article_pl_indef():
    return RandomChoice([(_some,4),
                         (_those,16),
                         (_two,1),
                         (_three,1),
                         (_four,1),
                         (_five,1),
                         (_six,1),
                         (lit_phrase("my"),7),
                         (lit_phrase("your"),7),
                         (lit_phrase("his"),2),
                         (lit_phrase("her"),2),
                         (lit_phrase("their"),2)])

def _article_sing_indef():
    return RandomChoice([(_a,8),
                         (_some,1),
                         (lit_phrase("my"),6),
                         (lit_phrase("your"),6),
                         (lit_phrase("his"),2),
                         (lit_phrase("her"),2),
                         (lit_phrase("their"),3)])

def _coordinating_conjunction():
    return RandomChoice([(lit_phrase("and"),1),
                         (lit_phrase("or"),1),
                         (lit_phrase("but"),1),
                         (lit_phrase("yet"),1),
                         (lit_phrase("for"),1),
                         (lit_phrase("so"),1)])

def _coordinating_conjunction_advice():
    return RandomChoice([(lit_phrase("and"),1),
                         (lit_phrase("and try to"),1),
                         (lit_phrase("and you will"),1),
                         (lit_phrase("and don't"),1),
                         (lit_phrase("or"),1),
                         (lit_phrase("or you won't be able to"),1),
                         (lit_phrase("but"),1),
                         (lit_phrase("but don't"),1),
                         (lit_phrase("but try to"),1),
                         (lit_phrase("yet"),1),
                         (lit_phrase("so you can"),1)])

def _subordinating_conjunction():
    return RandomChoice([(lit_phrase("after"),1),
                         (lit_phrase("till"),1),
                         (lit_phrase("if"),1),
                         (lit_phrase("unless"),1),
                         (lit_phrase("inasmuch as"),1),
                         (lit_phrase("until"),1),
                         (lit_phrase("as if"),1),
                         (lit_phrase("in order that"),1),
                         (lit_phrase("when"),1),
                         (lit_phrase("as long as"),1),
                         (lit_phrase("lest"),1),
                         (lit_phrase("whenever"),1),
                         (lit_phrase("as much as"),1),
                         (lit_phrase("now that"),1),
                         (lit_phrase("where"),1),
                         (lit_phrase("as soon as"),1),
                         (lit_phrase("provided"),1),
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
                         (_adj_2_and,1),
                         (_adj_3,1)])()

def _adj():
    return RandomChoice([(_adj_1,8),
                         (_adj_2_and,3),
                         (_adj_3,1)])()

def _adj_1():
    return rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)

def _adj_2():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _comma, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)])

def _adj_2_and():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _and, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)])

def _adj_3():
    return phrase([rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _comma, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD), _comma, _and, rand_word(POS_ADJECTIVE, ADJECTIVE_GOOD)])

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
                         (lit_phrase("I ve seen"),1),
                         (lit_phrase("I ve know"),1),
                         (lit_phrase("I ve heard of"),1)])

def _possible_adj_clause():
    return RandomChoice([(_nil_func0,2),
                         (_adj_clause,3)])()

def _adj_clause():
    return RandomChoice([(_that_adj_clause,3),
                         (_which_adj_clause,1)])()

def _that_adj_clause():
    return phrase([_that, _indep_clause_pl_trans_no_obj(rand_plural(), False)])

def _which_adj_clause():
    return phrase([_which, _indep_clause_pl_trans_no_obj(rand_plural(), False)])

def _noun_pl(simple):
    return RandomChoice([(lambda : _noun_phrase(NOUN_PLURAL, simple),100),
                         (lambda : phrase([_noun_phrase_no_clause(NOUN_SINGULAR), _and, _noun_phrase(NOUN_SINGULAR, simple)]),25),
                         (lambda : phrase([_noun_phrase_no_clause(NOUN_SINGULAR), _comma, _noun_phrase_no_clause(NOUN_SINGULAR), _comma, _and, _noun_phrase(NOUN_SINGULAR, simple)]),1)])()

def _noun_sing(simple):
    return _noun_phrase(NOUN_SINGULAR, simple)

def _noun_phrase_no_clause(plurality):
    return (_noun_phrase_no_clause_pl() if not(plurality) else _noun_phrase_no_clause_sing())

def _noun_phrase_no_clause_pl():
    return RandomChoice([(lambda : phrase([_article(False), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, False)]),8),
                         (lambda : phrase([_the, rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), rand_word(POS_COUNTABLE_NOUN, False)]),1)])()

def _noun_phrase_no_clause_sing():
    return RandomChoice([(lambda : phrase([_article(True), _possible_adj(), rand_word(POS_COUNTABLE_NOUN, True)]),8),
                         (lambda : phrase([_the, rand_word(POS_ADJECTIVE, ADJECTIVE_OTHER, ADJECTIVE_SUPERLATIVE), rand_word(POS_COUNTABLE_NOUN, True)]),1),
                         (lambda : rand_word(POS_PROPER_NOUN, PROPER_NOUN_FORENAME),2)])()

def _noun_phrase(plurality, simple):
    return (_noun_phrase_no_clause(plurality) if simple else phrase([_noun_phrase_no_clause(plurality)]))

def _object_sing(is_I):
    return RandomChoice([(lambda : _noun(False, False),20),
                         (lambda : (lit_phrase("myself") if is_I == I else (_object_sing(we) if is_I == we else lit_phrase("me"))),5),
                         (lambda : (lit_phrase("himself") if is_I == he else lit_phrase("him")),1),
                         (lambda : (lit_phrase("herself") if is_I == she else lit_phrase("her")),1),
                         (lambda : (lit_phrase("itself") if is_I == it else lit_phrase("it")),2),
                         (lambda : (lit_phrase("yourself") if is_I == you else lit_phrase("you")),2)])()

def _object_pl(is_we):
    return RandomChoice([(lambda : _noun(True, False),20),
                         (lambda : (lit_phrase("ourselves") if is_we == we else lit_phrase("us")),3),
                         (lambda : (lit_phrase("themselves") if is_we == them else lit_phrase("them")),2),
                         (lambda : lit_phrase("em"),2)])()

def _object(plurality, is_ego):
    return (_object_pl(is_ego) if plurality else _object_sing(is_ego))

def _subject_and_tag(plurality):
    return (_subj_and_tag_pl() if plurality else _subj_and_tag_sing())

def _subj_and_tag_sing():
    return RandomChoice([(lambda : (_noun(False, False), sing),10),
                         (lambda : (lit_phrase("I"), I),5),
                         (lambda : (lit_phrase("he"), he),1),
                         (lambda : (lit_phrase("she"), she),1),
                         (lambda : (lit_phrase("it"), it),2),
                         (lambda : (lit_phrase("you"), you),10)])()

def _subj_and_tag_pl():
    return RandomChoice([(lambda : (_noun(True, False), plural),10),
                         (lambda : (lit_phrase("we"), we),5),
                         (lambda : (lit_phrase("they"), they),3)])()

def _subject(plurality):
    return _subject_and_tag(plurality)[0]

def _verb_pl_func():
    return RandomChoice([(_verb_simple_present_pl,4),
                         (_verb_simple_past,4),
                         (_verb_simple_future,3),
                         (_verb_present_continuous_pl,3),
                         (_verb_past_continuous_pl,3),
                         (_verb_future_continuous,3),
                         (_verb_present_perfect_pl,2),
                         (_verb_past_perfect,2),
                         (_verb_future_perfect,2),
                         (_verb_present_perfect_continuous_pl,1),
                         (_verb_past_perfect_continuous,1),
                         (_verb_future_perfect_continuous,1)])

def _verb_sing_func():
    return RandomChoice([(_verb_simple_present_sing,4),
                         (_verb_simple_past,4),
                         (_verb_simple_future,3),
                         (_verb_present_continuous_sing,3),
                         (_verb_past_continuous_sing,3),
                         (_verb_future_continuous,3),
                         (_verb_present_perfect_sing,2),
                         (_verb_past_perfect,2),
                         (_verb_future_perfect,2),
                         (_verb_present_perfect_continuous_sing,1),
                         (_verb_past_perfect_continuous,1),
                         (_verb_future_perfect_continuous,1)])

def _verb_ego_func():
    return RandomChoice([(_verb_simple_present_ego,4),
                         (_verb_simple_past,4),
                         (_verb_simple_future,3),
                         (_verb_present_continuous_ego,3),
                         (_verb_past_continuous_sing,3),
                         (_verb_future_continuous,3),
                         (_verb_present_perfect_ego,2),
                         (_verb_past_perfect,2),
                         (_verb_future_perfect,2),
                         (_verb_present_perfect_continuous_ego,1),
                         (_verb_past_perfect_continuous,1),
                         (_verb_future_perfect_continuous,1)])

def _verb_we_func():
    return RandomChoice([(_verb_simple_present_ego,4),
                         (_verb_simple_past,4),
                         (_verb_simple_future,3),
                         (_verb_present_continuous_pl,3),
                         (_verb_past_continuous_pl,3),
                         (_verb_future_continuous,3),
                         (_verb_present_perfect_ego,2),
                         (_verb_past_perfect,2),
                         (_verb_future_perfect,2),
                         (_verb_present_perfect_continuous_ego,1),
                         (_verb_past_perfect_continuous,1),
                         (_verb_future_perfect_continuous,1)])

def is_helper(x):
    return x in [_not, _would, _will, _should, _may, _might, _could, _must, _is, _are, _am, _was, _were, _be, _has, _have, _had, _been]

def _verb_pl(trans):
    return _verb_pl_func()(trans)

def _verb_sing(trans):
    return _verb_sing_func()(trans)

def _verb_ego(plural):
    return (_verb_we_func() if plural else _verb_ego_func())

def _random_inflect():
    return RandomChoice([(lambda : phrase([_random_modal(), _not]),2),
                         (_random_modal,5)])()

def _random_modal():
    return RandomChoice([(_would,3),
                         (_will,8),
                         (_should,2),
                         (_may,1),
                         (_might,2),
                         (_could,2),
                         (_must,2)])

def _verb_simple_present_sing(trans):
    return rand_word(trans, VERB_CONJUGATED, CONJ_3RD_SING)

def _verb_simple_present_pl(trans):
    return rand_word(trans, VERB_INFINITIVE)

def _verb_simple_present_ego(trans):
    return rand_word(trans, VERB_INFINITIVE)

def _verb_simple_past(trans):
    return rand_word(trans, VERB_CONJUGATED, CONJ_PAST)

def _verb_simple_future(trans):
    return phrase([_random_inflect(), rand_word(trans, VERB_INFINITIVE)])

def _verb_present_continuous_sing(trans):
    return phrase([_is, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_present_continuous_pl(trans):
    return phrase([_are, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_present_continuous_ego(trans):
    return phrase([_am, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_past_continuous_sing(trans):
    return phrase([_was, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_past_continuous_pl(trans):
    return phrase([_were, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_future_continuous(trans):
    return phrase([_random_inflect(), _be, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_present_perfect_sing(trans):
    return phrase([_has, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)])

def _verb_present_perfect_pl(trans):
    return phrase([_have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)])

def _verb_present_perfect_ego(trans):
    return phrase([_have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)])

def _verb_past_perfect(trans):
    return phrase([_had, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)])

def _verb_future_perfect(trans):
    return phrase([_random_inflect(), _have, rand_word(trans, VERB_CONJUGATED, CONJ_PAST_PART)])

def _verb_present_perfect_continuous_sing(trans):
    return phrase([_has, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_present_perfect_continuous_pl(trans):
    return phrase([_have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_present_perfect_continuous_ego(trans):
    return phrase([_have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_past_perfect_continuous(trans):
    return phrase([_had, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _verb_future_perfect_continuous(trans):
    return phrase([_random_inflect(), _have, _been, rand_word(trans, VERB_CONJUGATED, CONJ_PRESENT_PART)])

def _insult_body():
    return RandomChoice([(lambda : phrase([_you_are(), _being_target(False, you)]),4),
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

