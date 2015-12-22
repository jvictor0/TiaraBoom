

def LispTokenize(str):
    str = str.replace("("," ( ").replace(")"," ) ")
    return str.split()

def MultiLispParse(toks):
    lisp = _LispParse(LispTokenize(toks),0)[0]
    result = []
    for r in lisp:
        result.append(Lisp())
        result[-1].l = r
    return result

def Load(filename):
    with open(filename, "r") as f:
        return MultiLispParse(f.read())

def Dump(lisps, filename):
    with open(filename, "w") as f:
        for l in lisps:
            print >>f, str(l)

def LispParse(toks):
    lisp = _LispParse(LispTokenize(toks),0)[0]
    assert len(lisp) == 1
    return lisp[0]

def _LispParse(toks, ix=0):
    result = []
    while ix < len(toks):
        if toks[ix] == "(":
            nxt, ix = _LispParse(toks,ix+1)
            result.append(nxt)
        elif toks[ix] == ")":
            return result, ix+1
        else:
            result.append(toks[ix])
            ix += 1
    return result, ix

def Narrow(a):
    return isinstance(a,str) or (len(a) == 2 and isinstance(a[0],str) and Narrow(a[1]))
        
def LispPrint(lisp, indentation=""):
    if not isinstance(lisp,list):
        return lisp
    if Narrow(lisp):
        return "(" + " ".join(map(LispPrint,lisp)) + ")"
    assert not isinstance(lisp[0], list), "not supporting that..."
    prefix = "(" + lisp[0] + "\n"
    nid = indentation + "    "
    body = "\n".join([nid + LispPrint(lisp[i], nid) for i in xrange(1,len(lisp))])
    return prefix + body + "\n" + indentation + ")"

def L(pos, *children):
    result = Lisp()
    result.l = [pos]
    for c in children:
        if isinstance(c,str):
            result.l.append(c)
        else:
            result.l.append(c.l)
    return result

class Lisp:
    def __init__(self, string = None):
        if string:
            self.l = LispParse(string)

    def __str__(self):
        return LispPrint(self.l)

    def IsLeaf(self):
        return len(self.l) == 2 and not isinstance(self.l[1], list)

    def POS(self):
        return self.l[0]

    def __len__(self):
        return len(self.l) - 1

    def At(self, i):
        result = Lisp()
        result.l = self.l[i+1]
        return result

    def Flatten(self):
        if self.IsLeaf():
            return [tuple(self.l)]
        return [f for i in xrange(len(self)) for f in self.At(i).Flatten()]

    def ToText(self):
        if self.IsLeaf():
            return self.l[1]
        return " ".join([self.At(i).ToText() for i in xrange(len(self))])

    def Narrow(self):
        return self.IsLeaf() or len(self) == 1 and self.At(0).IsLeaf()
