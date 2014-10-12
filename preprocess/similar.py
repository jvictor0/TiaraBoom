from nltk.corpus import wordnet as wn
import tiara.global_data as g
import json

def SimilarWords(words):
    result = []
    for syn in [s for word in words for s in wn.synsets(word, None)]:
        result.extend([n for n in syn.lemma_names() if not '_' in n and n not in result + words])
        result.extend([b for m in syn.lemmas() for a in m.antonyms() for b in a.name() if not '_' in n and n not in result + words])
    return result
    
def SimilarWordsDict():
    g_data = g.GlobalData()
    result = {}
    for word,unused in g_data.cooccuring:
        thism = ' '.join(SimilarWords(g_data.WordFamily(word))).lower()
        if thism != '':
            result[word] = thism
    with open("data/similar.json","w") as f:
        print >>f, json.dumps(result)
