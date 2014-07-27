#!/usr/bin/env python

# Date: 2014-07-24
# Author: Joonas Asikainen <tjasikai@mac.com>
# Description: Implementation of "Locality-sensitive hashing using 
# stable distributions" (http://people.csail.mit.edu/indyk/nips-nn.ps). 
#
# lsh.py implements Locality-sensitive hashing  (as in Ref. [1]). the
# main method also enables testing the algorithm by generating random
# coordinates and computing the locality sensitive hashes and printing
# out the pairs which are close to each other (based on the hash value).
#
# References: 
#
# 1. Nearest Neighbor Methods in Learning and Vision: Theory and Practice,
# by T. Darrell and P. Indyk and G. Shakhnarovich (eds.), MIT Press,
# 2006. 
#

#####
import sys
import math
import random
import numpy

### Locality Sensitive Hash ###
class LocalitySensitiveHash :

    ### constructor ###
    def __init__(self, d, k, l):
        # fix variables
        self.w = 4 # k-bin resolution
        self.d = d
        self.k = k
        self.l = l
        self.prime1 = (2**31-1)
        self.prime2 = (2**32-5)

        # gaussian coefficient array
        self.seedA = long(self.prime1)
        random.seed(self.seedA)
        self.a = numpy.zeros((self.l, self.k, self.d), dtype=numpy.float)
        for ll in range(self.l) :
            for kk in range(self.k) :
                for dd in range(self.d) :
                    self.a[ll][kk][dd] = random.gauss(0.0, 1.0)
        
        # uniformly random constants array
        self.seedB = long(((self.prime1+1)>>1)-1)
        random.seed(self.seedB)
        self.b = numpy.zeros((self.l, self.k), dtype=numpy.float)
        for ll in range(self.l) :
            for kk in range(self.k) :
                self.b[ll][kk] = (random.random() * self.w)

        # R_1 hash coefficient array
        self.seedR1 =  long(((self.prime1+1)>>2)-1)
        self.r1 = numpy.zeros((self.k), dtype=numpy.long)
        random.seed(self.seedR1)
        for kk in range(self.k) :
            self.r1[kk] = (random.randint(1, long(self.prime1)))
                             
        # R_2 hash coefficient array
        self.seedR2 =  long(((self.prime1+1)>>3)-1)
        self.r2 = numpy.zeros((self.k), dtype=numpy.long)
        random.seed(self.seedR2)
        for kk in range(self.k) :
            self.r2[kk] = (random.randint(1, long(self.prime1)))

        # printing
        print '# seeds: ', self.seedA, self.seedB, self.seedR1, self.seedR2
        print '# parameters: ', self.d, self.k, self.l, self.w
#        print '# random a-vectors:'
#        print self.a
#        print '# random b-values:'
#        print self.b
        self.minh = +int(self.prime1)
        self.maxh = -int(self.prime1)

    ### hash input v ###
    def getHashes(self, v) :
        # check dimensionality
        if (len(v) != d) :
            return None

        # loop over k random vs 
        hashKeyValueList = []
        for ll in range(self.l) :
            hashes = self.getHashesL(ll, v)
            [key, value] = self.getKeyValue(hashes)
            hashKeyValueList.append([key, value])

        # done
        return hashKeyValueList

    ### hashes ###
    def getHashesL(self, ll, v) :
        hashes = []
        for kk in range(self.k) :
            hk = self.getHashK(ll, kk, v)
            if (hk < self.minh) :
                self.minh = hk
            if (hk > self.maxh) :
                self.maxh = hk
            hashes.append(hk)
        return hashes

    ### hashes ###
    def getHashK(self, ll, kk, v) :
        h = 0.0
        for [ai, vi] in zip(self.a[ll][kk], v) :
            h += (ai * vi)
        h += (self.b[ll][kk])
        h /= self.w
        return int(math.floor(h))


    ### k hashes to key-value ###
    def getKeyValue(self, hashes) :
        # hash the key
        key = 0
        for kk in range(self.k) :
            key += self.r1[kk] * hashes[kk]
        key = (key % self.prime2)

        # hash the value
        value = 0
        for kk in range(self.k) :
            value += self.r2[kk] * hashes[kk]
        value = (value % self.prime2)

        # done
        return [key, value]

    ### printing ###
    def printInfo(self) :
        print '# min(h) = ', self.minh, '; max(h) = ', self.maxh

### n random points in d dimensions
def randomCoordinates(d, n) :
    pts = numpy.zeros((n, d), dtype=numpy.float)
    random.seed(918273645)
    ns = int(n / 5)
    for nn in range(n) :
        add = (nn % ns) * 2
        for dd in range(d) :
            pts[nn][dd] = (random.random() + add)
    return pts

### n random points in d dimensions
def distance(x, y) :
    d = 0.0
    for [xi, yi] in zip(x, y) :
        d += (xi - yi)**2
    return math.sqrt(d)

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 2) :
        print '# usage: lsh.py d n'
        sys.exit()

    # read input parameters 
    d = int(args[0]) # dimensions
    n = int(args[1]) # number of points

    # fixed (reasonable) probability values
    p1 = 0.99 # success probability
    p2 = 0.01 # false positive probability

    # compute 
    k = int(math.log(n) / math.log(1.0/p2) + .5)
    if (k < 5) :
        k = int(5)
    rho = math.log(1./p1) / math.log(1./p2)
    l = int(n**rho + .5)
    if (l < 3) :
        l = int(3)

    # print
    print '# d = ', d, '; n = ', n, '; p1 = ', p1, \
        '; p2 = ', p2, '; k = ', k, '; rho = ', rho, '; L = ', l, \
        '; n^rho = ', (n**rho)

    # points
    pts = randomCoordinates(d, n)
    print '# points:'
    print pts

    # distances
    print '# distances:'
    for i in range(n) :
        for j in range(i+1, n) :
            dst = distance(pts[i], pts[j])
            close = 0
            if (dst < 1.0) :
                close = 1
            print 'dist(i,j) = ', i, j, dst, '; close = ', close

    # locality sensitive hashing
    lsh = LocalitySensitiveHash(d, k, l)

    # hashing
    print ''
    for nn in range(n) :
        print '# hash ', nn
        results = lsh.getHashes(pts[nn])
        print results
    lsh.printInfo()
