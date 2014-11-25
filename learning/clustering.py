import json
import string
import collections
from scipy.spatial.distance import cosine
import math
import copy

import cPickle

import numpy as np

from nltk import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from pprint import pprint

import Pycluster
from Pycluster import distancematrix, kmedoids

import tiara.global_data as g
from tiara.util import *

from scipy.stats import norm

g_data = g.GlobalData()

def ProcessFile(dict, name):
    with open(name,'r') as f:
        for j,line in enumerate(f):
            if j % 1000 == 0:
                print j
            i,jsn = line.split(' ', 1)
            jsn = json.loads(jsn)
            assert int(i) not in dict
            if len(jsn) > 0 and jsn[0]['user']['lang'][:2] != 'en':
                print jsn[0]['user']['lang']
                continue
            dict[int(i)] = [(t['text'],"https://twitter.com/%s/status/%d" % (t['user']['screen_name'],t['id']), ' '.join(LKDL(t,'hashtags'))) for t in jsn if t['lang'] == 'en' and all(ord(c) < 128 for c in t['text'] + t['user']['screen_name'])]
            if len(dict[int(i)]) == 0:
                del dict[int(i)]

def DumpFile(dict):
    with open("human_readable_tweets",'w') as f:
        for k,v in dict.iteritems():
            print >>f, "%s" % k
            for vi,url in v:
                if all(ord(c) < 128 for c in vi+url):
                    print >>f, url
                    print >>f, vi
                    print >>f, ''

def ProcessText(text):
    if isinstance(text,unicode):
        text = str(text)
    text = text.translate(None,string.punctuation+'\n')
    tokens = word_tokenize(text)

    tokens = [NotNone(g_data.FamilyRepresentative(t),t) for t in tokens]
        
    return ' '.join(tokens)

def ToHumanReadable():
    d = {}
    ProcessFile(d, "learnings/save.targets")
    DumpFile(d)

def ToTFIDable(d = {}):
    if len(d) == 0:
        ProcessFile(d, "learning/save.targets")
    with open("learning/save.documents","w") as f:
        l = 0
        for i,text in d.iteritems():
            if l % 1000 == 0:
                print l
            print >>f, "%d %s" % (i,ProcessText(' '.join([t[0] for t in text])))
            l = l + 1

def ToHashtags(d = {}):
    if len(d) == 0:
        ProcessFile(d, "learning/save.targets")
    with open("learning/save.hashtags","w") as f:
        l = 0
        for i,text in d.iteritems():
            if l % 1000 == 0:
                print l
            print >>f, "%d %s" % (i,' '.join([t[2].lower() for t in text if t[2] !=  '']))
            l = l + 1

def LoadHashtags():
    with open("learning/save.hashtags","r") as f:
        result = [t.strip().split(' ')[1:] for t in f]
    return result

def LoadTFIDable():
    with open("learning/save.documents","r") as f:
        result = [t.split(' ',1)[1] for t in f]
    return result

def LoadIDs():
    with open("learning/save.documents","r") as f:
        result = [int(t.split(' ',1)[0]) for t in f]
    return result

def HashtagDict():
    return dict(zip(LoadHashtagIDs(), LoadHashtags()))

def LoadHashtagIDs():
    with open("learning/save.hashtags","r") as f:
        result = [int(t.split(' ',1)[0]) for t in f]
    return result

def UsersOfHashtag(hashtag, d=None):
    if d is None:
        d = HashtagDict()
    return [k for k,v in HashtagDict().iteritems() if hashtag in v]

def TagCounts(tags, group_by_user = False):
    d = {}
    for tag in tags:
        s = set([])
        for t in tag:
            if t not in d:
                d[t] = 0
            if not group_by_user or not t in s:
                d[t] += 1
                if group_by_user:
                    s.add(t)
    return [(a,b) for b,a in sorted([(b,a) for a,b in d.iteritems()])][-1::-1], d

def CoOccuring(hashtag, top = None, htu = None, group_by_user = False):
    if htu is None:
        htu = HashtagDict()
    hts,htds= TagCounts([htu[x] for x in UsersOfHashtag(hashtag)], group_by_user)
    if not top is None:
        return hts[:top]
    return hts,htds

def Interests(hashtag, top = None, htu = None, freq = None):
    if htu is None:
        htu = HashtagDict()
    if freq is None:
        freq = TagCounts(LoadHashtags(), True)[1][hashtag]
    hs = CoOccuring(hashtag, htu = htu, group_by_user = True)[0]
    interests =[(-float(b)/freq,a) for a,b in hs]
    return [(a,-b) for b,a in sorted(interests)][:(-1 if top is None else top)]

def Cluster(d = {}):
    if len(d) == 0:
        ProcessFile(d, "learning/save.targets")
    return cluster_texts([' '.join([t[0][:-1] for t in text]) for text in d.values()][:1000], 15)

def StopWords():
    with open("learning/stopwords","r") as f:
        result = [t.strip().translate(None,string.punctuation).lower() for t in f]
    return result

def Report(clusters=7):
    transd = cPickle.load(open( "save.tfidf_model", "rb" ) )
    ns = cPickle.load(open( "save.features", "rb" ) )
    km_model = cPickle.load(open( "save.km_model", "rb" ) )
    
    ids = LoadIDs()

    cluster_ids = list(set(km_model))
    for i in xrange(clusters):
        print "Cluster %d:" % i
        center = transd[cluster_ids[i]]
        print "   Most Important Words: %s" % ', '.join([ns[w] for w in Top(15,center.todense().tolist()[0])])
        users = Top(10,[-CosineDistance(t,center) for t in transd])
        print "   Most archetypal users:"
        for j in users:
            print "      https://twitter.com/intent/user?user_id=%d" % ids[j]

def ProfileURL(id):
    return "https://twitter.com/intent/user?user_id=%d" % id

def FullDistanceMatrix(points, distance_function):
    distances = []
    for p1 in points:
        temp = []
        for p2 in points:
            temp.append(distance_function(p1,p2))
        distances.append(temp)
    return distances

def CosineDistance(x,y):
    if x.getnnz() > y.getnnz():
        return CosineDistance(y,x)
    if x.getnnz() == 0:
        return 1.0 if y.getnnz() == 0 else float(np.dot(y.todense(),np.ones(y.shape[1])))
    return cosine(x.todense(), y.todense())
        
def Top(n,l):
    if n > len(l):
        return sorted(l)[-1::-1]
    return [y for x,y in sorted([(-a,b) for b,a in enumerate(l)])[:n]]

def ClusterTexts(texts, clusters=7):
    vectorizer = TfidfVectorizer(tokenizer = lambda t: t.split(' '),
                                 stop_words=StopWords(),
                                 max_df=0.5,
                                 min_df=0.1,
                                 lowercase=True)

    tfidf_model = vectorizer.fit_transform(texts)
    cPickle.dump( tfidf_model, open( "save.tfidf_model", "wb" ) )
    cPickle.dump( vectorizer.get_feature_names(), open( "save.features", "wb" ) )

#    tfidf_model = cPickle.load(open( "save.tfidf_model", "rb" ) )
 #   nm = cPickle.load(open( "save.features", "rb" ) )
    print "tdid'd"
    dists = 1-np.array(tfidf_model.todense().dot(tfidf_model.T.todense()))
    print "dists"
    km_model, error, nfound = kmedoids(dists, nclusters=clusters, npass=200)
    cPickle.dump(km_model, open("save.km_model","wb"))
    print "fit"
    print error
    print nfound


def HashtagPoints(i):
    if i <= 2:
        return float(i)
    return 3.0 - 1.0/2**(i-2)

def EmptyScore(scoring_dict):
    return { k : 0.0 for k in scoring_dict.keys() }

def HashtagScoreUser(hashtags, scoring_dict, score):
    d = {}
    for t in hashtags:
        if t not in d:
            d[t] = 0
        d[t] += 1
    for t in hashtags:
        for k,sd in scoring_dict.iteritems():
            score[k] += LKD0(sd,t) * HashtagPoints(d[t])

def SignalBoostUser(hashtags, scoring_dict, score):
    for k,sd in scoring_dict.iteritems():
        score[k] += 1.0/(1+len(hashtags)) * sd['_signal_boost']

def ShardBoostUser(user_id, scoring_dict, score):
    for k,sd in scoring_dict.iteritems():
        if sd['_shard'] == int(user_id) % sd['_mod']:
            score[k] += sd['_shard_boost']

def NormalPDF(mu, sigma, x):
    return norm.pdf((float(x) - mu)/sigma)

def StaticUserScore(jsons, score):
    points_for_more_tweets = 5.0
    points_for_friends = 5.0
    points_for_followers = 5.0
    for k in score.keys():
        score[k] += points_for_more_tweets * HashtagPoints(float(len(jsons))/5)
        score[k] += NormalPDF(800, 250, float(LKD0(jsons[0]['user'],'followers_count'))) * points_for_followers
        score[k] += NormalPDF(800, 250, float(LKD0(jsons[0]['user'],'friends_count'))) * points_for_friends

def MakeScoringDict():
    baseConservative = {
        "tcot" : 0.5,
        "ccot" : 1.0,
        "lcot" : 1.0,
        "obama": 0.25,
        "obamacare" : 0.75,
        "teaparty" : 2.0,
        "nra" : 1.5,
        "_mod" : 5,
        "_shard_boost" : 10,
        "_signal_boost" : 0
        }
    baseAutism = {
        "vaccines" : 1.0,
        "autism"   : 0.75,
        "vacinesnova" : 0.5,
        "hearthiswell" : 0.5,
        "cdcwhistleblower" : 1.0,
        "cdcfraud" : 1.5,
        "ebola" : 0.5,
        "climatechange" : 0.5,
        "health" : 0.25,
        "_mod" : 6,
        "_shard_boost" : 12,
        "_signal_boost" : 0.0
        }
    baseFallback = {
        "business" : 0.25,
        "life" : 0.25,
        "ff" :  0.25,
        "love" : 0.25,
        "quote" : 0.25,
        "_mod" : 4,
        "_shard_boost" : 8,
        "_signal_boost" : 10.0
        }
    scoring_dict = {
        "VanTheWinterer" : copy.copy(baseAutism), #story
        "ImDrErnst" : copy.copy(baseAutism), #doc
        "MarzipanIAm" : copy.copy(baseAutism), #doc
        "Rianna__Taylor" : copy.copy(baseFallback), #teen
        "AntonioBacusAmI" : copy.copy(baseFallback), #teen
        "Alexa_Smith9584" : copy.copy(baseAutism), #parent
        "LeeeroyOOOOman" : copy.copy(baseAutism), #parent
        "KarlKreegz20" : dict(baseFallback.items() + baseConservative.items()), #liberal
        "QueenNatLat" : dict(baseFallback.items() + baseConservative.items()), #liberal
        "Anold__Doyle" : copy.copy(baseConservative), #conservative
        "geneverasalomon" : copy.copy(baseConservative), #conservative
        "AppleBottomGrg" : copy.copy(baseConservative), #christian
        "MariaMunozOhMy" : copy.copy(baseConservative), #christian
        "SammyHerzt" : copy.copy(baseConservative), #muslim
        "LydiaGoldman253" : copy.copy(baseAutism), #story
        }
    scoring_dict["VanTheWinterer"]["_shard"] = 0
    scoring_dict["ImDrErnst"]["_shard"] = 1 
    scoring_dict["MarzipanIAm"]["_shard"] = 2
    scoring_dict["Rianna__Taylor"]["_shard"] = 0
    scoring_dict["AntonioBacusAmI"]["_shard"] = 1
    scoring_dict["Alexa_Smith9584"]["_shard"] = 3
    scoring_dict["LeeeroyOOOOman"]["_shard"] = 4
    scoring_dict["KarlKreegz20"]["_mod"] = 4
    scoring_dict["QueenNatLat"]["_mod"] = 4
    scoring_dict["KarlKreegz20"]["_shard"] = 2
    scoring_dict["QueenNatLat"]["_shard"] = 3
    scoring_dict["Anold__Doyle"]["_shard"] = 0
    scoring_dict["geneverasalomon"]["_shard"] = 1
    scoring_dict["AppleBottomGrg"]["_shard"] = 2
    scoring_dict["MariaMunozOhMy"]["_shard"] = 3
    scoring_dict["SammyHerzt"]["_shard"] = 4
    scoring_dict["LydiaGoldman253"]["_shard"] = 5

    scoring_dict["KarlKreegz20"]["_signal_boost"] = 40.0
    scoring_dict["QueenNatLat"]["_signal_boost"] = 40.0

    #muslim and christians more affinitive towards christian hashtags
    scoring_dict["AppleBottomGrg"]["ccot"] += 2
    scoring_dict["MariaMunozOhMy"]["ccot"] += 2
    scoring_dict["SammyHerzt"]["ccot"] += 2
    scoring_dict["AppleBottomGrg"]["pjnet"] = 1
    scoring_dict["MariaMunozOhMy"]["pjnet"] = 1
    scoring_dict["SammyHerzt"]["pjnet"] = 1

    scoring_dict["SammyHerzt"]["ferguson"] = 2
    scoring_dict["SammyHerzt"]["jttbm"] = 1
    scoring_dict["SammyHerzt"]["jtdtbm"] = 1
    scoring_dict["SammyHerzt"]["isis"] = 2
    scoring_dict["SammyHerzt"]["islam"] = 2

    return scoring_dict
    
def ScoreUsers():
    scores = {}
    scoring_dict = MakeScoringDict()
    hashtags = HashtagDict()
    with open('learning/save.targets','r') as f:
        for j,line in enumerate(f):
            if j % 1000 == 0:
                print j
            i,jsn = line.split(' ', 1)
            jsn = json.loads(jsn)
            assert int(i) not in scores
            if len(jsn) ==  0 or jsn[0]['user']['lang'][:2] != 'en':
                if len(jsn) == 0:
                    print "len 0"
                else:
                    print jsn[0]['user']['lang']
                continue
            if int(i) not in hashtags:
                print "notag"
                continue
            if LKD0(jsn[0]['user'],'followers_count') > 2500:
                continue
            scores[int(i)] = EmptyScore(scoring_dict)
            StaticUserScore(jsn, scores[int(i)])
            HashtagScoreUser(hashtags[int(i)], scoring_dict, scores[int(i)])
            SignalBoostUser(hashtags[int(i)], scoring_dict, scores[int(i)])
            ShardBoostUser(i, scoring_dict, scores[int(i)])
    return scores

def AllTweetsWithHashtag(tag):
    tweets = []
    with open('learning/save.targets','r') as f:
        for j,line in enumerate(f):
            if j % 1000 == 0:
                print j
            i,jsn = line.split(' ', 1)
            jsn = json.loads(jsn)
            if len(jsn) ==  0 or jsn[0]['user']['lang'][:2] != 'en':
                if len(jsn) == 0:
                    print "len 0"
                else:
                    print jsn[0]['user']['lang']
                continue
            for k in jsn:
                if 'hashtags' in k and tag in [t.lower() for t in k['hashtags']]:
                    print k["text"]
                    tweets.append(k)
    cPickle.dump(tweets,open("save.hashtags_" + tag,"wb"))


def LoadAllTweetsWithHashtag(tag):
    return cPickle.load(open("save.hashtags_" + tag,"rb"))

import pattern.en as pen

def PrintParsed(sentence):
    print sentence
    sens = pen.parsetree(sentence,lemmata=True,relations=True)
    for sen in sens:
        for chunk in sen.chunks:
            print chunk.type, [(w.string, w.type) for w in chunk.words]
    print '\n'
