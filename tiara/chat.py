import cmd
import time

class Chat(cmd.Cmd):
    prompt = "tiaraboom> "

    def response(self,x):
        return "hi " + x, {}

    def preloop(self):
        print "hi"

    def default(self, line):
        t0 = time.time()
        r,d = self.response(line)
        self.last_dict = d
        print "(%f secs)" % (time.time() - t0)
        print r
        return False

    def do_EOF(self, line):
        return True

    def do_quit(self, line):
        return True

    def emptyline(self):
        return False
    
    def postloop(self):
        print "good bye"

c = Chat()
c.cmdloop()
