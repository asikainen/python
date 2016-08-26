#!/usr/bin/python
#
# Date:         2019-09-22
# Author:       Joonas Asikainen
# Version:      v.1.0
# Description:  Read an Excel configuration file containing the concept (hubs), context (satellites),
#               relationsip (links) information; generate DDL for the corresponding Data Vault
# Usage:        python mkdv.py path/to/config
#

# imports
import sys
import os
import re
import time
import datetime
import csv
import math
from xlrd import open_workbook

"""
Begin the story.
"""

### Configuration
class Configuration :

    def __init__(self) :
        # code version
        self.version = 'v.1.0'
        # supported data types
        self.datatypes = ['char', 'varchar', 'text',
            'date', 'time', 'datetime', 'timestamp',
            'bigint', 'int', 'mediumint', 'smallint', 'tinyint', 'boolean', 'decimal', 'float', 'double']
        # structure of the hub (concept) input data
        self.hubStructure = ['Concept']
        # structure of the link (relation) input data
        self.lnkStructure = ['Relation', 'Concept']
        # structure of the satellite (context) input data
        self.satStructure = ['Concept', 'Context', 'Attribute', 'Datatype', 'Length', 'Precision', 'Nullable']

### Column
class Column:
    
    def __init__(self, name, datatype, length = None, precision = None, nullable = False, primary = False, unique = False) :
        # assign members
        self.name = name
        self.datatype = datatype
        self.length = getInt(length)
        self.precision = getInt(precision)
        self.primary = getBool(primary)
        self.unique = getBool(unique)
        self.nullable = getBool(nullable)
                
    def toString(self) :
        return (self.name + ', ' + self.datatype + ', ' + str(self.length) + ', ' + str(self.precision) + ', ' + str(self.primary) + ', ' + str(self.unique) + ', ' + str(self.nullable))
    
    def toCreateSQL(self) :
        sql = '\t' + self.name
        sql += ' ' + self.datatype
        if (self.length > 0 and self.precision > 0) :
            sql += ' (' + str(self.length) + ', ' + str(self.precision) + ') '    
        if (self.length > 0 and self.precision == 0) :
            sql += ' (' + str(self.length) + ') '    
        if (self.nullable == False) :
            sql += ' not null'
        else :
            sql += ' null'
        return sql

### Table base class
class Table :
    
    def __init__(self, name, kind = None, schema = None) :
        self.name = getTableName(name, kind)
        self.schema = schema
        self.columns = []
        
    def add(self, columnname, datatype, length = None, precision = None, nullable = False, primary = False, unique = False) :
        column = Column(columnname, datatype, length, precision, nullable, primary, unique)
        if ('_SK' in columnname) :
            self.columns.insert(0, column)
        else :
            self.columns.append(column)
        
    def toString(self) :
        tostr =  self.name + '\n'
        for column in self.columns :
            tostr += column.toString() + '\n'
        return tostr
    
    def toPrimaryKey(self) :
        sql = '\tconstraint PK_' + self.name
        sql += ' primary key ('
        cols = []
        for col in self.columns :
            if (col.primary) :
                cols.append(col.name)
        imax = len(cols)
        if (imax == 0) :
            return None
        for i in range(imax) :
            sql += cols[i]
            if (i < imax - 1) :
                sql += ', '
        sql += ')'
        return sql
    
    def toUnique(self) :
        sql = '\tconstraint UC_' + self.name
        sql += ' unique ('
        cols = []
        for col in self.columns :
            if (col.unique) :
                cols.append(col.name)
        imax = len(cols)
        if (imax == 0) :
            return None
        for i in range(imax) :
            sql += cols[i]
            if (i < imax - 1) :
                sql += ', '
        sql += ')'
        return sql
    
    def toDropSQL(self) :
        sql = 'drop table if exists '
        if (self.schema <> None) :
            sql += self.schema + '.'
        sql += self.name         
        sql += ';\n'
        return sql

    def toCreateSQL(self) :
        # create table statement
        sql = 'create table '
        if (self.schema <> None) :
            sql += self.schema + '.'
        sql += self.name + ' (\n'
        
        # constraints
        pk = self.toPrimaryKey()
        uq = self.toUnique()
        
        # list of columns
        imax = len(self.columns)
        for i in range(imax) :
            col = self.columns[i]
            sql += col.toCreateSQL()
            if (i < imax - 1) :
                sql += ', '
            elif ((i == imax - 1) and (pk != None or uq != None)) :
                sql += ', '
            sql += '\n'

        if (pk != None) :
            sql += pk
            if (uq != None) :
                sql += ','
            sql += '\n'
        if (uq != None) :
            sql += uq
            sql += '\n'
        
        sql += ');\n'
        return sql

### Hub table extension
class HubTable  (Table) :
        def __init__(self, name) :
            if ('Hub_' in name) :
                name = name.replace('Hub_', '')
            Table.__init__(self, name, 'hub')
            hubKey = (name + '_SK')
            self.add(hubKey, 'varchar', 64, None, False, True, False)
            self.add((name + '_BK'), 'varchar', 128, None, False, False, True)
            self.add('LoadDateTime', 'datetime', None, None, False, False, False)
            self.add('RecordSource', 'varchar', 32, None, False, False, False)

### Link table extension
class LinkTable  (Table) :
        def __init__(self, name) :
            if ('Lnk_' in name) :
                name = name.replace('Lnk_', '')
            Table.__init__(self, name, 'link')
            self.add('LoadDateTime', 'datetime', None, None, False, False, False)
            self.add('RecordSource', 'varchar', 32, None, False, False, False)
            
### Satellite table extension
class SatelliteTable  (Table) :
        def __init__(self, name, hubname = None) :
            if ('Sat_' in name) :
                name = name.replace('Sat_', '')
            if (hubname == None) :
                hubname = getTableName(name, 'hub')
            Table.__init__(self, name, 'satellite')
            hubKey = (hubname + '_SK')
            self.add(hubKey, 'varchar', 64, None, False, True, False)
            self.add('LoadDateTime', 'datetime', None, None, False, True, False)
            self.add('RecordSource', 'varchar', 32, None, False, False, False)
            self.add('IsDeleted', 'boolean')
            self.add('ContentHash', 'varchar', 32, None, False, False, False)

### get int with a default
def getInt(entry, default = 0) :
    if (entry == None) :
        return default
    try: 
        return int(entry)
    except ValueError:
        return default

### get int with a default
def getBool(entry, default = False) :
    if (entry == None) :
        return default
    try: 
        return bool(entry)
    except ValueError:
        return default

### get int with a default
def getFloat(entry, default = 0.0) :
    if (entry == None) :
        return default
    try: 
        return float(entry)
    except ValueError:
        return default

### check column name structure
def checkColumns(columnNames, expected) :
    col = 1
    for x, y in zip(columnNames, expected) :
        if (x != y) :
           return col
        col += 1
    return 0

### get table name based on type
def getTableName(name, kind = None) :
    if (kind.lower() == 'hub') :
        return 'Hub_' + name[0].upper() + name[1:].lower()
    if (kind.lower() == 'link') :
        return 'Lnk_' + name[0].upper() + name[1:].lower()
    if (kind.lower() == 'satellite') :
        return 'Sat_' + name[0].upper() + name[1:].lower()
    else :
        return name[0].upper() + name[1:].lower()

### read the given columns in the Excel sheet
def readColumnsFromExcel(fullname, sheetname, columns) :
    data = []
    
    filename, extension = os.path.splitext(fullname)   
    print '-- file name = ', fullname
    
    # open sheet.
    book = open_workbook(fullname)
    sh = book.sheet_by_name(sheetname)
    if (sh == None) :
        print '-- sheet ', sheetname, ' not found, exiting...'
        return data
    
    print '-- sheet name = ', sh.name

    # extract data and write to CSV
    start = int(round(time.time() * 1000))
    print '-- reading file ', fullname, ' sheet ', sh.name, '.'
    cols = [-1] * len(columns)
    for row in range(sh.nrows) :
        if (row == 0) :
            idx = 0
            for col in range(sh.ncols) :
                value  = (sh.cell(row, col).value)
                if (value.lower() == columns[idx].lower()) :
                    cols[idx] = col
                    idx += 1
            for col in cols :
                if col < 0 :
                    print '-- could not find the specified columns; expected = ', columns
                    return data
            else :
                print '-- column indexes = ', cols
        else :
            record = []
            for col in cols :
                record.append(sh.cell(row, col).value)
            data.append(record)
        if (row > 0 and row % 10000 == 0) :
            end = int(round(time.time() * 1000))
            print '-- processed ', row, ' in ', (end-start), ' ms.'
    end = int(round(time.time() * 1000))
    print '-- read ', row, ' rows in ', (end-start), ' ms.'
    return data

### run info
def printInfo(configuration, sheets, version) :
    now = datetime.datetime.now()
    print '-- mkdv.py - welcome! '
    print '--   code version    = ', version
    print '--   run date        = ', now.isoformat()
    print '--   excel file      = ', excel
    print '--   concept sheet   = ', sheets[0]
    print '--   context sheet   = ', sheets[1]
    print '--   relation sheet  = ', sheets[2]

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 1) :
        print '-- usage: mkdv.py path/to/configuration [[[concept] [context]] [relation]'
        sys.exit()

    # parameters
    excel = args[0]
    sheets = ['concept','context','relation']
    if (nargs > 1) :
        sheets[0] =args[1]
    if (nargs > 2) :
        sheets[1] =args[2]
    if (nargs > 3) :
        sheets[2] =args[3]

    # print info
    cfg = Configuration()
    printInfo(excel, sheets, cfg.version)

    # read data
    start = int(round(time.time() * 1000))
    print '-- start reading data...'
    hubs = readColumnsFromExcel(excel, sheets[0], cfg.hubStructure)
    sats = readColumnsFromExcel(excel, sheets[1], cfg.satStructure)
    lnks = readColumnsFromExcel(excel, sheets[2], cfg.lnkStructure)
    end = int(round(time.time() * 1000))
    print '-- finished  in ', (end-start), ' ms.'

    # print data as read    
    # print '-- hubs = ', hubs
    # print '-- lnks = ', lnks
    # print '-- sats = ', sats
    
    # generate table objects
    print '-- start generating table objects...'
    start = int(round(time.time() * 1000))

    # generate hubs
    chk = {}
    for hub in hubs :
        key = getTableName(hub[0], 'hub')
        if (key not in chk) :
            tbl = HubTable(key)
            chk[key] = tbl
            
    # generate links
    for lnk in lnks :
        key = getTableName(lnk[0], 'link')
        tbl = None
        if (key not in chk) :
            tbl = LinkTable(lnk[0])
            chk[key] = tbl
        else :
            tbl = chk[key]
        hubKey = lnk[1]+'_SK'
        tbl.add(hubKey,'varchar',64,None,False,True,True)

    # generate satellites
    for sat in sats :
        key = getTableName(sat[1], 'satellite')
        tbl = None
        if (key not in chk) :
            tbl = SatelliteTable(sat[1], sat[0])
            chk[key] = tbl
        else :
            tbl = chk[key]
        tbl.add(sat[2],sat[3],sat[4],sat[5],sat[6])

    # print drop DDL's
    keys = chk.keys()
    keys = sorted(keys)
    for key in keys :
        print chk[key].toDropSQL()

    # print create DDL's
    for key in keys:
        print chk[key].toCreateSQL()

    # timestamp
    strDateTime = time.strftime('%Y%m%d', time.localtime())
        
    # print info
    end = int(round(time.time() * 1000))
    print '-- finished  in ', (end-start), ' ms.'

"""
End of story.
"""
