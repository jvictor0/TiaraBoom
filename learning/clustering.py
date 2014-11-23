import json
import string
import collections
from scipy.spatial.distance import cosine
import math

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
        result = [t.split(' ')[1:].strip() for t in f]
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

def HashtagScoreUser(hashtags, scoreing_dict, score):
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
        if sd['_shard'] == user_id % sd['_mod']:
            score[k] += sd['_shard_boost']

def NormalPDF(mu=, sigma, x):
    return norm.pdf((float(x) - mu)/sigma)

def StaticUserScore(jsons, score):
    points_for_more_tweets = 2.5
    points_for_friends = 2.5
    points_for_followers = 2.5
    for k in score.keys():
        score[k] += points_for_more_tweets * HashtagPoints(float(len(jsons))/5)
        score[k] += NormalPDF(800, 250, float(jsons[0]['user']['followers_count'])) * points_for_followers
        score[k] += NormalPDF(800, 250, float(jsons[0]['user']['friends_count'])) * points_for_friends

def MakeScoringDict():
    

def ScoreUsers():
    scores = {}
    with open('save.targets','r') as f:
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
            scores[int(i)] = EmptyScore(scoring_dict):
            StaticUserScore(jsn, scores[int(i)])
            HashtagScoreUser(hashtags[int(i)], scoreing_dict, scores[int(i)])
            SignalBoostUser(hashtags[int(i)], scoring_dict, scores[int(i)])
            ShardBoostUser(i, scoring_dict, scores[int(i)])
    return scores


                
if __name__ == '__main__':
    pass
