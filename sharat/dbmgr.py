
import tiara.database as database
import os.path
import simplejson
import sharat_ddl
import requests
import nlpclasses
import sys
import traceback
import converters as cvts

class SharatDbMgr:
    def __init__(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/config.json','r') as f:
            dbhost = simplejson.load(f)["dbHost"]
            self.con = database.ConnectToMySQL(dbhost)
            sharat_ddl.DoDDL(self.con)
        self.xact = False
    
    def NLP(self, q):
        properties = {}
        host = "http://localhost:9001/?properties=%s" % simplejson.dumps(properties)
        r = requests.post(host, data=q)
        if r.status_code == 200:
            return nlpclasses.Parse(simplejson.loads(r.content))
        else:
            r.raise_for_status()

    def NLPFile(self, filename):
        with open(filename,"rb") as f: #uhh, ok
            return self.NLP(f.read())

    def Ingest(self, text, user_id=-1, source=None):
        return self.InsertParse(user_id, source, self.NLP(text))
        
    def Insert(self, table, dct):
        return self.MultiInsert(table, [dct])
    
    def MultiInsert(self, table, dcts):
        if len(dcts) == 0:
            return
        q = "insert into %s (%s) values %s"
        keys = dcts[0].keys()
        cols = ",".join(keys)
        values = []
        tups = []
        for dct in dcts:
            tup = []
            assert len(dct.keys()) == len(keys)
            for k in keys:
                if dct[k] is None:
                    tup.append("null")
                else:
                    values.append(str(dct[k]))
                    tup.append("%s")
            tups.append("(%s)" % ",".join(tup))
        q = q % (table, cols, ",".join(tups))
        return self.con.execute(q, *values)

    def Begin(self):
        assert not self.xact
        self.con.query("begin")
        self.xact = True

    def Commit(self):
        assert self.xact
        self.con.query("commit")
        self.xact = False

    def Rollback(self):
        assert self.xact
        self.con.query("rollback")
        self.xact = False

    def InsertParse(self, user_id, source, parse):
        self.Begin()
        try:
            source_id = self.Insert("sources", {"user_id" : user_id, "source"  : source}) 
            for i in xrange(parse.SentenceLen()):
                s = parse.Sentence(i)
                sentence_id = self.Insert("sentences", cvts.Sentence2Row(source_id, s))
                tokens = []
                relations = []
                for tk in s.Tokens():
                    tokens.append(cvts.Token2Row(source_id, sentence_id, tk))
                for i,r in enumerate(s.Relations()):
                    relations.append(cvts.Relation2Row(source_id, sentence_id, i, r))
                self.MultiInsert("tokens", tokens)            
                self.MultiInsert("relations", relations)
            self.Commit()
            return source_id
        except Exception as e:
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)
            self.Rollback()
            raise e        

    def GetSentence(self, source_id, sentence_id):
        sentence_rows = self.con.query("select * from sentences where sentence_id = %d and source_id = %d" % (sentence_id, source_id))
        if len(sentence_rows) == 0:
            return None
        assert len(sentence_rows) == 1
        tokens_rows = self.con.query("select * from tokens where sentence_id = %d and source_id = %d" % (sentence_id, source_id))
        relations_rows = self.con.query("select * from relations where sentence_id = %d and source_id = %d" % (sentence_id, source_id))
        return cvts.Rows2Sentence(sentence_rows[0], relations_rows, tokens_rows)
        
    def GetSource(self, source_id):
        sentence_rows = self.con.query("select * from sentences where source_id = %d" % (source_id))
        if len(sentence_rows) == 0:
            return None
        tokens_rows = self.con.query("select * from tokens where source_id = %d" % (source_id))
        relations_rows = self.con.query("select * from relations where source_id = %d" % (source_id))
        return cvts.Rows2Parse([], sentence_rows[0], relations_rows, tokens_rows)
        
