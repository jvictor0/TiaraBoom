import random
try:
    import nltk.data
except Exception as e:
    print "cannot import nltk"
import copy
import client
try:
    import corenlp
except Exception as e:
    print "cannot import corenlp"
import time
from unidecode import unidecode
import database
import rewrite_rules as rr
import depend_tree as deptree

class SentenceBuilderErr:
    def __init__(self, err):
        self.err = err
        
    def __str__(self):
        return "SentenceBuilderErr(%s)" % self.err

class ExpansionNode:
    def __init__(self, word, arctype, sid, did, height, fixed_sib):
        self.word = word
        self.arctype = arctype
        self.sid = sid
        self.did = did
        self.height = height
        self.fixed_siblings = fixed_sib

    def __str__(self):
        return "ExpansionNode(word = %s, arctype = %s, sid = %s, did = %s, height = %s, fixed_sibling = %s)" % (self.word, self.arctype, self.sid, self.did, self.height, self.fixed_siblings)

HEIGHT_THROTTLER = 1.0
ARC_WILDNESS = {
    "amod" : 0.5,
#    "num" : 0.5,
    "iobj" : 0.5,
    "dobj" : 0.5,
#    "vmod" : 0.5,
#    "rcmod" : 0.2,
#    "pobj" : 0.5,
#    "quantmod" : 0.5,
    "nsubj" : 0.5,
#    "nsubjpass" : 0.5,
#    "csubj" : 0.25,
#    "number" : 0.5
    }
DEFAULT_PARAMS = {
    "height_throttler" : HEIGHT_THROTTLER,
    "arc_wildness" : ARC_WILDNESS
    }


NLP = None
def InitNLP():
    global NLP
    if NLP is None:
        NLP = client.StanfordNLP()

def Print(x):
    print x
    
def Test(sentence, verbose=False, transforms=[], exempt=[]):
    print sentence
    global NLP
    InitNLP()
    dt = deptree.ToDependTree(NLP.parse(sentence)["sentences"][0]["dependencies"],"ROOT-0")
    print dt
    result = deptree.FromDependTree(copy.deepcopy(dt),verbose=verbose,printres=True)
    assert result == sentence.strip(".").strip("!"), "\n%s\n%s" % (result,sentence)
    for arc,tg in transforms:
        if arc in exempt:
            continue
        dtcopy = copy.deepcopy(dt)
        if dtcopy.Transform(arc,tg):            
            result = deptree.FromDependTree(dtcopy,verbose=verbose,printres=False)
            Test(result, verbose=verbose)
    print

def Reset(con, user):
    con.query("drop table %s_dependencies" % user)
    con.query("drop table %s_sentences" % user)
    con.query("drop table %s_procd" % user)
    DDL(con,user)

def DDL(con, user):
    con.query("use tiaraboom")
    con.query(("create table if not exists %s_dependencies"
               "(sentence_id bigint not null"
               ",arctype varbinary(255) not null"
               ",governor varbinary(255) not null"
               ",dependant varbinary(255) not null"
               ",governor_id int not null"
               ",dependant_id int not null"
               ",primary key(sentence_id,dependant_id)"
               ")") % user)
    con.query(("create table if not exists %s_procd"
               "(sentence_id bigint not null"
               ",arctype varbinary(255) not null"
               ",governor varbinary(255) not null"
               ",dependant varbinary(255) not null"
               ",governor_id int not null"
               ",dependant_id int not null"
               ",primary key(sentence_id,dependant_id)"
               ",shard(sentence_id)"
               ",key(arctype, governor, dependant)" 
               ")") % user)
    con.query(("create table if not exists %s_sentences"
               "(id bigint primary key auto_increment"
               ",sentence blob"
               ",source blob default null)") % user)

def UpdateProcd(con, user):
    con.query("drop table %s_procd" % user)
    DDL(con, user)
    ids = [int(r["id"]) for r in con.query("select id from %s_sentences" % user)]
    for i in xrange(len(ids)):
        if i % 100 == 0:
            print "%f%% done" % (100*float(i)/len(ids))
        ix = ids[i]
        PostProcessSentence(con, ix, user)

def PostProcessSentence(con, i, user):
    procd = deptree.FlattenDependTree(deptree.PreProcessDependTree(SentenceIdDependTree(user,i, con)))
    if len(procd) == 0:
        return
    q = "insert into %s_procd values" % user
    params = []
    for p in procd:
        q += "(%d, '%s', %%s, %%s, %d, %d)," % (i, p[0], p[2], p[4])
        params.append(p[1])
        params.append(p[3])
    q = q.strip(",")
    try:
        con.query(q, *params)
    except Exception as e:
        print q
        print params
        print i
        raise e
    
def InsertSentence(con, user, sentence):
    # if you SQL inject me I'll urinate on you
    sentence = sentence.encode("utf8")
    global NLP
    print sentence
    if NLP is None:
        InitNLP()
    nlp_parsed = NLP.parse(sentence.decode("utf8").encode("ascii","ignore"))
    depsa = nlp_parsed["sentences"]
    ProcessDependencies(con, user, depsa)
def ProcessDependencies(con, user, depsa, source=None, log=Print):
    for deps in depsa:
        txt = deps["text"].encode("utf8")
        try:
            if source is None:
                sid = str(con.execute("insert into %s_sentences(sentence) values(%%s)" % (user), txt))
            else:
                sid = str(con.execute("insert into %s_sentences(sentence,source) values(%%s,%%s)" % (user), txt, unidecode(source)))
        except Exception as e:
            log("insert sentence error " + str(e))
            continue
        deps = deps["dependencies"]
        failed = False
        for at, gv, dp in deps:
            values = [sid, "'%s'" % at, "%s",  "%s", deptree.remove_word(gv), deptree.remove_word(dp)]
            q = "insert into %s_dependencies values (%s)" % (user,",".join(values))
            try:
                con.query(q.encode("utf8"),
                          deptree.remove_id(gv).lower().encode("utf8"),
                          deptree.remove_id(dp).lower().encode("utf8"))
            except Exception as e:
                log("insert dep error " + str(e))
                log("%s %s %s" % (q.encode("utf8"),
                                  deptree.remove_id(gv).lower().encode("utf8"),
                                  deptree.remove_id(dp).lower().encode("utf8")))
                con.query("delete from %s_sentences where id = %s" % (user,sid))
                con.query("delete from %s_dependencies where sentence_id = %s" % (user,sid))
                failed = True
                break
        if not failed: 
            PostProcessSentence(con, int(sid), user)

def Ingest(con, text, user):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    texts = tokenizer.tokenize(text.decode("utf8"))
    for sentence in texts:
        InsertSentence(con, user, sentence)

def IngestFile(con, filename, user, log=Print):
    result = corenlp.ParseAndSaveFile(filename)
    log("begin xact")
    con.query("begin")
    try:        
        ProcessDependencies(con, user, result["sentences"], filename, log=log)
        log("commit xact")
        con.query("commit")
    except Exception:
        con.query("rollback")
        raise

def RandomWeightedChoice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c,w  in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, ("RandomWeightedChoice",choices)

def Subset(superset,subset):
    for elem in set(subset):
        if superset.count(elem) < subset.count(elem):
            return False
    return True

# this function find a all sentences containing a given word under a given arctype
# for each fixed sibling, the toplevel arctype will be present.
# the return type is [([(arctype, word)], sentence_id, dependant_id)]
# 
def HistogramSubsets(con, node, user):
    word = node.word
    parent_arctype = node.arctype
    fixed_siblings = node.fixed_siblings
    subs =  ("select dl.sentence_id as sid, dl.dependant_id as did, "
             "group_concat(dr.arctype separator '___')   as gc_arc, "
             "group_concat(dr.dependant separator '___') as gc_dep, "
             "count(dr.dependant) as groupsize "
             "from %s_procd dl left join %s_procd dr "
             "on dl.sentence_id = dr.sentence_id and dl.dependant_id = dr.governor_id "
             "where dl.dependant = %%s %s "
             "group by dl.sentence_id, dl.dependant_id ")
    extra_cond = ""
    params = [word]
    if not parent_arctype is None:
        extra_cond += ("and dl.arctype = '%s'" % parent_arctype)
    subs = subs % (user, user, extra_cond)
    q = subs
    t0 = time.time()    
    qres = con.query(q, *params)
    maxgroupsize = max([int(r["groupsize"]) for r in qres])
    if maxgroupsize == 0:
        qres = [qres[0]]
    t1 = time.time()
    hists = [( ([] if r["gc_arc"] is None else r["gc_arc"].split("___")),
               ([] if r["gc_dep"] is None else r["gc_dep"].split("___")),
               r["sid"],
               r["did"]) 
             for r in qres]
    disallowed = ["cc"]
    disallowed.extend(["num","number"]) # this will add some stability for now...
    if len(hists) == 0:
        raise SentenceBuilderErr("before filtering no rows")
    result = []
    assert fixed_siblings.data is None
    fixed_tups = [(fs[0], fs[1].data) for fs in fixed_siblings.children]
    t2 = time.time()
    for h in hists:
        assert len(h[0]) == len(h[1]), h
        if len([x for x in h[0] if x in disallowed]) == 0 and len([x for x in h[0] if x == "nsubj"]) < 2:
            zipd = zip(h[0],h[1])
            if Subset(zipd, fixed_tups):
                result.append((zipd, h[2], h[3]))
    return result

# returns [(arctype, word, fixed_arcs)]
def SubsetSelector(con, node, user, dbg_out, symbols):
    if 'facts' not in dbg_out:
        dbg_out['facts'] = []
    params = DEFAULT_PARAMS
    hist = HistogramSubsets(con, node=node, user=user)
    if len(hist) == 0:
        raise SentenceBuilderErr("generated no rows, word = %s, \nfixed=%s" % (node.word, str(node.fixed_siblings)))
    for i in xrange(len(hist)):
        denom = float(len(hist[i][0])) if node.height == 0 else (params["height_throttler"] * float(node.height))**len(hist[i][0])
        hist[i] = (hist[i], 0 if denom == 0 else (1.0/denom))
        for s,k in symbols.iteritems():
            if s in [hr[1] for hr in hist[i][0][0]]:                
                dbg_out['facts'].append("Bumped %s by %f" % (s,4+k))
                hist[i] = (hist[i][0], hist[i][1]*(4+k))
    result_entry = RandomWeightedChoice(hist)
    q = "select * from %s_procd where sentence_id = %s and governor_id = %s" % (user, result_entry[1], result_entry[2])
    result = [ExpansionNode(r["dependant"],
                            r["arctype"], 
                            r["sentence_id"],
                            r["dependant_id"],
                            node.height+1,
                            deptree.DependTree(None))
              for r in con.query(q)]
    assert sorted([(r.arctype,r.word) for r in result]) == sorted(result_entry[0]), "%s\n%s\n%s\n%s" % (result,result_entry)

    if "used_list" not in dbg_out:
        dbg_out["used_list"] = []
    if len(result) != 0:
        dbg_out["used_list"].append(int(result_entry[1]))

    fixed_ixs = set([])
    for at,fs in node.fixed_siblings.children:
        found = False
        for i in xrange(len(result)):
            if (result[i].arctype,result[i].dependant) == (at,fs.data):
                fixed_ixs.add(i)
                result[i].fixed_sibling = deptree.DependTree(None, fs.children)
                found = True
                break
        assert found, ("not found",at,fs.data,result)
        
    for i in xrange(len(result)):
        if result[i].arctype in params["arc_wildness"] and random.random() < params["arc_wildness"][result[i].arctype]:
            if i not in fixed_ixs:
                next_word = RandomDependant(con, user, node.word, result[i].arctype, symbols=symbols)
                dbg_out['facts'].append(result[i].word +"->"+next_word)
                result[i].word = next_word
        if result[i].word in symbols:
            del symbols[result[i].word]
    return result

def GetDependants(con, user, sentence_id, gov_id):
    q = "select arctype, dependant from %s_procd where governor_id = %%s and sentence_id = %%s" % user
    return [(a["arctype"], a["dependant"]) for a in con.query(q,gov_id, sentence_id)]


def RandomDependant(con, user, gov, arctype, symbols={}):
    q = "select dependant from %s_procd where governor = %%s and arctype = %%s" % user
    dependants = [d['dependant'] for d in con.query(q,gov,arctype)]
    for sym,rate in symbols.iteritems():
        if sym in dependants:
            dependants.append(sym)
            dependants.append(sym)
            for x in xrange(int(rate)):
                dependants.append(sym)
    return random.choice(dependants)
        
def Expand(con, node, user, dbg_out, symbols):
    arctypes = SubsetSelector(con, node, user=user, dbg_out = dbg_out, symbols=symbols)
    outs = []
    for nextnode in arctypes:
        outs.append((nextnode.arctype, Expand(con, node=nextnode, user=user, symbols=symbols, dbg_out=dbg_out)))
    return deptree.DependTree(node.word, outs, node.sid, node.did)

# SeekToRoot :: dependant -> fixed_tree
def SeekToRoot(con, user, dependant):
    result = []
    q = (("select governor, arctype from %s_procd "
          "where dependant = %%s"))
    q = q % user
    rows = con.query(q,dependant.encode("utf8"))
    if len(rows) == 0:
        return deptree.DependTree(None)
    row = random.choice(rows)
    result.append((row["arctype"],dependant))
    dependant = row['governor']
    while dependant != 'root':
        q = (("select sentence_id as sid, governor_id as gid from %s_procd "
              "where arctype = '%s' and governor = %%s and dependant = %%s"))
        q = q % (user, result[-1][0])
        rows = con.query(q, dependant, result[-1][1])
        assert len(rows) != 0
        row = random.choice(rows)
        rows = con.query("select governor, arctype from %s_procd where sentence_id = %s and dependant_id = %s" % (user, row["sid"], row["gid"]))
        assert len(rows) == 1, ("SeekToRoot",rows)
        result.append((rows[0]['arctype'], dependant))
        dependant = rows[0]['governor']
    result_tree = []
    for at, dep in result:
        result_tree = [(at, deptree.DependTree(dep, result_tree))]
    assert result_tree[0][0] == 'root', ("SeekToRoot",result_tree)
    return result_tree[0][1]

g_last_generated = None

def Generate(con, user, using=None, dbg_out={}, symbols={}):
    if not using is None:
        fixed_chain = SeekToRoot(con, user, using)
        if fixed_chain.data is None:
            return None
        word = fixed_chain.data
        fixed_chain.data = None
    else:
        fixed_chain = deptree.DependTree(None)
        word = random.choice(con.query("select dependant from %s_procd where arctype = 'root'" % user))['dependant']
    global g_last_generated
    node = ExpansionNode(word, 'root', -1, -1, 0, fixed_chain)
    result = Expand(con, node=node, user=user, dbg_out=dbg_out, symbols=symbols)
    g_last_generated = copy.deepcopy(result)
    return result

def GenerateAndExpand(user, using=None):
    con = database.ConnectToMySQL()
    con.query("use tiaraboom")
    dbg_out = { "used_list" : [] }
    result = deptree.FromDependTree(Generate(con, user, using=using,dbg_out=dbg_out))
    print "sentences_used" , dbg_out["used_list"]
    print "facts" , dbg_out["facts"]
    print g_last_generated
    return result

def GenerateWithSymbols(con, user, symbols, requireSymbols=False):
    symbols = { k.encode("utf8") : v for k,v in symbols.iteritems() }
    while len(symbols) != 0:
        using = RandomWeightedChoice(symbols.items())
        del symbols[using]
        dbg_out = { "used_list" : [] }
        result = Generate(con, user, using, symbols=copy.copy(symbols), dbg_out=dbg_out)
        print dbg_out["facts"]
        if not result is None:
            return result, using
    if requireSymbols:
        raise Exception("cannot build sentence with provided symbols")
    result = Generate(con, user, None)
    return result, None
    
def SentenceIdDependTree(user,sid, con):
    rows = con.query("select arctype, governor, dependant, governor_id, dependant_id from %s_dependencies where sentence_id = %d" % (user,sid))
    deps = [(r["arctype"], r['governor'] + "-" + r['governor_id'], r['dependant'] + "-" + r['dependant_id']) for r in rows]
    return deptree.ToDependTree(deps, root='root-0')


def PrintSentences(user,sids):
    for s in sids:
        PrintSentence(user,s)


def PrintSentence(user,sid):
    con = database.ConnectToMySQL()
    con.query("use tiaraboom")
    print con.query("select * from %s_sentences where id = %d" % (user,sid))[0]['sentence']
    print SentenceIdDependTree(user,sid, con)

def GetImportantWords(parsetree, nlp):
    root = parsetree.Child(parsetree.Find("root"))
    result = { root.data : 1 }
    nsubj = root.FindNoCheck("nsubj")
    if not nsubj is None:
        if not root.ChildStr(nsubj) in result:
            result[root.ChildStr(nsubj)] = 0
        result[root.ChildStr(nsubj)]+= 3
    dobj = root.FindNoCheck("dobj")
    if not dobj is None:
        if not root.ChildStr(dobj) in result:
            result[root.ChildStr(dobj)] = 0
        result[root.ChildStr(dobj)]+= 3
    for w,mw in nlp["words"]:
        if mw["NamedEntityTag"] != 'O':
            if not w in result:
                result[w] = 0
            result[w]+= 10
    return result
            

if __name__ == "__main__":
    TestAll()
