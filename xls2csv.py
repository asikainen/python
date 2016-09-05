#!/usr/bin/python

# Date:        2019-09-22
# Author:      Joonas Asikainen 
# Description: Convert Excel files in the given directory to CSV              
# Usage:       python xls2csv.py path/to/files

"""
Here we go
"""

# imports
import sys
import os
import re
import time
import unicodecsv
from xlrd import open_workbook

### read Excel and write content to CSV
def xls2csv(path, fullname, dm = ';') :
    # open sheet.
    print '-- path = ', path, '; fullname = ', fullname
    start = int(round(time.time() * 1000))
    filename, extension = os.path.splitext(fullname)
    xlsfilename = path + '/' +fullname
    workbook = open_workbook(xlsfilename)
    sheetnames = workbook.sheet_names()
    
    # loop over all sheets
    print '-- reading file ', xlsfilename, '...'
    tot = 0
    for sheetname in sheetnames : 
        # extract data from current sheet and write to CSV
        csvfilename = (path + '/' + filename + '_' + sheetname + '.csv')
        with open(csvfilename, "wb") as outputfile:
            csvwriter = unicodecsv.writer(outputfile, delimiter=dm, lineterminator='\n' ,encoding='utf-8')
            print '-- writing file ', csvfilename
            sh =workbook.sheet_by_name(sheetname)
            for row in range(sh.nrows) :
                result = []
                for col in range(sh.ncols) :
                    value  = (sh.cell(row, col).value)
                    if (isinstance(value, basestring)) :
                        value = value.strip().replace('\n', ' ').replace('  ', ' ') # get rid of whitespaces and newlines
                    result.append(value)
                csvwriter.writerow(result)
                if (row > 0 and row % 10000 == 0) :
                    end = int(round(time.time() * 1000))
                    print '-- processed ', row, ' in ', (end-start), ' ms.'
                tot += 1
    # done with the file
    end = int(round(time.time() * 1000))
    
    # done
    print '-- processed ', tot, ' in ', (end-start), ' ms.'
    return  tot
    

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
    if (path.endswith('/')) :
        path = path[:-1]
    exts = ['xls', 'xlsx'] ;
    fnames = [fn for fn in os.listdir(path) if any([fn.endswith(ext) for ext in exts])];

    # convert all files
    start = int(round(time.time() * 1000))
    tot = 0
    for fname in fnames :
        tot = tot + xls2csv(path, fname)    
    end = int(round(time.time() * 1000))
    print '-- converted ', len(fnames), ' files / ', tot, ' rows in ', (end-start), ' ms.'

"""
End of story
"""
