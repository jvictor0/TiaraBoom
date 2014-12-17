import socket
import os
import json
import time

class Client():
    def __init__(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../client")
        with open(abs_prefix + '/config.json','r') as f:
            conf = json.load(f)
            self.port = conf["port"]
            self.host = conf["host"]
            print (self.host,self.port)
            self.password = conf["password"]
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self.sock.send(self.password)
        assert self.sock.recv(1024) == "welcome"

    def Send(self, msg):
        self.sock.send(msg)
        if msg == "quit":
            self.Close()
            return False
        data = self.sock.recv(1024)
        print data
        return True

    def Prompt(self):
        return self.Send(raw_input("boom> "))

    def Close(self):
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
    while True:
        if not c.Prompt():
            break
    print "good bye"
