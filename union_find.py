#!/usr/bin/env python

# Date: 2014-07-24
# Author: Joonas Asikainen <tjasikai@mac.com>
# Description: Implementation of the clustering algorithm 
# "Union-find with path compression" (as in Ref. [1]).
#
# References:
# 
# 1. M. E. J. Newman1 and R. M. Ziff Phys. Rev. E 64, 016706 (2001)
#

#####
import sys
import numpy
import stack

### union find with weighting and path compression ###
class UnionFind :
    ### constructor ###
    def __init__(self, number_points):
        self.n = number_points
        self.ptr = numpy.zeros((self.n), dtype=numpy.int)
        self.reset()
        self.stck = stack.Stack(100)

    ### reset ###
    def reset(self) :
        # reset pointer array
        for i in range(self.n):
            self.ptr[i] = -1

    ### check if root ###
    def root(self, i) :
        return (self.ptr[i] < 0)

    ### find method ###
    def find(self, i) :
        # check bounds
        if (i < 0 or i >= self.n) :
            si = str(i)
            sn = str(self.n)
            msg = 'UnionFind(' + sn + '); index out of bounds: ' + si
            raise LookupError(msg)

        # check if root
        if (self.ptr[i] < 0) :
            return i

        # iterate to root; store path to stack
        cnt = 0
        self.stck.reset()
        j = self.ptr[i]
        while j >= 0 :
            ri = j
            self.stck.push(ri)
            j = self.ptr[ri]
            cnt += 1
            if (cnt > 100) :
                print 'maxiter exceeded'
                return -101010101
        r = ri

        # iterate back to 'i' and point nodes to root
        while (self.stck.empty() == False) :
            j = self.stck.pop()
            if (j != r) :
                self.ptr[j] = r

        # done
        return r

    ### union method ###
    def union(self, i, j) :
        # roots of i and j
        r1 = self.find(i); 
        r2 = self.find(j);

        # if r1 and r2 differ, point smaller to larger
        if (r1 == r2) :
            return r1; 
        if (self.ptr[r1] > self.ptr[r2]) :
            self.ptr[r2] += self.ptr[r1]; 
            self.ptr[r1] = r2; 
            r1 = r2; 
        else :
            self.ptr[r1] += self.ptr[r2]; 
            self.ptr[r2] = r1; 

        # done
        return r1; 
 
    ### printing ###
    def output(self) :
        print self.ptr

### main ###
#if __name__ == '__main__':
#
#    # check args
#    args = sys.argv[1:] 
#    nargs = len(args)
#    if (nargs < 1) :
#        print '# usage: union_find.py n'
#        sys.exit()
#    
#    # setup
#    n = int(args[0])
#    uf = UnionFind(n)
#
#    # find
#    i = 0
#    n2 = int(n/2)
#    while (i < n2) :
#        j = (n-i-1)
#        r = uf.union(i, j)
#        print i, j, r
#        uf.output()
#        i += 1
#
#    print n2, (n2+1)
#    uf.union(n2, n2+1)
#    uf.output()
#
#    for i in range(n) :
#        print i, uf.find(i), uf.root(i)
