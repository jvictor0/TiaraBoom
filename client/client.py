import socket
import os
import json
import time
import sys
import select
import cmd
import hashlib

class Client(cmd.Cmd):
    def preloop(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../client")
        cfig = "config.json" 
        with open(abs_prefix + '/' + cfig,'r') as f:
            conf = json.load(f)
            self.port = conf["port"]
            self.host = conf["host"]
            print (self.host,self.port)
            self.password = conf["bots"][sys.argv[1]]
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self.sock.send(sys.argv[1])
        pad = self.sock.recv(1024)
        h = hashlib.sha256(pad)
        h.update(self.password)
        passwrd = h.hexdigest()
        self.sock.send(passwrd)
        assert self.sock.recv(1024) == "welcome"
        print "connected"

    def Send(self, msg):
        self.sock.send(msg)
        if msg in ["quit","_kill","_upgrade"]:
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
        return not self.Send(line)

    def do_help(self, line):
        self.default("help " + line)

    def do_EOF(self, line):
        return True

    def do_quit(self, line):
        self.Send("quit")
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
