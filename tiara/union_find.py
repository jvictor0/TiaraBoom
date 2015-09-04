

def Find(uf, k):
    v = uf[k]
    if v == k:
        return v
    result = Find(uf, v)
    uf[k] = result
    return result

def UnionFind(uf):
    results = {}
    for k in uf.keys():
        v = Find(uf, k)
        if v not in results:
            results[v] = []
        results[v].append(k)
    return results

