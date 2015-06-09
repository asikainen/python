#!/usr/bin/env python

# Date:        2015-06-09
# Author:      Joonas Asikainen 
# Description: Computes the path length in a graph based on
#              edges connecting the nodes by traversal.

#####
import sys
import math
import numpy
import time

# global variable(s)
maxlevel = 0

### grap traversal
def traverse(node, edges, level) :
    global maxlevel
    if (level > maxlevel) :
        maxlevel = level
    for edge in [e for e in edges if e[1] == node] :
        traverse(edge[0], edges, level + 1)
    return

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 3) :
        print '-- usage: maxpath.py node_file_name edge_file_name start_node'
        sys.exit()

    # info
    print '-- maxpath.py:', args
    
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

    # info
    print '-- number of nodes =', len(nodes)
    print '-- number of edges =',len(edges)

    # iterate from start node
    node = args[2]
    if (not node in nodes) :
        print '-- node ', node, ' not in the list, exiting...'
        sys.exit()

    # compute
    level = 0
    traverse(node, edges, level)
    print '-- start node = ', node, '; max level = ', maxlevel
