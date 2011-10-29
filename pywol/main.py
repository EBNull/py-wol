import os, sys

import socket
import msvcrt

import wol_logging

from server.wolserver import WOLServer
from listenthread import ListenThread
    
def console_ui(serv, accept_thread):
    print "In console UI"
    halt = False
    while (halt == False):
        k = msvcrt.getch() #this line blocks, waiting for input
        if k == '0':
            debugs = db['all']
            print "Debug Level: All"
        if k == '1':
            debugs = db['common']
            print "Debug Level: common"
        if k == '9':
            debugs = db['raw']
            print "Debug Level: raw"
        if k == 'g':
            print "Running Games:"
            for g in serv.games.g:
                print "\t%s"%(repr(g))
        if k == 'u':
            print "Connected Users:"
            for u in serv.users.u:
                print "\t%s"%(repr(u))
        if k == 'b':
            for u in serv.users.u:
                u.connection.dumpbuf();
        if k in 'sq\x03':
            print "System Halted. Press enter to Finish."
            for u in serv.users.u:
                u.connection.Disconnect();
                accept_thread.halt();
            while halt == False:
                k = msvcrt.getch()
                if (k == chr(13)):
                    halt = True

def main(argv):
    wol_logging.SetupLogging(wol_logging.DEBUG)
    wol_logging.log(wol_logging.INFO, "", "PyWOL started")
    
    serv = WOLServer()

    accept_thread = ListenThread(serv)
    accept_thread.start()

    console_ui(serv, accept_thread)
    return 0
    
if __name__ == "__main__":
    sys.exit(main(sys.argv))