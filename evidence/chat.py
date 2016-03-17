import cmd
import time
import reply
import sys
import generator

def Reload():
    reload(generator)
    generator.Reload()
    reload(reply)
    reply.Reload()

class Chat(cmd.Cmd):
    prompt = "me: "
        
    def preloop(self):
        print "Chat with the evidence bot!"

    def default(self, line):
        if line.strip() == "_reset":
            Reload()
            self.SetCtx(generator.OpenContext(sys.argv[1]))
            print "_reset"
        elif line.startswith("_fact ") and len(line.split()) > 1:            
            self.ctx.GetFact(int(line.split()[1])).PrintAllSimpleSentences(self.ctx)
        elif line.strip() == "_all_facts":
            self.ctx.PrintAllFacts()
        elif line.strip() == "_all_rels":
            self.ctx.PrintAllRelations()
        elif line.strip() == "_debug":
            self.ctx.debug = not self.ctx.debug
            print "debug mode =", self.ctx.debug
        else:
            self.convo.Append(reply.InterlocutorMessage(line))
            self.convo.Append(self.convo.FormReply())
            print "bot:", self.convo[-1]
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
