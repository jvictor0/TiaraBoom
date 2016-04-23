import cmd
import time
import reply
import sys
import traceback
import generator

def Reload():
    generator.Reload()
    reply.Reload()
    if __name__ != "__main__":
        return reload(sys.modules[__name__])
    return sys.modules[__name__]

class Chat(cmd.Cmd):
    prompt = "me: "
        
    def preloop(self):
        print "Chat with the evidence bot!"

    def default(self, line):
        try:
            if line.strip() == "_reset" or line.strip() == "_reload":
                Reload()
                self.SetCtx(generator.OpenContext(sys.argv[1]))
                print line.strip()
            elif line.startswith("_fact ") and len(line.split()) > 1:
                for f in self.ctx.GetFactsByOriginalId(int(line.split()[1])):
                    f.PrintAllSimpleSentences(self.ctx)
            elif line.strip() == "_all_facts":
                self.ctx.PrintAllFacts()
            elif line.strip() == "_all_relations":
                self.ctx.PrintAllRelations()
            elif line.startswith("_relation "):
                self.ctx.PrintAllRelations(involving=int(line.split()[1]))
            elif line.strip() == "_debug":
                self.ctx.debug = not self.ctx.debug
                print "debug mode =", self.ctx.debug
            elif line.strip() == "_converse":
                for i in xrange(10):
                    self.convo.Append(reply.InterlocutorMessage("why"))
                    if i > 0:
                        print "me: why"
                    self.convo.Append(self.convo.FormReply())                    
                    print "bot:", self.convo[-1]                    
            elif line.strip().startswith("_"):
                print "unknown command"
            else:
                self.convo.Append(reply.InterlocutorMessage(line))
                self.convo.Append(self.convo.FormReply())
                print "bot:", self.convo[-1]
        except Exception as e:
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)
            print e
        return False

    def do_EOF(self, line):
        return True

    def do_quit(self, line):
        return True

    def emptyline(self):
        return False
    
    def postloop(self):
        print "good bye"

    def SetCtx(self, ctx):
        self.ctx = ctx
        self.convo = reply.Conversation(ctx)

if __name__ == "__main__":
    chat = Chat()
    chat.SetCtx(generator.OpenContext(sys.argv[1]))
    chat.cmdloop()
