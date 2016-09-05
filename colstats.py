#!/usr/bin/python

###
# Date:         2016-07-11
# Author:       Joonas Asikainen 
# Description:  Compute simple column stats from a CSV file (assuming a header line):
#               - col_id - ordinal number of the column
#               - col_name - name of the column
#               - min_length - minimum length of the records in the column
#               - avg_length - average length of the records in the column
#               - max_length - maximum length of the records in the column
#               - nulls - number of NULL or empty records in the column
# Usage:        python colstats.py pathToCSV delimiter [samples]

"""
Start of story.
"""

### imports
import sys
import os
import re
import time
import datetime
import csv
#import numpy

### main
if __name__ == '__main__':
    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 2) :
        print '-- usage: colstats.py pathToCSV delimiter'
        sys.exit()
    
    # args
    pathToCSV = args[0]
    delimchar = args[1]
    breakrows = 0
    if (nargs > 2) :
        breakrows = int(args[2])

    # output file name
    fileName, extension = os.path.splitext(pathToCSV)
    pathToOutput = (fileName + '_unquoted' + extension)
    
    # metadata
    print '-- input file = ', pathToCSV
    print '-- output file = ', pathToOutput
    print '-- delimiter = ', delimchar
    mins = [] #numpy.zeros(1, dtype=int)
    maxs = [] #numpy.zeros(1, dtype=int)
    avgs = [] #numpy.zeros(1, dtype=int)
    cnms = []
    nulls = []

    # loop & count
    showrows = 100000
    start = int(round(time.time() * 1000))
    procrows = 0
    with open(pathToCSV, 'rb') as inputfile :
        with open(pathToOutput, "wb") as outputfile:
            csvreader = csv.reader(inputfile, delimiter=delimchar, quotechar='"')
            for record in csvreader :
                if (procrows == 0) :
                    cols = len(record)
#                    mins = numpy.zeros(cols, dtype=int)
#                    mins += 0x01<<32
#                    maxs = numpy.zeros(cols, dtype=int)
#                    maxs -= 0x01<<32
#                    avgs = numpy.zeros(cols, dtype=int)
                    for item in record :
                        cnms.append(item)
                        mins.append(0x01<<32)
                        maxs.append(-0x01<<32)
                        avgs.append(0)
                        nulls.append(0)
                else :
                    col = 0
                    for item in record :
                        lngth = 0
                        if item != None :
                            lngth = len(item)
                        if (lngth < mins[col]) :
                            mins[col] = lngth
                        if (lngth > maxs[col]) :
                            maxs[col] = lngth
                        avgs[col] += lngth
                        if item == None or item == '':
                            nulls[col] += 1
                        col += 1
                procrows += 1
                if (procrows % showrows == 0) :
                    end = int(round(time.time() * 1000))
                    print '-- read ', procrows, ' readrows in ', (end-start), ' ms.'
                if (breakrows > 0 and procrows > breakrows) :
                    break

    # average
    for col in range(len(avgs)) :
        avgs[col] /= (1.0 * procrows)

    # output
    end = int(round(time.time() * 1000))
    print '-- finished in ', (end-start), ' ms.'
    print '-- read ', procrows, ' rows.'

    # print data
    print 'col_id\tcol_name\tmin_length\tavg_length\tmax_length\tnulls'
    for col in range(len(avgs)) :
        print (str(col) + '\t'
               + cnms[col] + '\t'
               + str(mins[col]) + '\t'
               + str(avgs[col]) + '\t'
               + str(maxs[col]) + '\t'
               + str(nulls[col]))

"""
End of story.
"""
