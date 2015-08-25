import global_data as g
from util import *
import sys
import time
import select
import socket
import Queue
import os
from input_handler import HandleUserInput
import random
import hashlib
import json
import artrat_utils as au
import threading
import atexit, signal

class Connection:
    def __init__(self, g_data):
        self.auth = False
        self.queue = Queue.Queue()
        self.g_data = g_data
        self.attached = False


def GDatas():
    abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
    with open(abs_prefix + '/config.json','r') as f:
        conf = json.load(f)
        host           = conf['host'] if 'host' in conf else 'localhost'
        port           = conf['port'] if 'port' in conf else 10001
        g_datas        = []
        for i in xrange(len(conf["bots"])):
            g_datas.append(g.GlobalData(g_data = None if len(g_datas) == 0 else g_datas[0], conf=conf["bots"][i]))
            g_datas[-1].TraceInfo("Initialized!")
        for i in xrange(len(conf["bots"])):
            if g_datas[i].invalid:
                g_datas[-1].TraceWarn("g_data INVALID!")
                assert False
        assert len(g_datas) != 0
    return g_datas

if __name__ == '__main__':

    abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
    with open(abs_prefix + '/config.json','r') as f:
        conf = json.load(f)
        host = conf['host'] if 'host' in conf else 'localhost'
        port = conf['port'] if 'port' in conf else 10001


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    
    g_datas = GDatas()

    sys.excepthook = exceptionTrace

    refreshProcess = threading.Thread(target = au.ArticleInsertionThread,
                                      args=(g_datas[0].TraceArticleThread,))
    refreshProcess.setDaemon(True)
    refreshProcess.start()
                
    server_address = (host, port)
    server.bind(server_address)
    server.listen(5)
    
    g_datas[0].TraceInfo("Starting up Tiara Boom Server on %s, port %s!" % server_address)

    inputs = [server]
    outputs = []

    cons = {}

    while inputs:

        for g_data in g_datas:
            g_data.SocialLogic().Act()
        assert refreshProcess.is_alive()
        
        ############# Begin server stuff ##################
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 60)
        for s in readable:
            if s in exceptional:
                continue
            if s is server:
                connection, client_address = s.accept()
                g_datas[0].TraceInfo('new connection from %s:%s' %  client_address)
                connection.setblocking(0)
                inputs.append(connection)
                cons[connection] = Connection(g_datas[0])
            else:
                data = s.recv(1024)
                data = data.strip()
                if data and not data in ["quit","_upgrade","_kill"]:
                    if cons[s].auth:
                        cons[s].g_data.TraceInfo('received "%s" from %s' % (data, s.getpeername()))
                        cons[s].queue.put(HandleUserInput(cons[s].g_data, data))
                    elif not cons[s].attached: # we haven't yet decided who to assign you to
                        if data in [g_data.myName for g_data in g_datas]:
                            this_bot = [g_data for g_data in g_datas if data == g_data.myName][0]
                            this_bot.TraceDebug("received hi message")
                            cons[s].attached = True
                            cons[s].g_data = this_bot
                            cons[s].pad = random.randrange(0,2**32)
                            cons[s].queue.put(str(cons[s].pad))
                    else: # you're assigned a bot but not authorized
                        h = hashlib.sha256(str(cons[s].pad))
                        h.update(cons[s].g_data.password)
                        if data == h.hexdigest():
                            cons[s].auth = True
                            cons[s].queue.put("welcome")
                            cons[s].g_data.TraceInfo('%s:%s entered the password' % s.getpeername())
                        else:
                            cons[s].queue.put("password denied")
                            cons[s].g_data.TraceInfo('%s:%s failed the password' % s.getpeername())
                    if s not in outputs:
                        outputs.append(s)
                elif not data or data == "quit" or not cons[s].auth:
                    try:
                        cons[s].g_data.TraceInfo('closing %s:%s' % s.getpeername())
                    except Exception as e:
                        cons[s].g_data.TraceInfo("closing, cant get peer name")
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()                        
                    del cons[s]
                elif data == "_upgrade":
                    s.close()
                    server.close()
                    os.system("git pull --rebase origin master")
                    os.execl(sys.executable, sys.executable, * sys.argv)
                else:
                    assert data == "_kill"
                    s.close()
                    server.close()
                    cons[s].g_data.TraceInfo("Recieved _kill, going down NOW")
                    assert False
        for s in writable:
            if s in exceptional:
                continue
            try:
                next_msg = cons[s].queue.get_nowait()
            except Exception as e:
                if s in outputs:
                    outputs.remove(s)
            else:
                cons[s].g_data.TraceInfo('sending "%s" to %s' % (next_msg[:min(50,len(next_msg))], s.getpeername()))
                s.send(next_msg)
        for s in exceptional:
            try:
                cons[s].g_data.TraceInfo('closing %s:%s' % s.getpeername())
            except Exception as e:
                pass
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del cons[s]
                

