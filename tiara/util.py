from bisect import bisect_left
import logging
import sys
import inspect
import traceback

import paramiko

def Indentation():
    return ' ' * len(inspect.stack())

# puts traceback into the log
def log_assert(bool_, message, g_data):
    try:
        assert bool_, message
    except AssertionError:
        # construct an exception message from the code of the calling frame
        last_stackframe = inspect.stack()[-2]
        source_file, line_no, func = last_stackframe[1:4]
        source = "Traceback (most recent call last):\n" + \
            '  File "%s", line %s, in %s\n    ' % (source_file, line_no, func)
        source_code = open(source_file).readlines()
        source += "".join(source_code[line_no - 3:line_no + 1])
        g_data.TraceError("%s\n%s" % (message, source))
        raise AssertionError("%s\n%s" % (message, source))

# does binary search in a sorted alist
#
def BinarySearch(l, key):  
    hi = len(l)
    lo = 0
    pos = bisect_left(l,(key,None),lo,hi)         
    if pos != hi and l[pos][0] == key:
        return l[pos][1]
    if pos != 0 and l[pos-1][0] == key:
        return l[pos-1][1]
    return None

def DictToSortedTuple(d):
    return tuple(sorted(d.iteritems()))

def ListInsert(dict, k, v):
    if k not in dict:
        dict[k] = [v]
    else:
        dict[k].append(v)

def NotNone(arg1, arg2):
    return arg1 if not arg1 is None else arg2


def exceptionTrace(exctype, value, tb):
    logger = logging.getLogger('TiaraBoom')
    
    logger.error('I seem to have crashed with an exception')
    logger.error('Type: %s' % str(exctype))
    logger.error('Value: %s' % str(value))
    logger.error('Traceback:\n%s' % traceback.format_tb(tb))
    

def QueryFriendBot(query, friendhost, password, pem=None, friendUsername="ubuntu"):
    client = paramiko.SSHClient()
    client.load_system_host_keys()

    client.connect(friendhost, 22, username=friendUsername, key_filename=pem)
    chan = client.get_transport().open_channel('direct-tcpip',("localhost", 10001),("localhost",10002))
    chan.send(password)
    res = chan.recv(1024)
    assert res == "welcome"
    chan.send(query)
    return chan.recv(1024)

    
