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

def lit_phrase(str):
    return phrase(str.split(' '))

def RandomChoice(choices):
   total = sum(w for c, w in choices)
   r = random.uniform(0, total)
   upto = 0
   for c, w in choices:
      if upto + w > r:
         return c
      upto += w
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

def fix_helper(is_helper, adverb, verb):
    result = []
    for i,v in enumerate(verb):
        if not is_helper(v):
            break
    return phrase([verb[:i],adverb,verb[i:]])


_comma = lit_phrase(",")
_question = lit_phrase("?")
