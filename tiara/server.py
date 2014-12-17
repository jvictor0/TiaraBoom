import global_data as g
from util import *
import sys
import time
import select
import socket
import Queue
import os
from input_handler import HandleUserInput


if __name__ == '__main__':

    g_data = g.GlobalData()
    if g_data.read_only_mode:
        g_data.TraceInfo("In Read Only Mode!")

    sys.excepthook = exceptionTrace

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server_address = (g_data.host, g_data.port)
    server.bind(server_address)
    server.listen(5)
    
    g_data.TraceInfo("Starting up Tiara Boom Server on %s, port %s!" % server_address)

    inputs = [server]
    outputs = []

    message_queues = {}

    server_password = g_data.password
    abs_prefix = os.path.join(os.path.dirname(__file__), "../data")

    assert server_password != ""

    while inputs:

        g_data.SocialLogic().Act()
        
        ############# Begin server stuff ##################
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 60)
        for s in readable:
            if s in exceptional:
                continue
            if s is server:
                connection, client_address = s.accept()
                g_data.TraceInfo('new connection from %s:%s' %  client_address)
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = (Queue.Queue(),False)
            else:
                data = s.recv(1024)
                data = data.strip()
                if data and data != "quit":
                    g_data.TraceInfo('received "%s" from %s' % (data, s.getpeername()))
                    if message_queues[s][1]:
                        message_queues[s][0].put(HandleUserInput(g_data, data))
                    else:
                        if data == server_password:
                            message_queues[s] = (message_queues[s][0],True)
                            message_queues[s][0].put("welcome")
                            g_data.TraceInfo('%s:%s entered the password' % s.getpeername())
                        else:
                            message_queues[s][0].put("password denied")
                            g_data.TraceInfo('%s:%s failed the password' % s.getpeername())
                    if s not in outputs:
                        outputs.append(s)
                else:
                    g_data.TraceInfo('closing %s:%s' % s.getpeername())
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()                        
                    del message_queues[s]
        for s in writable:
            if s in exceptional:
                continue
            try:
                next_msg = message_queues[s][0].get_nowait()
            except Exception as e:
                g_data.TraceWarn("error getting message from queue %s" % str(e))
                if s in outputs:
                    outputs.remove(s)
            else:
                g_data.TraceInfo('sending "%s" to %s' % (next_msg, s.getpeername()))
                s.send(next_msg)
        for s in exceptional:
            g_data.TraceInfo('closing %s:%s' % s.getpeername())
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]
                
