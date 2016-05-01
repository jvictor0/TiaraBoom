import evidence_ddl
import reply
import simplejson
import sys
import generator

def Reload():
    reply.Reload()
    generator.Reload()
    reload(evidence_ddl)
    return reload(sys.modules[__name__])

class EvidenceDataMgr:
    def __init__(self, con, dbmgr, ctx=None, infile=None):
        if ctx is None:
            ctx = generator.OpenContext(infile)
        self.ctx = ctx
        self.con = con
        self.dbmgr = dbmgr
        evidence_ddl.EvidenceCreateTables(con)
    
    def GetConversation(self, cid):
        convo = reply.Conversation(self.ctx)
        q = ("select bt.user_id as user_id, bt.body as body, et.facts as facts "
             "from bot_tweets bt left join evidence_tweets et "
             "on bt.user_id = et.user_id and bt.id = et.id "
             "where bt.conversation_id = %d "
             "order by bt.id") % cid
        for m in self.con.query(q):
            if int(m["user_id"]) == self.dbmgr.GetUserId():
                if m["facts"] is not None:                
                    facts = simplejson.loads(m["facts"])
                else:
                    facts = []
                convo.Append(reply.EvidenceMessage(facts=facts, text=m["body"]))
            else:
                convo.Append(reply.InterlocutorMessage(m["body"]))
        return convo

    def InsertMsg(self, tweet, msg):
        q = "insert into evidence_tweets (user_id, id, facts) values (%d,%d,%s)" % (tweet.GetUser().GetId(), tweet.GetId(), msg.Facts())
        self.con.query(q)

    def FormConversationFromTweet(self, tweet):
        # there are two cases.  Either this is part of an ongoing conversation or not.
        # if it is, form the conversation and get started, otherwise just get started
        q = "select conversation_id from bot_tweets where user_id = %d and id = %d" % (tweet.GetUser().GetId(), tweet.GetId())
        cid = self.con.query(q)
        if len(cid) == 0:
            convo = reply.Conversation(self.ctx)
            convo.Append(reply.InterlocutorMessage(tweet.GetText()))
            return convo
        else:
            assert len(cid) == 1, cid
            return self.GetConversation(cid[0]['conversation_id'])
            
    def Reply(self, tweet):
        convo = self.FormConversationFromTweet(tweet)
        convo.FormReply()
        convo[-1].text = "@" + tweet.GetUser().GetScreenName() + " " + convo[-1].text
        return convo[-1]
