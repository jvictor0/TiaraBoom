from grammar import _sentence, _advice, _sentence_bother, _insult

def ConstructSentence(phr):
    punc = False
    first = True
    result = []
    for w in phr:
        tpunc = (w in [",",".","?","!"])
        if tpunc and first:
            continue
        if first:
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

def SentenceBother():
    return ConstructSentence(_sentence_bother())

def Insult():
    return ConstructSentence(_insult())
