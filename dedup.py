#!/usr/bin/env python

# Date:        2014-09-04
# Author:      Joonas Asikainen 
# Description: scripting of DB duplicate cleanup

#####
import sys
import math
import numpy

###
# low level processing
#

# select list for multi-column ID
def toSelectList(tableIdString) :

    tableIds = tableIdString.strip().split(',')
    imax = len(tableIds)
    selectList = ''
    for i in range(imax):
        tableId = tableIds[i].strip()
        selectList = selectList + ('a.' + tableId)
        if (i < imax-1) :
            selectList = selectList + (', ')

    return selectList

# join AND join list on multi-column ID
def toJoinAndList(tableIdString) :
    
    tableIds = tableIdString.strip().split(',')
    imax = len(tableIds)
    joinList = ''
    for i in range(imax):
        tableId = tableIds[i].strip()
        joinList = joinList + ('a.' + tableId + ' = d.' + tableId)
        if (i < imax-1) :
            joinList = joinList + (' and ')

    return joinList

# batch preparation; note that for SIQ, the table prefixes are pruned
def getBatch(dbms, args) :

    # extract table, business key column(s) and the dependent tables (if any)
    table = args[0]
    tableId = args[1]
    i=2
    while not (args[i].endswith('_SK')) :
        tableId = tableId + (', ' + args[i])
        i = i + 1
    tableSk = args[i]
    dependents = args[i+1:]

    selectList = toSelectList(tableId)
    joinList = toJoinAndList(tableId)
 #   print joinList

    # prefix pruninn
    if (dbms == 'siq') :
        # dimension and fact tables (adjust if needed)
        if (table[:2] in ('D_','F_')) :
            table = table[2:]
        for i in range(len(dependents)):
            dependent = dependents[i]
            # dimension and fact tables (adjust if needed)
            if (dependent[:2] in ('D_','F_')) :
                dependents[i] = dependent[2:]

    # set up batch
    batch = []
    batch.append(table)
    batch.append(tableId)
    batch.append(tableSk)
    for dependent in dependents:
        batch.append(dependent)
    return batch

# count SQL generator
def sqlCountDuplicates (table, tableId, tableSK) :

    sql =       ('-- count duplicates in ' + table)
    sql = sql + ('select count(*) cnt_dupes from (' + '\n')
    sql = sql + ('   select ' + tableId + ', max(' + tableSk + ') keeper_sk' + '\n')
    sql = sql + ('   from ' + table + ' a' + '\n')
    sql = sql + ('   group by ' + tableId + '\n')
    sql = sql + ('   having count(*) > 1 '  + '\n')
    sql = sql + (') sub;' + '\n')

    return sql

# identify SQL generator
def sqlIdentifyDuplicates (table, tableId, tableSk) :

    sql =       ('drop table if exists dup_' + table +';' + '\n')
    sql = sql + ('select ' + toSelectList(tableId) + ', a.' + tableSk + ', d.keeper_sk' + '\n')
    sql = sql + ('into dup_' + table + '\n')
    sql = sql + ('from ' + table + ' a' + '\n')
    sql = sql + ('inner join (' + '\n')
    sql = sql + ('   select ' + tableId + ', max(' + tableSk + ') keeper_sk' + '\n')
    sql = sql + ('   from ' + table + ' a' + '\n')
    sql = sql + ('   group by ' + tableId + '\n')
    sql = sql + ('   having count(*) > 1 '  + '\n')
    sql = sql + (') d' + '\n')
    sql = sql + ('on ' + toJoinAndList(tableId) + '\n')
    sql = sql + ('where a.' + tableSk + ' <> d.keeper_sk' + '\n')
    sql = sql + ('; ' + '\n')

    return sql


# identify SQL generator for Oracle
def sqlIdentifyDuplicatesOracle (table, tableId, tableSk) :

    sql =       ('-- drop table dup_' + table + '\n')
    sql = sql + ('drop table dup_' + table +';' + '\n')
    sql = sql + ('create table dup_' + table + ' as (' + '\n')
    sql = sql + ('   select ' + toSelectList(tableId) + ', a.' + tableSk + ', d.keeper_sk' + '\n')
    sql = sql + ('   from ' + table + ' a' + '\n')
    sql = sql + ('   inner join (' + '\n')
    sql = sql + ('      select ' + tableId + ', max(' + tableSk + ') keeper_sk' + '\n')
    sql = sql + ('      from ' + table + ' a' + '\n')
    sql = sql + ('      group by ' + tableId + '\n')
    sql = sql + ('      having count(*) > 1 '  + '\n')
    sql = sql + ('   ) d' + '\n')
    sql = sql + ('   on ' + toJoinAndList(tableId) + '\n')
    sql = sql + ('   where a.' + tableSk + ' <> d.keeper_sk ' + '\n')
    sql = sql + ('); ' + '\n')
    
    return sql

# duplicates backup
def sqlBackupDuplicates(table, tableId, tableSk, dependent, chkmap) :

    bcktbl = (('bck_'+dependent)[0:27]+str(len(chkmap)))              
    chkmap[bcktbl] = len(chkmap)

    sql =       ('-- backup duplictates from dup_' + dependent +';' + '\n')
    sql = sql + ('drop table if exists '+ bcktbl+ ';' + '\n')
    sql = sql + ('select a.*' + '\n')
    sql = sql + ('into ' + bcktbl + '\n')
    sql = sql + ('from ' + dependent + ' a' + '\n')
    sql = sql + ('inner join dup_' + table + ' d' + '\n')
    sql = sql + ('on (a.' + tableSk + ' = d.' + tableSk + ');' + '\n')
    sql = sql + ('' + '\n')
    
    return sql

# duplicates backup for Oracle
def sqlBackupDuplicatesOracle(table, tableId, tableSk, dependent, chkmap) :

    bcktbl = (('bck_'+dependent)[0:27]+str(len(chkmap)))              
    chkmap[bcktbl] = len(chkmap)

    sql =       ('-- backup duplictates from dup_' + dependent +';' + '\n')
    sql = sql + ('drop table ' + bcktbl +';' + '\n')
    sql = sql + ('create table ' + bcktbl + ' as (' + '\n')
    sql = sql + ('   select a.*' + '\n')
    sql = sql + ('   from ' + dependent + ' a' + '\n')
    sql = sql + ('   inner join dup_' + table + ' d' + '\n')
    sql = sql + ('   on (a.' + tableSk + ' = d.' + tableSk + ') ' + '\n')
    sql = sql + (');' + '\n')
    
    return sql

# delete SQL generator
def sqlDeleteDuplicates(table, tableId, tableSk) :

    sql = ('-- delete duplicates from ' + table + '\n');
    sql = sql + ('delete from ' + table + '\n')
    sql = sql + ('where ' + tableSk + ' in (' + '\n')
    sql = sql + ('   select ' + tableSk + '\n')
    sql = sql + ('   from dup_' + table + '\n')
    sql = sql + (');' + '\n')

    return sql

# delete SQL generator for Oracle
def sqlDeleteDuplicatesOracle(table, tableId, tableSk) :

    sql = ('-- delete duplicates from ' + table + '\n');
    sql = sql + ('delete from ' + table + '\n')
    sql = sql + ('where ' + tableSk + ' in (' + '\n')
    sql = sql + ('   select ' + tableSk + '\n')
    sql = sql + ('   from dup_' + table + '\n')
    sql = sql + (');' + '\n')

    return sql

# delete SQL generator for Oracle
def sqlDeleteDuplicatesLogicalOracle(table, tableId, tableSk) :

    sql = ('-- delete (logical) duplicates from ' + table + '\n');
    sql = sql + ('update ' + table + '\n')
    sql = sql + ('set ' + tableId + ' = -' + tableId + ', ' + '\n')
    sql = sql + ('   change_action = ''U''' + '\n')
    sql = sql + ('from ' + table + ' trg' + '\n')
    sql = sql + ('join dup_' + table + ' src ' + '\n')
    sql = sql + ('on trg.' + tableSk + ' = src.' + tableSk + ';' + '\n')

    return sql

# update SQL generator
def sqlUpdateDuplicates(table, tableId, tableSk, dependent) :
    
    sql =       ('-- deduplicate ' + table + ' - ' + dependent + '\n');
    sql = sql + ('update ' + dependent + '\n')
    sql = sql + ('set ' + tableSk + ' = src.keeper_sk' + '\n')
    sql = sql + ('from ' + dependent + ' trg' + '\n')
    sql = sql + ('join dup_' + table + ' src ' + '\n')
    sql = sql + ('on trg.' + tableSk + ' = src.' + tableSk + ';' + '\n')

    return sql

# update SQL generator
def sqlUpdateDuplicatesOracle(table, tableId, tableSk, dependent) :
    
    dependentSk = (dependent[2:]+'_SK')

    sql =       ('-- deduplicate ' + table + ' - ' + dependent + '\n');
    sql = sql + ('merge into ' + dependent + ' trg '+ '\n')
    sql = sql + ('using (' + '\n')
    sql = sql + ('   select a.' + dependentSk + ',' +  '\n') 
    sql = sql + ('      b.'+ tableSk + ','  + '\n')
    sql = sql + ('      b.keeper_sk ' + '\n')
    sql = sql + ('   from ' + dependent + ' a' + '\n')
    sql = sql + ('   join dup_' + table + ' b ' + '\n')
    sql = sql + ('   on a.' + tableSk + ' = b.' + tableSk + '\n')
    sql = sql + (')  src ' + '\n')
    sql = sql + ('on (trg.' + dependentSk + ' = src.' + dependentSk + ')' + '\n')
    sql = sql + ('when matched then ' + '\n')
    sql = sql + ('update set trg.' + tableSk + ' = src.keeper_sk,' + '\n')
    sql = sql + ('   is_processed = 0,' + '\n')
    sql = sql + ('   change_action = ' + ("""'U'""") +';' + '\n')

    return sql

####
# high level processing
#


# identify duplicates
def identify(dbms, args) :

    # extract parameters
    table = args[0]
    tableId = args[1]
    tableSk = args[2]
    dependents = args[3:]

    # info
    print '-- target: ', table, '; dependents: ', dependents
    print ''

    # identification of duplicates
    if (dbms == 'ora') :
        print sqlIdentifyDuplicatesOracle(table, tableId, tableSk)
    elif (dbms == 'siq') :
        print sqlIdentifyDuplicates(table, tableId, tableSk)

# backup duplicated records
def backup(dbms, args, chkmap) :
    # extract parameters
    table = args[0]
    tableId = args[1]
    tableSk = args[2]
    dependents = args[3:]

    # backup
    if (dbms == 'ora') :
        print sqlBackupDuplicatesOracle(table, tableId, tableSk, table, chkmap)
        for dependent in dependents :
            print sqlBackupDuplicatesOracle(
                table, tableId, tableSk, dependent, chkmap)
    elif (dbms == 'siq') :                    
        print sqlBackupDuplicates(table, tableId, tableSk, table, chkmap)
        for dependent in dependents :
            print sqlBackupDuplicates(
                table, tableId, tableSk, dependent, chkmap)
        
# update
def update(dbms, args) :
    # extract parameters
    table = args[0]
    tableId = args[1]
    tableSk = args[2]
    dependents = args[3:]

    # update - update runs only in the dependent tables
    if (dbms == 'ora') :
        for dependent in dependents :
            print sqlUpdateDuplicatesOracle(table, tableId, tableSk, dependent)
    elif (dbms == 'siq') :
        for dependent in dependents :
            print sqlUpdateDuplicates(table, tableId, tableSk, dependent)

# delete duplicates in the "root" table
def delete(dbms, args) :
    # extract parameters
    table = args[0]
    tableId = args[1]
    tableSk = args[2]
    dependents = args[3:]

    # deletion of duplicates in the target table
    if (dbms == 'ora') :
        print sqlDeleteDuplicatesOracle(table, tableId, tableSk)
    elif (dbms == 'siq') :
        print sqlDeleteDuplicates(table, tableId, tableSk)


### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 2) :
        print '-- usage: dedup.py dbms input_file'
        print '--    supported values for dbms: siq/ora'
        print '--    input file to be filled with 01_input.sql output'
        sys.exit()

    # info
    print '-- dedup.py:', args
    print ''

    # extract DBMS
    dbms = args[0]
    if dbms not in ('siq','ora') :
        print '-- invalid DBMS (', dbms, ' )'
        sys.exit(1) 
       
    # extract batches
    fn = args[1]
    f = open(fn, 'r')
    batches = []
    for line in f :
        print '-- input line:', line.strip()
        batch = getBatch(dbms, line.strip().split(','))
        batches.append(batch)
    f.close()
    print

    # dbg kill switch for batch preparation
#    if dbms in ('siq','ora') :
#        sys.exit(1) 

    # identify duplicates
    for batch in batches :
        identify(dbms, batch)

    # backup duplicated records
    chkmap = {}
    for batch in batches :
        backup(dbms, batch, chkmap)

    # re-link duplicates
    for batch in batches :
        update(dbms, batch)

    # delete
    for batch in batches :
        delete(dbms, batch)
