#!/usr/bin/python

# Date:         2016-09-01
#
# Author:       Joonas Asikainen
#
# Description:  Read CSV/Excel files containing tabular data;
#               analyze content for each column and decide on
#               the data type; generate (MySQL) DDL script for
#               a table correspondign to the file; generate (MySQL) 
#               bulk load script for the CSV files.
#
# Usage:        python csv2sql.py schema path/to/csv path/to/ddl path/to/dml [sample]'
#                   - schema = database schema
#                   - path/to/csv = local path to folder containing input CSV files
#                   - path/to/ddl = local path to folder where the create table scripts are written
#                   - path/to/ddl = local path to folder where the load table scripts are written
#                   - sample = optional parameter to use the indicated number of rows for data type detection
#
#                E.g. python csv2sql.py sip ./csv/ ./ddl/ ./dml/ 1000
#
# Notes:        Date types decided upon the hierarchy:
#                   1. Date
#                   2. Decimal/float (w/ precision)
#                   3. Integer
#                   4. Varchar (w/ width of the field)
#

# imports
import sys
import os
import re
import time
import csv
import math

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
        self.formats.append('decimal(38,14)')
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
        self.types = ['Date','Decimal','Integer','Varchar']
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
    def __init__(self, fileName, columnNames, dataTypes, formats, lengths, delimiter):
        self.id = id
        self.fileName = fileName
        self.columnNames = columnNames
        self.dataTypes = dataTypes
        self.formats = formats
        self.lengths = lengths
        self.delimiter = delimiter

    ### get file name 
    def getFileName(self) :
        return self.fileName

    ### get column names 
    def getColumnNames(self) :
        return self.columnNames
    
    ### get data types 
    def getDataTypes(self) :
        return self.dataTypes

    ### get formats 
    def getFormats(self) :
        return self.formats
    
    ### get lengths 
    def getLengths(self) :
        return self.lengths
    
    ### get delimiter 
    def getDelimiter(self) :
        return self.delimiter

### generate DDL script for the table with the given columns/types ###
def generateDDL(schemaName, fullName, columnNames, dataTypes, lengths) :
    fileName, extension = os.path.splitext(fullName)
    cols = (len(columnNames))
    ddl = ''
    ddl += ('DROP TABLE IF EXISTS `' + (schemaName + '`.`' + fileName)  + '`;\n')
    ddl += ('CREATE TABLE `' + (schemaName + '`.`' + fileName)  + '` (\n')
    for col in range(cols):     
        ddl += ('\t`' + columnNames[col] + '`\t' + dataTypes[col])
        if (dataTypes[col] == 'Varchar') :
            ddl += ('(' + str(lengths[col]) + ')')
        elif (dataTypes[col] == 'Decimal') :
            ddl += ('(38,12)')
        if (col < cols - 1) :
            ddl += (',\n')
        else :
            ddl += ('\n')
    ddl += (');\n')
    return ddl

### generate CTL script for the table with the given columns/types ###
def generateDML(path, fullName, schemaName, columnNames, dataTypes, formats, delimiter) :
    fileName, extension = os.path.splitext(fullName)
    cols = (len(columnNames))
    ctl = ''
    ctl += ('LOAD DATA LOCAL INFILE\n')
    ctl += ('\t\'' + path + '' + fullName + '\'\n')
    ctl += ('INTO TABLE `' + schemaName + '`.`' + fileName + '`\n')
    ctl += ('\tFIELDS TERMINATED BY \'' + delimiter + '\'\n')
    ctl += ('\tOPTIONALLY ENCLOSED BY \'"\'\n')
    ctl += ('\tLINES TERMINATED BY \'\\n\'\n')
    ctl += ('IGNORE 1 LINES;\n')
    return ctl

### read CSV and generate ddl ###
def analyzeFile(path, fullName, sample = 0) :
    print '-- reading file ', fullName, '; schema ', schema
    fileName, extension = os.path.splitext(fullName)
    if (extension.lower() != '.csv') :
        print '-- file extension ', extension, ' not supported.'
        return None

    sniffer = csv.Sniffer()
    sf = open(path + '/' + fullName, 'rb')
    ln = sf.readline().strip()
    dm = sniffer.sniff(ln).delimiter
    if (dm == None) :
        print '-- could not extract delimiter - exiting...'
        return None

    # initialize parsers and analyse file
    parsers = []
    with open(path + '/' + fullName, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=dm, quotechar='"')
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
            if (sample > 0 and row > sample) :
                break

        # extract data 
        dataTypes = []
        formats = []
        lengths = []
        for parser in parsers :
            dataTypes.append(parser.getDataType())
            formats.append(parser.getFormat())
            lengths.append(parser.getLength())

    # print info
    print '-- read ', row, ' rows total, skipped ', skip,
    if (sample > 0) :
        print ', using sample size ', sample,
    print ''
    
    # done
    return FileResult(fullName, columnNames, dataTypes, formats, lengths, dm)

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 5) :
        print '-- usage: csv2sql.py schema path/to/csv path/to/ddl path/to/dml path/to/load [sample]'
        sys.exit()
    print '-- csv2sql.py ', args

    # extract Excel files in the path
    schema = args[0]
    loadPath = args[1]
    inputPath = args[2]
    ddlPath = args[3]
    dmlPath = args[4]
    sample = 0
    if (nargs > 5) :
        sample = int(args[5])

    # filter input files
    exts = ['csv'] ;
    fnames = [fn for fn in os.listdir(inputPath) \
              if any([fn.lower().endswith(ext) for ext in exts])];

    # timestamp
    strDateTime = time.strftime('%Y%m%d', time.localtime())
    
    # DDL script file
    ddlFile = open(ddlPath + '/ddl_' + strDateTime + '.sql', 'w')

    # DML script file
    dmlFile = open(dmlPath + '/dml_' + strDateTime +  '.sql', 'w')
            
    # convert all files
    start = int(round(time.time() * 1000))
    for fname in fnames :
        # analyse single file
        result = analyzeFile(inputPath, fname, sample)
        if (result == None) :
            continue
                
        # generate DDL
        ddl = generateDDL(schema, result.getFileName(), result.getColumnNames(), result.getDataTypes(), result.getLengths())
        ddlFile.write(ddl + '\n')

        # generate DML
        ctl = generateDML(loadPath, result.getFileName(), schema, result.getColumnNames(), result.getDataTypes(), result.getFormats(), result.getDelimiter())
        dmlFile.write(ctl + '\n')

    # done
    ddlFile.close()
    dmlFile.close()
    
    # print info
    end = int(round(time.time() * 1000))
    print '-- processed ', len(fnames), ' files  in ', (end-start), ' ms.'

