from bisect import bisect_left
import logging
import sys
import inspect
import traceback
import datetime

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
def BinarySearch(l, key, index = False):  
    hi = len(l)
    lo = 0
    pos = bisect_left(l,(key,None),lo,hi)
    if index:
        return pos
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

def Median(nums):
    return sorted(nums)[len(nums)/2]

def Differences(nums):
    nums = sorted(nums)
    result = []
    for i in xrange(len(nums)-1):
        result.append(nums[i+1] - nums[i])
    return result

def exceptionTrace(exctype, value, tb):
    logger = logging.getLogger('TiaraBoom')
    
    logger.error('I seem to have crashed with an exception')
    logger.error('Type: %s' % str(exctype))
    logger.error('Value: %s' % str(value))
    logger.error('Traceback:\n%s' % "".join(traceback.format_tb(tb)))
    

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

def ToWordForm(g_data,word,form):
    return [w for w, t in g_data.FamilyLookup(word) if t == form]

def LKD(d,a,r=None):
    return d[a] if a in d else r

def LKDT(d,a):
    return LKD(d,a,True)
def LKDF(d,a):
    return LKD(d,a,True)
def LKD0(d,a):
    return LKD(d,a,0)
def LKDS(d,a):
    return LKD(d,a,"")
def LKDL(d,a):
    return LKD(d,a,[])

def SKD(a,d,r):
    if not a in d:
        d[a] = r

def joinit(delimiter, iterable):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x

def FormatResponse(tweet,response):
    return '@' + tweet.GetUser().GetScreenName() + ": " + response

def Const(x):
    return lambda g_data, args: x
ConstTrue = Const(True)

def GetURL(status):
    return "https://twitter.com/%s/status/%d" % (status.GetUser().GetScreenName(), status.GetId())

# looks like Fri Jan 02 03:14:31 +0000 2015
def TwitterTimestampToMySQL(ts):
    ts = ts.split()
    assert ts[0] in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], ts
    mon = str(1 + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(ts[1]))
    if len(mon) == 1:
        mon = "0" + mon
    day = ts[2]
    time = ts[3]
    assert ts[4] == "+0000", ts
    year = ts[5]
    return "%s-%s-%s %s" % (year,mon,day,time)

# looks like 2008-09-15 00:15:03
def MySQLTimestampToTwitter(msts):
    if msts == "0000-00-00 00:00:00":
        return None
    ts = MySQLTimestampToPython(msts)
    dow = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][ts.weekday()]
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][ts.month-1]
    def pad(a):
        if len(a) == 1:
            return "0" + a
        return a

    day = pad("%d" % ts.day)
    hour= pad("%d" % ts.hour)
    minute = pad("%d" % ts.minute)
    second = pad("%d" % ts.second)    
    year = "%d" % ts.year
    result = "%s %s %s %s:%s:%s +0000 %s" % (dow,mon,day,hour,minute,second,year)
    assert TwitterTimestampToMySQL(result) == msts, (result,msts,TwitterTimestampToMySQL(result))
    return result

def MySQLTimestampToPython(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

def OlderThan(ts,days):
    return (ts.now() - ts) > datetime.timedelta(days,0,0)

def Decay(x):
    return max(0,3 - 0.5**(x-2))

def Int(x):
    if x is None:
        return None
    return int(x)

def ImageURLToTuple(url):
    assert url.startswith("https://pbs.twimg.com/profile_images/"), url
    url = url[len("https://pbs.twimg.com/profile_images/"):]
    url = url.split("/")
    assert len(url) == 2, url
    assert url[1].endswith("_normal.jpg"), url
    return int(url[0]), url[1][:-len("_normal.jpg")]

def TupleToImageURL(imid, hsh):
    if str(imid) == "0":
        return "https://abs.twimg.com/sticky/default_profile_images/default_profile_2_normal.png"
    return "https://pbs.twimg.com/profile_images/" + str(imid) + "/" + hsh + "_normal.jpg"
