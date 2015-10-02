#!/usr/bin/python

# Date:        2019-09-22
# Author:      Joonas Asikainen 
# Description: Schema/Table/Column/Type diff tool
# Usage:       python dwhdiff.py fileA.csv fileB.csv

"""
-- SQL for Sybase IQ to extract input to be stored in files A and B.
SELECT usr.name table_owner,
    obj.name table_name,
    col.name column_name,
    col.colid column_id,
    typ.name data_type,
    col.prec precision,
    col.scale, 
    col.length
FROM dbo.sysobjects obj
JOIN dbo.syscolumns col
ON obj.id=col.id
JOIN dbo.sysusers usr
ON obj.uid=usr.uid
JOIN dbo.systypes typ
ON col.type      = typ.type
AND col.usertype = typ.usertype
WHERE usr.name   IN ('UDM', 'DELTA')
AND obj.type = 'U'
AND OBJ.NAME NOT LIKE 'DELTA_BUDGET'
AND OBJ.NAME NOT LIKE '%MNBI%'
ORDER BY usr.name,
    obj.name,
    col.name;
"""

# imports
import sys
import os
import re
import csv
import math
import time
import datetime

### read CSV file ###
def readCsvFile(pathToFile, separator=';') :
    print '-- reading file ', pathToFile
    with open(pathToFile, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=separator, quotechar='"')
        row = 0
        skip = 0
        columns = []
        records = []
        for record in csvreader :
            # header/column names
            if (row == 0) :
                for item in record :
                    columns.append(item.lower())
            # data; check for bad/good
            else :
                if (len(columns) != len(record)) :
                    print '-- skipping row ', row, '; not all records available!'
                    skip += 1
                else :
                    records.append(record)
            # row count
            row += 1
    print '-- read ', row, ' rows; skipped ', skip, ' rows.'
    return [columns, records]

### comparison of records A/B; returns tuple [cmp, col] where "cmp"
### can get any of the values [-1, 0, 1]:
###     -1 indicates recordA < recordB (in column "col")
###      0 indicates recordA = recordB (in all columns)
###     +1 indicates recordA < recordB (in column "col")
def compare(recordA, recordB) :
    res = 0
    col = 0
    if (recordA == None) :
        res = +1
        return [res, col]
    elif (recordB == None) :
        res = -1
        return [res, col]
    else :
        for a, b in zip(recordA, recordB) :
            if (a < b) :
                res = -1
                return [res, col]
            elif (a > b) :
                res = +1
                return [res, col]
            col += 1
        return [res, col]

### get current record (None if out of range)
def getCurrentRecord(row, rows, records) :
    if (row < rows) :
        return records[row]
    else :
        return None

### main ###
if __name__ == '__main__':

    # check args
    target = ['table_owner','table_name','column_name','colummn_id','data_type', 'precision', 'scale', 'length']
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 2) :
        print '-- usage: dwhdiff.py path/to/fileA path/to/fileB [separator]'
        print '-- \tpath/to/fileA: data from DWH A - required.'
        print '-- \tpath/to/fileB: data from DWH B - required.'
        print '-- \tseparator: field delimiter in CSV file (default is ";") - optional.'
        sys.exit()
    print '-- dwhdiff.py version 1.0.'

    # extract Excel files in the path
    pathToA = args[0]
    pathToB = args[1]
    separator = ';'
    if (len(args) > 2) :
        separator = args[2]

    # start time
    start = int(round(time.time() * 1000))
   
    # read files
    [colsA, recsA] = readCsvFile(pathToA, separator)
    [colsB, recsB] = readCsvFile(pathToB, separator)
    
    # check number of columns in the files
    if (len(colsA) != len(colsB)) :
        print '-- Error: number of columns not matching between files.'
        sys.exit()
        
    # check column names
    [res, col] = compare(colsA, target)
    if (res != 0) :
        print '-- Error: column ', col, ' not as required (', colsA[col], ' <> ', target[col], ')'
        sys.exit()

    # check column names
    [res, col] = compare(colsA, colsB)
    if (res != 0) :
        print '-- Error: column ', col, ' mismatch (', colsA[col], ' <> ', colsB[col], ')'
        sys.exit()

    # sort records by 1) table_owner, 2) table_name, 3) column_name
    recsA = sorted(recsA, key = lambda x : (x[0], x[1], x[2])) 
    recsB = sorted(recsB, key = lambda x : (x[0], x[1], x[2])) 

    # record level comparison (merge-sort-compare)
    row = 0
    rowA = 0
    rowsA = len(recsA)
    rowB = 0
    rowsB = len(recsB)
    missingA = 0
    missingB = 0
    differing = 0
    while not (rowA >= rowsA and rowB >= rowsB) :
        # current record from either data set
        recA = getCurrentRecord(rowA, rowsA, recsA)
        recB = getCurrentRecord(rowB, rowsB, recsB)
        # comparison
        [res, col] = compare(recA, recB)
        if (res == 0) :
            # records equal
            rowA += 1
            rowB += 1
        elif (res == -1) :
            if (col < 3) : # owner/table/column missing
                print 'Missing: ', pathToB, ' - ', (recA[0]+'.'+recA[1]+'.'+recA[2])
                missingB += 1
                rowA += 1
            else :         # metadata different
                print 'Differing: ', pathToB, ' - ', (recA[0]+'.'+recA[1]+'.'+recA[2]+' field '+ recA[col])
                differing += 1
                rowB += 1
                rowA += 1
        else : # (res == +1)
            if (col < 3) : # owner/table/column missing
                print 'Missing: ', pathToA, ' - ', (recB[0]+'.'+recB[1]+'.'+recB[2])
                missingA += 1
                rowB += 1
            else :         # metadata different
                print 'Differing: ', pathToA, ' - ', (recB[0]+'.'+recB[1]+'.'+recB[2]+' field '+ recB[col])
                differing += 1
                rowA += 1
                rowB += 1
        # next row
        row  += 1
        if (row >= (rowsA + rowsB)) : # safety - cannot be more that "union" # of records
            break;

    # print info
    end = int(round(time.time() * 1000))
    print '-- finished in ', (end-start), ' ms.'
    print '-- rowsA = ', rowsA, '; rowsB = ', rowsB, '; rows = ', row, '; missing in A = ', missingA, '; missing in B = ', missingB, '; differing = ', differing
