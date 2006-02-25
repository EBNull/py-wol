import logging
from logging import INFO, DEBUG, WARNING, ERROR, CRITICAL
#Levels
#CRITICAL 50
#ERROR	  40
#WARNING  30
#INFO     20
#DEBUG	  10

def SetupLogging(console_level, file_level=1):
    logging.basicConfig(level=file_level,
                    format='%(asctime)s %(name)-14s: %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='PyWOL_log.txt',
                    filemode='w')

    console = logging.StreamHandler()
    console.setLevel(console_level)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-14s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

import inspect
def linehere(framesback=1):
    """Give linenumer, file, and functionname of the callers,        
    caller.. Uses the standard module inspect
    """
    fr = inspect.currentframe()
    for i in range(0, framesback):
        fr = fr.f_back
    info = inspect.getframeinfo(fr)[0:3]
    printInfo=[]
    # Break long filenames
    printInfo.append('\\'.join(info[0].split("\\")[-2:]))
    printInfo.extend(info[1:3])
    return '[%s @ %s in %r] '% tuple(printInfo)

def log(severity, cat, data, backs=2):
    #print "%s %s %s"%(severity, cat, data)
    if (cat == ""):
        the_log = logging.getLogger('pywol'+cat)
    else:
        the_log = logging.getLogger('pywol.'+cat)
    data = linehere(backs) + data
    the_log.log(severity, data)
    
def log_caller(*args, **kargs):
    kargs['backs'] = 4
    log(*args, **kargs)
