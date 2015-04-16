#!/usr/bin/env python

# Date: 2014-07-24
# Author: Joonas Asikainen <tjasikai@mac.com>
# Description: Implementation of a stack algorithm for integers.

#####
import sys
import math
import numpy

### Stack ###
class Stack :
    ### constructor ###
    def __init__(self, number_points):
        self.n = number_points
        self.idx = 0
        self.stack = numpy.zeros((self.n), dtype=numpy.int)

    ### reset ###
    def reset(self) :
        self.idx = 0

    ### push ###
    def push(self, i) :
        if (self.idx == self.n) :
#            print '--- appending...'
            self.stack = numpy.append(self.stack, [0, 0, 0])
            self.n += 3
        self.stack[self.idx] = i
        self.idx += 1

    ### pop ###
    def pop(self) :
        self.idx -= 1
        i = self.stack[self.idx]
        return i

    ### check if empty ###
    def empty(self) :
        return (self.idx == 0)

### main ###
#if __name__ == '__main__':
#
#    # check args
#    args = sys.argv[1:] 
#    nargs = len(args)
#    if (nargs < 1) :
#        print '# usage: stack.py n'
#        sys.exit()
#
#    # setup
#    n = int(args[0])
#    s = Stack(n)
#
#    # pushing
#    for i in range(2 * n) :
#        v = i + 1
#        print 'push; i = ', i, '; v = ', v
#        s.push(v)
# 
#    # popping
#    while (s.empty() == False) :
#        j = s.pop()
#        print 'pop; ', j
       
