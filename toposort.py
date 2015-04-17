#!/usr/bin/env python

# Date:        2014-09-04
# Author:      Joonas Asikainen 
# Description: Kahn algorithm - topological sorting

#        sumOverRow = matrix[i].sum()
#        sumOverCol = matrix[:,i].sum()

#####
import sys
import math
import numpy
import time


# Depth-first algorithm 
def getTopologicalSortingDepthFirst(matrix, dbg) :
    
    # unmarked = 0, temporarily marked = 1, marked = 2
    srtd = []
    size = len(matrix[0])
    nodes = numpy.zeros(size, dtype=int)
    #print numpy.where(nodes == 0)[0]

    # loop while unmarked nodes left 
    unmarked = size
    while (unmarked > 0) :
        node = -1 
        for n in range(size) :
            if (nodes[n] == 0) :
                node = n
                break
        visit(matrix, nodes, node, srtd)
        unmarked = sum([1 for x in nodes if x == 0])

    # remove edges and return the sorted list
    for i in range(size) :
        for j in range(size) :
            matrix[i][j] = 0 
    return srtd


# visit a node
def visit(matrix, nodes, nn, srtd) :
    size = len(nodes)

    if (nodes[nn] == 1) :
        print '-- not a ADG!'
        sys.exit()

    if (nodes[nn] == 0) :
        nodes[nn] = 1 # temporary mark
        for mm in range(size) :
            # visit referencing node
            if (matrix[mm][nn] == 1) :
                visit(matrix, nodes, mm, srtd)
        nodes[nn] = 2
        srtd.insert(0, nn)
    return

# Kahn algorithm 
def getTopologicalSortingKahn(matrix, dbg) :
    slist = []
    for i in range(size) :
        refs = matrix[i].sum()
        if (refs == 0) :
            slist.append(i)
    if (dbg) :
        print '-- non-referenced nodes:', slist
    llist = []

    # topological sort algorithm
    while (slist) :
        nn = slist.pop()
        llist.append(nn)
#        print '-- adding node ', nn
        for mm in range(size) :
            # remove edge
            if (matrix[mm][nn] == 1) :
#                print '-- removing edge (mm, nn) = (', mm, ',', nn,')'
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

    # debug printing flag
    dbg = False

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
    if (dbg) :
        print '-- nodes:', nodes

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
    if (dbg) :
        print '-- edges',edges

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
    srtd = getTopologicalSortingKahn(matrix, dbg)
    end = int(round(time.time() * 1000))
    print '-- computation time =', (end-start), 'ms.'
    
    # done sorting
    cnt = matrix.sum()
    if (cnt > 0) :
        print '-- not an ADG (asyclic directed graph)'
        print '-- number of edges remaining = ', cnt
    else :
        print '-- list of nodes in topological order:'
        for node in srtd :
            print nodes[node]



