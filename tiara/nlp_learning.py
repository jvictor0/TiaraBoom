import numpy as np
from scipy.sparse import dok_matrix

class NLPMatrix(object):
    def __init__(self, data_tups):
        self.row_ids = {}
        self.row_ixs = []
        for row_id, feat_id, val in data_tups:
            if row_id not in self.row_ids:
                self.row_ids[row_id] = len(self.row_ixs)
                self.row_ixs.append(row_id)
        self.matrix = dok_matrix((len(self.row_ixs), max([b for a,b,c in data_tups])+1))
        self.Check()
        for row_id, feat_id, val in data_tups:
            try:
                self.matrix[self.row_ids[row_id], feat_id] = val
            except Exception as e:
                print "could not insert %d,%d into mat of shape %s" % (row_id,feat_id,self.matrix.shape)
                raise e

    def Check(self):
        assert len(self.row_ids) == len(self.row_ixs)
        for i in xrange(len(self.row_ixs)):
            assert self.row_ids[self.row_ixs[i]] == i

    def ToVector(self, dct):
        assert len(dct) == len(self.row_ixs), (len(dct), len(self.row_ixs))
        result = np.zeros(len(dct))
        for a,b in dct.iteritems():
            result[self.row_ids[a]] = b
        return result
