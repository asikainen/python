#!/usr/bin/python

# imports
import sys
import re
import math
import time
from datetime import datetime

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 1) :
        print '-- usage: todate.py days_since_1970 [\d{5}] OR date [yyyy-mm-dd]'
        sys.exit()

    MILLISECONDS_IN_DAY = (1000 * 3600 * 24);
    inp = args[0]
    p1970 = re.compile('^(\d{5})$')    
    pdate = re.compile('^(\d{4})-(\d{2})-(\d{2})$')    

    if (p1970.match(inp)) :
        #print '--converting', inp, ' to date...'
        out = datetime.fromtimestamp(int(inp) * MILLISECONDS_IN_DAY / 1000.0)
        print '-- days since 1970 ', inp, '; date ', out
    elif (pdate.match(inp)) :
        #print '--converting', inp, ' to days since 1970...'
        dt = datetime.strptime(inp, '%Y-%m-%d')
        #print dt, time.mktime(dt.timetuple())
        t = time.mktime(dt.timetuple())
        out = int(math.floor(t * 1000/MILLISECONDS_IN_DAY + 1))
        print '-- date ', inp, '; days since 1970 ', out
    else :
        print '-- invalid input; accepted formats are [\d{5}] OR [yyyy-mm-dd]'
