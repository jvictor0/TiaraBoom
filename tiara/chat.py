import cmd
import time

class Chat(cmd.Cmd):
    prompt = "tiaraboom> "

    def preloop(self):
        print "hi"

    def default(self, line):
        t0 = time.time()
        r = self.response(line)
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
