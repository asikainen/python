#!/usr/bin/python

# imports
import sys
import re
import math
import time
from datetime import datetime

### compute ISO week number
def getIsoWeekNumber(cdate) :
    cyea = cdate.year
    cdoy = cdate.timetuple().tm_yday
    cdow = cdate.isoweekday()
    cwkn = int((cdoy - cdow + 10.0)/7.0)
    
    pdate = datetime.strptime((str(cyea - 1)+'-12-28'), '%Y-%m-%d')
    pdoy = pdate.timetuple().tm_yday
    pdow = pdate.isoweekday()
    pwkn = int((pdoy - pdow + 10.0)/7.0)

    ndate = datetime.strptime((str(cyea)+'-12-28'), '%Y-%m-%d')
    ndoy = ndate.timetuple().tm_yday
    ndow = ndate.isoweekday()
    nwkn = int((ndoy - ndow + 10.0)/7.0)
    
    wkn = cwkn
    if (wkn < 1) :
        wkn = pwkn
    elif (wkn > nwkn) :
        wkn = 1

    return wkn

### main ###
if __name__ == '__main__':

    # check args
    args = sys.argv[1:] 
    nargs = len(args)
    if (nargs < 1) :
        print '-- usage: weeknumber.py days_since_1970 [\d{5}] OR date [yyyy-mm-dd]'
        sys.exit()

    MILLISECONDS_IN_DAY = int(1000 * 3600 * 24);
    inp = args[0]
    p1970 = re.compile('^(\d{5})$')    
    pdate = re.compile('^(\d{4})-(\d{2})-(\d{2})$')    

    cdate = datetime.fromtimestamp(time.time());
    if (p1970.match(inp)) :
        cdate = datetime.fromtimestamp(int(inp) * MILLISECONDS_IN_DAY / 1000.0)
    elif (pdate.match(inp)) :
        cdate = datetime.strptime(inp, '%Y-%m-%d')
    else :
        print '-- invalid input; accepted formats are [\d{5}] OR [yyyy-mm-dd]'
        sys.exit()

    wkn = getIsoWeekNumber(cdate)
    print '-- week number for date ', cdate, ' is ', wkn, '; w/ python datetime value is ', cdate.isocalendar()[1]
