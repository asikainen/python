#!/usr/bin/python

# Date:        2019-09-22
# Author:      Joonas Asikainen 
# Description: Convert Excel files in the given directory to CSV              
# Usage:       python file2ddl.py path/to/files

# Date:        2019-09-22
# Author:      Joonas Asikainen 
# Description: Read CSV/Excel files containing tabular data;
#              analyze content for each column and decide on
#              the data type; generate (PL*SQL) DDL script for
#              a table correspondign to the file; generate CTL file
#              for SQL Loader; generate a sh script with SQL Loader
#              commands.
# Usage:       python file2ddl.py path/to/files
#
# Notes:       Date types decided upon the hierarchy:
#              1. Date
#              2. Decimal/float (w/ precision)
#              3. Integer
#              4. Varchar (w/ width of the field)
#

# imports
import sys
import os
import re
import time
import csv
import math
from xlrd import open_workbook

### Parser base class ###
class Parser :

    ### constructor ###
    def __init__(self):
        self.patterns = []
        self.formats = []
        self.matches = []
        self.length = 0
        
    ### match date patterns
    def match(self, value) :
        idx = 0
        for pattern in self.patterns :
            if (pattern.match(value)) :
                if (len(value) > self.length) :
                    self.length = len(value)
                self.matches[idx] += 1 
                return True
            idx += 1
        return False

    ### return the list of formats
    def getFormat(self) :
        idx = self.getMatchIndex()
        if (idx < 0) :
            return None
        else :
            return self.formats[idx]

    ### return the match counts to formats
    def getMatch(self) :
        idx = self.getMatchIndex()
        if (idx < 0) :
            return None
        else :
            return self.matches[idx]
    
    ### return the max length of the matched strings
    def getLength(self) :
        return self.length
    
    ### return the index of the first matching pattern
    def getMatchIndex(self) :
        idx = -1
        for i in range(len(self.matches)) :
            if (self.matches[i] > 0) :
                idx = i
                break
        return idx

### Parser of date ###
class DateParser (Parser) :

    ### constructor ###
    def __init__(self):
        Parser.__init__(self)
        self.patterns.append(re.compile('^(\d{4})-(\d{2})-(\d{2})$'))
        self.patterns.append(re.compile('^(\d{4})/(\d{2})/(\d{2})$'))
        self.patterns.append(re.compile('^(\d{2})-(\d{2})-(\d{4})$'))
        self.patterns.append(re.compile('^(\d{2})/(\d{2})/(\d{4})$'))
        self.patterns.append(re.compile('^(\d{2})\.(\d{2})\.(\d{4})$'))

        self.formats.append('\'yyyy-mm-dd\'')
        self.formats.append('\'yyyy/mm/dd\'')
        self.formats.append('\'dd-mm-yyyy\'')
        self.formats.append('\'dd/mm/yyyy\'')
        self.formats.append('\'dd.mm.yyyy\'')

        self.matches.append(0)
        self.matches.append(0)
        self.matches.append(0)
        self.matches.append(0)
        self.matches.append(0)

### Parser of Decimal ###
class DecimalParser (Parser) :
    
    ### constructor ###
    def __init__(self):
        Parser.__init__(self)
        self.patterns.append(re.compile('^([-+])?(?:\d*\.\d+)|(?:\d+\.\d*?)$'))
        self.formats.append('number(38,14)')
        self.matches.append(0)

### Parser of Integer ###
class IntegerParser (Parser) :
    
    ### constructor ###
    def __init__(self):
        Parser.__init__(self)
        self.patterns.append(re.compile('^([-+]?)(\d+)$'))
        self.formats.append('integer')
        self.matches.append(0)

### Parser of Integer ###
class StringParser (Parser) :

    ### constructor ###
    def __init__(self):
        Parser.__init__(self)
        self.patterns.append(re.compile('^.*$'))
        self.formats.append('varchar')
        self.matches.append(0)
        
        
#### class for parsing data types ###
class DataTypeParser :

    ### constructor ###
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.parsers = []
        self.parsers.append(DateParser())
        self.parsers.append(DecimalParser())
        self.parsers.append(IntegerParser())
        self.parsers.append(StringParser())        
        self.types = ['Date','Number','Integer','Varchar']
        self.matches = [0,0,0,0]
        
    ### update for value ###
    def update(self, value) :
        p = 0
        for parser in self.parsers :
            if (parser.match(value)) :
                self.matches[p] += 1
                return p
            p += 1
        return -1

    ### get the id ###
    def getId(self) :
        return self.id
    
    ### get the current match (data type) ###
    def getDataType(self) :
        idx = self.getMatch()
        if (idx < 0) :
            return None
        else :
            return self.types[idx]

    ### get format ###
    def getFormat(self) :
        idx = self.getMatch()
        if (idx < 0) :
            return None
        else :
            return self.parsers[idx].getFormat()
    
    ### get the length ###
    def getLength(self) :
        idx = self.getMatch()
        if (idx < 0) :
            return None
        else :
            lngth = self.parsers[idx].getLength()
            return int(math.pow(2, (1 + math.floor(math.log(lngth, 2)))))
    
    ### get the matched parser - note: current implementation returns the first match in pattern ###
    ### hierarchy this can be replaced by a more complicated analysis (majority rule etc.) ###
    def getMatch(self) :
        idx = -1
        for i in range(len(self.matches)) :
            if (self.matches[i] > 0) :
                idx = i
                break
        return idx
    
    ### get id ###
    def getId(self) :
        return self.id
    
    ### get name  ###
    def getName(self) :
        return self.name

### class holiding file analysis result
class FileResult :

    ### constructor ###
    def __init__(self, fileName, columnNames, dataTypes, formats, lengths):
        self.id = id
        self.fileName = fileName
        self.columnNames = columnNames
        self.dataTypes = dataTypes
        self.formats = formats
        self.lengths = lengths

    ### get file name###
    def getFileName(self) :
        return self.fileName

    ### get column names ###
    def getColumnNames(self) :
        return self.columnNames
    
    ### get data types ###
    def getDataTypes(self) :
        return self.dataTypes

    ### get formats ###
    def getFormats(self) :
        return self.formats
    
    ### get lengths ###
    def getLengths(self) :
        return self.lengths

### generate DDL script for the table with the given columns/types ###
def generateDDL(schemaName, fullName, columnNames, dataTypes, lengths) :
    fileName, extension = os.path.splitext(fullName)
    cols = (len(columnNames))
    ddl = ''
    ddl += ('DROP TABLE ' + (schemaName + '.' + fileName)  + ';\n')
    ddl += ('CREATE TABLE ' + (schemaName + '.' + fileName)  + ' (\n')
    for col in range(cols):     
        ddl += ('\t' + columnNames[col] + "\t" + dataTypes[col])
        if (dataTypes[col] == "Varchar") :
            ddl += ('(' + str(lengths[col]) + ')')
        elif (dataTypes[col] == "Number") :
            ddl += ('(38,14)')
        if (col < cols - 1) :
            ddl += (',\n')
        else :
            ddl += ('\n')
    ddl += (');\n')
    return ddl

### generate CTL script for the table with the given columns/types ###
def generateCTL(path, fullName, schemaName, columnNames, dataTypes, formats) :
    fileName, extension = os.path.splitext(fullName)
    cols = (len(columnNames))
    ctl = ''
    ctl += ('options (skip=1)\n ')
    ctl += ('\tload data\n ')
    ctl += ('\tinfile \'' + path + '/' + fullName + '\'\n')
    ctl += ('\tappend into table ' + schemaName + '.' + fileName + '\n')
    ctl += ('\tfields terminated by \';\'\n')
    ctl += ('\ttrailing nullcols\n ')
    ctl += ('(\n')
    for col in range(cols):
        ctl += ('\t' + columnNames[col])
        if (dataTypes[col] == 'Date') :                      
            ctl += (' date ' + formats[col])
        if (col < cols - 1) :
            ctl += (',\n')
        else :
            ctl += ('\n')
    ctl += (')\n')
    return ctl

### generate CMD for SQL Loader ###
# loader command for remote database: sqlldr user/password@//server
# # sqlldr userid=dwh/havefun@XE control=./ctl/BETRIEBSPUNKT.ctl
def generateCMD(fullName, user, password, server, schema) :
    fileName, extension = os.path.splitext(fullName)

    cmd  = ''
    cmd += 'sqlldr userid=' + user + '/' + password +'@' + server
    cmd += ' control=./ctl/' + fileName + '.ctl '
#    cmd += ' log=./log/' + fileName + '.log '
#    cmd += ' bad=./bad/' + fileName + '.bad '
    
    return cmd

### read CSV and generate ddl ###
def analyzeFile(path, fullName) :
    print '-- reading file ', fullName, '; schema ', schema
    fileName, extension = os.path.splitext(fullName)
    if (extension.lower() != '.csv') :
        print '-- file extension ', extension, ' not supported.'
        return None

    # initialize parsers and analyse file
    parsers = []
    with open(path + '/' + fullName, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        row = 0
        skip = 0
        columnNames = []
        for record in csvreader :
            # header/column names
            if (row == 0) :
                col = 0
                for item in record :
                    columnNames.append(item)
                    parsers.append(DataTypeParser(col, item))
                    col += 1
            # data; check for bad/good
            if (len(columnNames) != len(record)) :
                print '-- skipping row ', row, '; not all records available!'
                skip += 1
            else :
                col = 0
                for item in record :
                    parsers[col].update(item)
                    col += 1
            # row count
            row += 1

        # extract data 
        dataTypes = []
        formats = []
        lengths = []
        for parser in parsers :
            dataTypes.append(parser.getDataType())
            formats.append(parser.getFormat())
            lengths.append(parser.getLength())

    # print info
    print '-- read ', row, ' rows total, skipped ', skip
    
    # done
    return FileResult(fullName, columnNames, dataTypes, formats, lengths)

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 7) :
        print '-- usage: file2ddl.py user password server schema path/to/input path/to/ddl path/to/ctl'
        sys.exit()
    print '-- file2ddl.py ', args

    # extract Excel files in the path
    user = args[0]
    password = args[1]
    server = args[2]
    schema = args[3]
    inputPath = args[4]
    ddlPath = args[5]
    ctlPath = args[6]

    # filter input files
    exts = ['csv'] ;
    fnames = [fn for fn in os.listdir(inputPath) \
              if any([fn.lower().endswith(ext) for ext in exts])];

    # timestamp
    strDateTime = time.strftime('%Y%m%d', time.localtime())
    
    # DDL script file
    ddlFile = open(ddlPath + '/' + schema + '_' + strDateTime + '.sql', 'w')
    
    # loader command file
    cmdFile = open(schema + '_' + strDateTime + '.sh', 'w')
        
    # convert all files
    start = int(round(time.time() * 1000))
    for fname in fnames :
        # analyse single file
        result = analyzeFile(inputPath, fname)
                
        # generate DDL
        ddl = generateDDL(schema, result.getFileName(), result.getColumnNames(), result.getDataTypes(), result.getLengths())
        ddlFile.write(ddl + '\n')

        # generate CTL
        ctl = generateCTL(inputPath, result.getFileName(), schema, result.getColumnNames(), result.getDataTypes(), result.getFormats())
        fileName, extension = os.path.splitext(result.getFileName())
        ctlFile = open(ctlPath + '/' + fileName + '.ctl', 'w')
        ctlFile.write(ctl + '\n')
        ctlFile.close()

        # generate CMD
        cmd = generateCMD(result.getFileName(), user, password, server, schema)
        cmdFile.write(cmd + '\n')

    # done
    ddlFile.close()
    cmdFile.close()
    
    # print info
    end = int(round(time.time() * 1000))
    print '-- processed ', len(fnames), ' files  in ', (end-start), ' ms.'

