import random
import syntax_rewriter
import sys

def Reload():
    syntax_rewriter.Reload()
    return reload(sys.modules[__name__])

class Message:
    def Facts(self):
        return []

    def Text(self):
        return ""

class InterlocutorMessage(Message):
    def __init__(self, text):
        self.text = text

    def Text(self):
        return self.text

    def SentByMe(self):
        return False

class EvidenceMessage(Message):
    def __init__(self, facts=[], ctx=None, snode=None, text=None):
        if text is None:
            assert ctx is not None
            assert snode is not None
            self.text = syntax_rewriter.RewriteSyntax(ctx, snode).ToText()
        else:
            self.text = text
        self.facts = facts

    def Text(self):
        return self.text

    def Facts(self):
        return self.facts

    def SentByMe(self):
        return True

    def Prepend(self, prefix):
        self.text = prefix + self.text
            
class Conversation:
    def __init__(self, ctx):
        self.ctx = ctx
        self.messages = []

    def PrtDbg(self, msg):
        if self.ctx.debug:
            print "[REPLY]", msg

    def Append(self, msg):
        self.messages.append(msg)

    def StartConversation(self):
        replied = " ".join([m.Text() for m in self.messages if not m.SentByMe()]).lower()        
        for t, e in self.ctx.EntityTags().iteritems():
            if t in replied:
                return self.RandomFactMsg(entityName=e)
        return self.RandomFactMsg()
        
    def RandomFactMsg(self, entityName=None):
        unusedFacts = [(fi,fo) for fi,fo in self.ctx.FactIds() if fo not in self.UsedFacts()]
        relevantFacts = [(fi,fo) for fi,fo in self.ctx.FactIds() if entityName is None or self.ctx.GetFact(fi).ReferencesEntity(entityName)]
        intersect = list(set(unusedFacts) & set(relevantFacts))
        if len(intersect) == 0:
            if len(relevantFacts) == 0 and len(unusedFacts) == 0:                
                f = random.choice(self.ctx.FactIds())
            elif len(relevantFacts) == 0:
                f = random.choice(unusedFacts)
            else:
                f = random.choice(relevantFacts)
        else:
            f = random.choice(intersect)
        return EvidenceMessage(snode=self.ctx.GetFact(f[0]).Mtr(self.ctx), ctx=self.ctx, facts=[f[1]])

    def __getitem__(self, i):
        return self.messages[i].Text()
        
    def FormReply(self):
        assert len(self.messages) > 0, "no messages to reply to"
        assert not self.messages[-1].SentByMe(), "cannot reply to myself"
        myMsgs = [m for m in self.messages if m.SentByMe()]
        if len(myMsgs) == 0:
            self.PrtDbg("no myMsgs")
            return self.StartConversation()
        else:
            for f in self.IterateFacts(2):
                j = self.Justify(f)
                if j is not None:
                    return j
            return self.RandomFactMsg()

    def UsedFacts(self):
        return [f for m in self.messages for f in m.Facts()]
    
    def Justify(self, factId):
        rels = self.ctx.Justifications(factId)
        random.shuffle(rels)
        for r in rels:
            if not all([f in self.UsedFacts() for _,f in r.FactIds(self.ctx)]):                
                snode = r.Mtr(self.ctx)
                return EvidenceMessage(snode=snode, facts=[f for _,f in r.FactIds(self.ctx)], ctx=self.ctx)
        self.PrtDbg("no justification for %d" % factId)
        return None

    # iterates over facts order by times_used, time desc
    #
    def IterateFacts(self, max_use):
        myFacts = [m.Facts() for m in self.messages if m.SentByMe()]
        for f in myFacts:
            random.shuffle(f)
        flatFacts = [f for m in myFacts for f in m]
        for i in xrange(max_use):
            for fs in myFacts[-1::-1]:
                for f in fs:
                    if len([f2 for f2 in flatFacts if f2 == f]) == i + 1:
                        yield f
        
