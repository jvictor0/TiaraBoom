from grammar import _sentence, _advice, _insult

def ConstructSentence(phr):
    punc = False
    first = True
    result = []
    for w in phr:
        tpunc = (w in [",",".","?","!",";","..."])
        if tpunc and first:
            continue
        if first or result[-1] in [".","?","!"]:
            result.append(w[0].upper() + w[1:])
            first = False
            continue
        if punc and tpunc:
            result[-1] = w
        else:
            result.append(w)
        punc = tpunc
    return result

def Sentence():
    return ConstructSentence(_sentence())

