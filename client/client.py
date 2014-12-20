import socket
import os
import json
import time
import sys
import select
import cmd

class Client(cmd.Cmd):
    def preloop(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../client")
        cfig = "config.json" if len(sys.argv) == 1 else sys.argv[1]
        with open(abs_prefix + '/' + cfig,'r') as f:
            conf = json.load(f)
            self.port = conf["port"]
            self.host = conf["host"]
            print (self.host,self.port)
            self.password = conf["password"]
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self.sock.send(self.password)
        assert self.sock.recv(1024) == "welcome"
        print "connected"

    def Send(self, msg):
        self.sock.send(msg)
        if msg == "quit":
            self.Close()
            return False
        data = self.sock.recv(4096)
        while True:
            read_sockets, write_sockets, error_sockets = select.select([self.sock], [], [], 1)
            for s in read_sockets:
                assert s == self.sock
                data = data + self.sock.recv(4096)
            if read_sockets == []:
                break
        print data
        return True

    prompt = "boom> "

    def default(self, line):
        self.Send(line)
        if line == "_upgrade":
            return True

    def do_help(self, line):
        self.default("help " + line)

    def do_EOF(self, line):
        return True

    def do_quit(self, line):
        return True

    def emptyline(self):
        return False
    
    def postloop(self):
        print "good bye"
        self.sock.close()

if __name__ == "__main__":
    c = Client()
    print "You are now connected to a TiaraBoom server."
    print "This server enforces NO RATE LIMITS!!!"
    print "Please respect that Tiara does not wish to respond to more than a few requests per hour!"
    print "If you receive an error other than a syntax error, or the server does not respond, please DO NOT TRY AGAIN"
    print "Instead, contact support at 513-284-5321"
    print "Enter a command, or try \"help\""
    print "to exit, type quit"
    c.cmdloop()