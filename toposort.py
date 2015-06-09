#!/usr/bin/env python

# Date:        2014-09-04
# Author:      Joonas Asikainen 
# Description: Kahn algorithm - topological sorting
# Usage:       toposort.py node_file_name edge_file_name;
#
# Sample:      Sample input data (tab-separated files edges.txt, nodes.txt)
#              below.

# edges.txt:
"""
# NodeTo	NodeFrom
City	Customer
City	SalesOrder
Customer	SalesOrder
SalesOrder	SalesOrderDetail
Product	SalesOrderDetail
"""
# nodes.txt:
"""
# Node
SalesOrder
Customer
City
SalesOrderDetail
Product
"""

#####
import sys
import math
import numpy
import time

# Kahn algorithm. 
def getTopologicalSortingLevel(matrix) :
    nxt = 0
    slist = []
    for i in range(size) :
        refs = matrix[i].sum()
        if (refs == 0) :
            slist.append([i,nxt])
    llist = []

    # topological sort algorithm
    nxt = nxt + 1
    while (slist) :
        [nn, cur] = slist.pop()
        if (nxt == cur) :
            nxt = nxt + 1
#        print nn, cur
        llist.append([nn,cur])
        for mm in range(size) :
            # remove edge
            if (matrix[mm][nn] == 1) :
                matrix[mm][nn] = 0
                refs = matrix[mm].sum()
                if (refs == 0) :
                    slist.insert(0, [mm, nxt])
    # done
    return llist

# Kahn algorithm. 
def getTopologicalSorting(matrix) :
    slist = []
    for i in range(size) :
        refs = matrix[i].sum()
        if (refs == 0) :
            slist.append(i)
    llist = []

    # topological sort algorithm
    while (slist) :
        nn = slist.pop()
        llist.append(nn)
        for mm in range(size) :
            # remove edge
            if (matrix[mm][nn] == 1) :
                matrix[mm][nn] = 0
                refs = matrix[mm].sum()
                if (refs == 0) :
                    slist.insert(0, mm)
    # done
    return llist

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 2) :
        print '-- usage: toposort.py node_file_name edge_file_name'
        sys.exit()

    # info
    print '-- toposort.py:', args

    # timing
    start = int(round(time.time() * 1000))
       
    # extract nodes
    fn = args[0]
    f = open(fn, 'r')
    nodes = []
    for line in f :
        if (not line.startswith('#')) :
            line = line.strip()
            nodes.append(line)
    f.close()
    nodes = sorted(nodes)

    # system size and the edge matrix
    size = len(nodes)
    matrix = numpy.zeros([size, size], dtype=numpy.int)

    # extract edges
    fn = args[1]
    f = open(fn, 'r')
    edges = []
    for line in f :
        if (not line.startswith('#')) :
            # edge
            edge = line.strip().split('\t')
            # exclude self-references
            if (not edge[0] == edge[1]) :
                edges.append(edge)
    f.close()
    edges = sorted(edges)

    # prepare the edge matrix
    for edge in edges :
        efrom = nodes.index(edge[1])
        eto = nodes.index(edge[0])
        matrix[efrom][eto] = 1

    # timing
    print '-- number of nodes =', len(nodes)
    print '-- number of edges =',len(edges)
    end = int(round(time.time() * 1000))
    print '-- read time =', (end-start), 'ms.'

    # sorting topologically
    start = int(round(time.time() * 1000))
    srtd = getTopologicalSortingLevel(matrix)
    end = int(round(time.time() * 1000))
    print '-- computation time =', (end-start), 'ms.'
    
    # done sorting
    cnt = matrix.sum()
    if (cnt > 0) :
        print '-- not an ADG (asyclic directed graph)'
        print '-- number of edges remaining = ', cnt
    else :
        print '-- list of nodes in topological order:'
        for [node, lvl] in srtd :
            print lvl, nodes[node]



