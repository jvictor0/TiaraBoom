import snode
import copy

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
        
    def _rewrite(self, s):
        return s    
    
    def PostOrderTraversal(self, s):
        self.stack.append(s)
        if s.IsLeaf():
            result = self._rewrite(s)
        else:
            newNode = snode.SNode(s.tags, *[self.PostOrderTraversal(s[i]) for i in xrange(len(s))])
            result = self._rewrite(newNode)
        self.stack.pop()
        return result
        
    def __call__(self, ctx, s):
        self.Init(ctx, s)
        return self.PostOrderTraversal(s)
    
class CommonEntityEliminator(SyntaxRewriter):

    def __init__(self, tp):
        self.tp = tp
    
    def _init(self, s):
        self.entities = set([])
        
    def _rewrite(self, s):
        subjEntity = s.tags["type"] == snode.ENTITY and any([t.tags["type"] == self.tp for t in self.stack])
        if subjEntity:
            name = s.tags["name"]
            if name in self.entities:
                pron = self.ctx.SubjectPronoun(name) if self.tp == snode.SUBJECT else self.ctx.ObjectPronoun(name)
                if pron is not None:
                    return snode.SNode(s.tags, snode.SNode({"type":snode.PRONOUN}, pron))
            self.entities.add(name)
        return s

def RewriteSyntax(ctx, s):
    s = CommonEntityEliminator(snode.SUBJECT)(ctx, s)
    s = CommonEntityEliminator(snode.OBJECT)(ctx, s)
    return s
