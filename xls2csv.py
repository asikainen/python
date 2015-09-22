#!/usr/bin/python

# Date:        2019-09-22
# Author:      Joonas Asikainen 
# Description: Convert Excel files in the given directory to CSV              
# Usage:       python xls2csv.py path/to/files

# imports
import sys
import os
import re
import time
from xlrd import open_workbook

### read Excel and write content to CSV
def xls2csv(fullname) :
    filename, extension = os.path.splitext(fullname)
    

    # open sheet.
    book = open_workbook(fullname)
    sh = book.sheet_by_index(0)    

    # extract data and write to CSV
    start = int(round(time.time() * 1000))
    fout = open(filename + '.csv', 'w')
    print '-- reading file ', fullname, ' sheet ', book.sheet_names()[0], '.'
    print '-- writing  file ', (filename + '.csv.')
    for row in range(sh.nrows) :
        for col in range(sh.ncols) :
            value  = (sh.cell(row, col).value)
            fout.write(str(value))
            if (col < sh.ncols - 1) :
                fout.write(';')
        fout.write('\n')
        if (row > 0 and row % 10000 == 0) :
            end = int(round(time.time() * 1000))
            print '-- processed ', row, ' in ', (end-start), ' ms.'
    fout.close()
    end = int(round(time.time() * 1000))
    print '-- processed ', row, ' in ', (end-start), ' ms.'
    return  (sh.nrows)
    

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 1) :
        print '-- usage: xls2csv.py path/to/files'
        sys.exit()
    print '-- xls2csv.py ', args

    # extract Excel files in the path
    path = args[0]
    exts = ['xls', 'xlsx'] ;
    fnames = [fn for fn in os.listdir(path) if any([fn.endswith(ext) for ext in exts])];

    # convert all files
    start = int(round(time.time() * 1000))
    tot = 0
    for fname in fnames :
        tot = tot + xls2csv(fname)    
    end = int(round(time.time() * 1000))
    print '-- converted ', len(fnames), ' files / ', tot, ' rows in ', (end-start), ' ms.'
