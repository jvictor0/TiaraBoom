import artrat.lispparse as lisp

class ExpansionUnit(object):
    def __init__(self, grandparent, parent_symbol, parent_text):
        self.grandparent = grandparent
        self.parent_symbol = parent_symbol
        self.parent_text = parent_text

class LeafExpansionUnit(ExpansionUnit):
    def __init__(self, grandparent, parent_symbol, parent_text, pos, word):
        super(ExpansionUnit, self).__init__(grandparent, parent_symbol, parent_text)
        self.pos = pos
        self.word = word

    def Expand(self, ctx):
        return lisp.Lisp(self.pos, self.word)
        
class InnerExpansionUnit(ExpansionUnit):
    def __init__(self, grandparent, parent_symbol, parent_text, child_lisp):
        super(InnerUnit, self).__init__(grandparent, parent_symbol, parent_text)
        self.child_lisp = child_lisp

    def Expand(self, ctx):
        result = []
        for i in xrange(len(self.child_lisp)):
            if self.child_lisp.At(i).IsLeaf():
                result.append(child_lisp.At(i))
            else:
                pos = self.child_lisp.At(i).POS()
                last_pos = None if i == 0 else result[-1].POS()
                last_text = "" if i == 0 else result[-1].ToText()
                lku = ctx.Lookup(parent_symbol, last_pos, last_text)
                result.append(lku.Expand(ctx))
        return lisp.Lisp(self.child_lisp.POS(), *result)

def FromPenn(lisp):
    result = []
    if lisp.IsLeaf():
        return []
    for i in xrange(len(lisp)):
        if lisp.At(i).IsLeaf():
            continue
        if i == 0:
            result.append(InnerExpansionUnit(lisp.POS(), None, "", lisp.At(i)))
        else:
            result.append(InnerExpansionUnit(lisp.POS(), lisp.At(i-1).POS(), lisp.At(i-1).ToText(), lisp.At(i)))
