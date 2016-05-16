import snode
import copy
import os.path
import contractions
import sys

def Reload():
    snode.Reload()
    reload(contractions)
    return reload(sys.modules[__name__])

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

    def _after(self, result, s):
        pass
    
    def PostOrderTraversal(self, s):
        self.stack.append(s)
        if s.IsLeaf():
            result = self._rewrite_leaf(s)
        else:
            newNode = snode.SNode(s.tags, *[self.PostOrderTraversal(s[i]) for i in xrange(len(s))])
            result = self._rewrite(newNode)
        self.stack.pop()
        self._after(result, s)
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
    def __init__(self, tp, tp2=None):
        self.tp = tp
        if tp2 is None:
            self.tp2 = self.tp
        else:
            self.tp2 = tp2
    
    def _init(self, s):
        self.entities = set([])
        self.used = set([])
            
    def _rewrite(self, s):
        subjEntity = s.Type() == snode.ENTITY and "entity_type" in s.tags and s.tags["entity_type"] in [self.tp,self.tp2]
        if subjEntity:
            name = s.tags["key"]
            if name in self.entities and s.tags["entity_type"] == self.tp2:
                pron = self.ctx.SubjectPronoun(name) if self.tp == snode.PRIMARY_SUBJECT else self.ctx.ObjectPronoun(name)
                if pron is not None:
                    self.used.add(name)
                    return snode.SNode(s.tags, snode.SNode({"type":snode.PRONOUN}, pron))
            if s.tags["entity_type"] == self.tp:
                self.entities.add(name)
        return s

    def _rewrite_leaf(self, s):
        return self._rewrite(s)

class CommonAutoEntityEliminator(SyntaxRewriter):

    def _init(self, s):
        self.entities = set([])
        self.used = set([])
            
    def _rewrite(self, s):
        subjEntity = s.Type() == snode.ENTITY and "entity_type" in s.tags and s.tags["entity_type"] == snode.PRIMARY_SUBJECT
        objEntity = s.Type() == snode.ENTITY and "entity_type" in s.tags and s.tags["entity_type"] == snode.PRIMARY_OBJECT
        objEntity = objEntity and "toplevel" in s.tags and s.tags["toplevel"]
        if subjEntity:
            name = s.tags["key"]
            self.entities.add(name)
        if objEntity:
            name = s.tags["key"]
            if name in self.entities:
                pron = self.ctx.SelfPronoun(name)
                if pron is not None:
                    self.used.add(name)
                    return snode.SNode(s.tags, snode.SNode({"type":snode.PRONOUN}, pron))
        return s

    def _after(self, result, s):
        if s.tags["type"] == snode.FACT:
            self.entities = set([])
    
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

    def __init__(self, conts):
        self.conts = conts
    
    def _rewrite(self, s):        
        cs = []
        i = 0
        while i < len(s):        
            if len(s) > i+1 and s[i].IsLeaf() and s[i+1].IsLeaf() and (s[i].Word().lower(), s[i+1].Word().lower()) in self.conts:
                c = self.conts[(s[i].Word().lower(), s[i+1].Word().lower())]
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
    sr_auto = CommonAutoEntityEliminator()
    s = sr_auto(ctx, s)
    if ctx.debug: print "[REWRITER] (auto entity)     ", s.ToText()
    sr_subj = CommonEntityEliminator(snode.PRIMARY_SUBJECT)
    s = sr_subj(ctx, s)    
    if ctx.debug: print "[REWRITER] (subject pronoun) ", s.ToText()
    sr_obj = CommonEntityEliminator(snode.PRIMARY_OBJECT)
    s = sr_obj(ctx, s)
    if ctx.debug: print "[REWRITER] (object pronoun)  ", s.ToText()
    if len(sr_subj.used | sr_obj.used) <= 1 and len(sr_auto.used) == 0:
        sr_cross = CommonEntityEliminator(snode.PRIMARY_SUBJECT, snode.PRIMARY_OBJECT)
        s = sr_cross(ctx, s)
        if ctx.debug: print "[REWRITER] (cross pronoun)   ", s.ToText()
    s = SentenceFlattener()(ctx, s)
    if ctx.debug: print "[REWRITER] (flattener)       ", s.ToText()
    s = ContractionIntroducer(contractions.contractions)(ctx, s)
    if ctx.debug: print "[REWRITER] (contractions)    ", s.ToText()
    s = ContractionIntroducer(contractions.protracts)(ctx, s)
    if ctx.debug: print "[REWRITER] (pron contracts)  ", s.ToText()
    s = SentenceCapitalizer()(ctx, s)
    if ctx.debug: print "[REWRITER] (capitalizer)     ", s.ToText()
    return s
