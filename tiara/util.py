from bisect import bisect_left


# does binary search in a sorted alist
#
def BinarySearch(l, key, lo=0, hi=None):  
    hi = hi if hi is not None else len(l)
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
