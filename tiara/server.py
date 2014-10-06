import social_logic as sl
import global_data as g
import sys
import time
import select
import socket
import Queue

def HandleInput(g_data, inp):
    inp = inp.strip()
    if inp == 'reply':
        sl.Reply(g_data)
        return "ok"
    return "syntax error"

if __name__ == '__main__':

    read_only_mode = "--read-only-mode" in sys.argv
    g_data = g.GlobalData(read_only_mode)
    if read_only_mode:
        g_data.TraceInfo("In Read Only Mode!")
    

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server_address = ('localhost', 10001)
    server.bind(server_address)
    server.listen(5)
    

    g_data.TraceInfo("Starting up Tiara Boom Server on %s, port %s!" % server_address)

    inputs = [server]
    outputs = []

    message_queues = {}

    while inputs:
        
        sl.Reply(g_data)

        ############# Begin server stuff ##################
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 60)
        for s in readable:
            if s is server:
                connection, client_address = s.accept()
                g_data.TraceInfo('new connection from %s:%s' %  client_address)
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
            else:
                data = s.recv(1024)
                if data:
                    g_data.TraceInfo('received "%s" from %s' % (data, s.getpeername()))
                    message_queues[s].put(HandleInput(g_data, data))
                    if s not in outputs:
                        outputs.append(s)
                else:
                    g_data.TraceInfo('closing %s' % s.getpeername())
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()                        
                    del message_queues[s]
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                outputs.remove(s)
            else:
                g_data.TraceInfo('sending "%s" to %s' % (next_msg, s.getpeername()))
                s.send(next_msg)
        for s in exceptional:
            g_data.TraceInfo('closing %s' % s.getpeername())
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]
                
