import snode
import copy
import os.path
import contractions

def Reload():
    reload(snode)
    snode.Reload()

class SyntaxRewriter(object):

    def Init(self, ctx, s):
        self.ctx = ctx
        self.stack = []
        self._init(s)

    def _init(self, s):
        pass

    def _rewrite_leaf(self, s):
        return s
        
    def _rewrite(self, s):
        return s    
    
    def PostOrderTraversal(self, s):
        self.stack.append(s)
        if s.IsLeaf():
            result = self._rewrite_leaf(s)
        else:
            newNode = snode.SNode(s.tags, *[self.PostOrderTraversal(s[i]) for i in xrange(len(s))])
            result = self._rewrite(newNode)
        self.stack.pop()
        return result
        
    def __call__(self, ctx, s):
        self.Init(ctx, s)
        return self.PostOrderTraversal(s)

class Copy(SyntaxRewriter):
    pass
    
class SyntaxNormalizer(SyntaxRewriter):

    def _rewrite_leaf(self, s):
        if s.Type() == snode.SYNTAX:
            if s.IsLeaf():
                cs = [snode.SNode({"type":snode.SYNTAX}, w) for w in s.Word().split()]
                if len(cs) == 1:
                    return s
                return snode.SNode(s.tags, *cs)
        return s
    
    def _rewrite(self, s):
        if s.Type() == snode.SYNTAX:
            if len(s) == 1:
                return s[0]
            cs = []
            for i in xrange(len(s)):
                if s[i].Type() != snode.SYNTAX or s[i].IsLeaf():
                    cs.append(s[i])
                else:
                    for j in xrange(len(s[i])):
                        cs.append(s[i][j])
            return snode.SNode(s.tags, *cs)
        return s
    
class CommonEntityEliminator(SyntaxRewriter):

    def __init__(self, tp):
        self.tp = tp
    
    def _init(self, s):
        self.entities = set([])
            
    def _rewrite(self, s):
        subjEntity = s.Type() == snode.ENTITY and any([t.Type() == self.tp for t in self.stack])
        if subjEntity:
            name = s.tags["name"]
            if name in self.entities:
                pron = self.ctx.SubjectPronoun(name) if self.tp == snode.SUBJECT else self.ctx.ObjectPronoun(name)
                if pron is not None:
                    return snode.SNode(s.tags, snode.SNode({"type":snode.PRONOUN}, pron))
            self.entities.add(name)
        return s

    def _rewrite_leaf(self, s):
        return self._rewrite(s)
    
class SentenceCapitalizer(SyntaxRewriter):

    def Capitalize(self, s):
        if s.IsLeaf():
            w = s.Word()
            w = w[0].upper() + w[1:]
            return snode.SNode(s.tags, w)
        else:
            cs = [self.Capitalize(s[0])] + [s[i+1] for i in xrange(len(s)-1)]
            return snode.SNode(s.tags, cs)

    def _rewrite(self, s):
        if s.Type() == snode.SENTENCE:
            return self.Capitalize(s)
        return s

class SentenceFlattener(SyntaxRewriter):

    def _rewrite(self, s):
        cs = []
        for i in xrange(len(s)):
            if s[i].IsLeaf() or s[i].Type() == snode.SENTENCE:
                cs.append(s[i])
            else:
                for j in xrange(len(s[i])):
                    cs.append(s[i][j])
        return snode.SNode(s.tags, *cs)
            
    
class ContractionIntroducer(SyntaxRewriter):

    def _rewrite(self, s):        
        cs = []
        i = 0
        while i < len(s):        
            if len(s) > i+1 and s[i].IsLeaf() and s[i+1].IsLeaf() and (s[i].Word().lower(), s[i+1].Word().lower()) in contractions.contractions:
                c = contractions.contractions[(s[i].Word().lower(), s[i+1].Word().lower())]
                cs.append(snode.SNode(s[i].tags, c))
                i = i + 1
            else:
                cs.append(s[i])
            i = i + 1
        return snode.SNode(s.tags, *cs)
    
def RewriteSyntax(ctx, s):
    if ctx.debug: print "[REWRITER] (start)           ", s.ToText()
    s = SyntaxNormalizer()(ctx, s)
    if ctx.debug: print "[REWRITER] (normalized)      ", s.ToText()
    s = CommonEntityEliminator(snode.SUBJECT)(ctx, s)
    if ctx.debug: print "[REWRITER] (subject pronoun) ", s.ToText()
    s = CommonEntityEliminator(snode.OBJECT)(ctx, s)
    if ctx.debug: print "[REWRITER] (object pronoun)  ", s.ToText()
    s = SentenceFlattener()(ctx, s)
    if ctx.debug: print "[REWRITER] (flattener)       ", s.ToText()
    s = ContractionIntroducer()(ctx, s)
    if ctx.debug: print "[REWRITER] (contractions)    ", s.ToText()
    s = SentenceCapitalizer()(ctx, s)
    if ctx.debug: print "[REWRITER] (capitalizer)     ", s.ToText()
    return s
