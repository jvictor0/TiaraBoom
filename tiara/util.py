

def ListInsert(dict, k, v):
    if k not in dict:
        dict[k] = [v]
    else:
        dict[k].append(v)
