import random
import syntax_rewriter

def Reload():
    reload(syntax_rewriter)
    syntax_rewriter.Reload()

class Message:
    def Facts(self):
        return []

    def Text(self, ctx):
        return ""

class InterlocutorMessage(Message):
    def __init__(self, text):
        self.text = text

    def Text(self, ctx):
        return self.text

    def SentByMe(self):
        return False

class EvidenceMessage(Message):
    def __init__(self, snode, facts):
        self.snode = snode
        self.facts = facts

    def Text(self, ctx):
        return syntax_rewriter.RewriteSyntax(ctx, self.snode).ToText()

    def Facts(self):
        return self.facts

    def SentByMe(self):
        return True
            
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
        replied = " ".join([m.Text(self.ctx) for m in self.messages if not m.SentByMe()]).lower()        
        for t, e in self.ctx.EntityTags().iteritems():
            if t in replied:
                return self.RandomFact(entityName=e)
        return self.RandomFact()
        
    def RandomFact(self, entityName=None):
        unusedFacts = [f for f in self.ctx.FactIds() if f not in self.UsedFacts()]
        relevantFacts = [f for f in self.ctx.FactIds() if entityName is None or self.ctx.GetFact(f).ReferencesEntity(entityName)]
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
        return EvidenceMessage(self.ctx.GetFact(f).Mtr(self.ctx), [f])

    def __getitem__(self, i):
        return self.messages[i].Text(self.ctx)
        
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
            return self.RandomFact()

    def UsedFacts(self):
        return [f for m in self.messages for f in m.Facts()]
    
    def Justify(self, factId):
        rels = self.ctx.Justifications(factId)
        random.shuffle(rels)
        for r in rels:
            if not all([f in self.UsedFacts() for f in r.FactIds()]):                
                snode = r.Mtr(self.ctx)
                return EvidenceMessage(snode, r.FactIds())
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
        
