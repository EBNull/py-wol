import socket
import msvcrt

import ip
import irc_util
from irc_util import PrefixMessageFormat
from py_util import *
import channel
import user


import wol_logging
wol_logging.SetupLogging(wol_logging.DEBUG)

from listenthread import ListenThread

class WOLServer:
    def __init__(self):
        self.name = "PyWOL 0.3a"
        self.motd = """This is a nondescriptive MOTD."""
        self.hostname = "irc.westwood.com"
        try:
            self.ip = ip.get_external_ip()
        except ip.IPError, e:
            wol_logging.log(wol_logging.CRITICAL, "ip", e.error)
            raise e
        wol_logging.log(wol_logging.INFO, "ip", "Detected External IP as %s"% self.ip)
        self.users = user.User_Manager()
        chans = ("#Lob_18_0", #TS
                 "#Lob_33_0", #RA2
                 "#Lob_33_1", #RA2
                 "#Lob_33_2", #RA2
                 "#Lob_33_3", #RA2
                 "#Lob_40_0", #YR?
                 "#Lob_41_0", #YR
                 "#Lob_41_1", #YR
                 "#Lob_41_2", #YR
                 "#Lob_41_3"  #YR
                 )
        self.channels = channel.Channel_Manager()
        for name in chans:
            self.channels.CreateChannel(name)
        self.games = channel.Game_Manager()
        self.adminusername = "PyWOL_0.3"



#-----------------------------------------------------------------
#-----------------------------------------------------------------
#-----------------------------------------------------------------
if (__name__ == "__main__"):
    wol_logging.log(wol_logging.INFO, "", "PyWOL started")
    
    serv = WOLServer()

    accept_thread = ListenThread(serv)
    accept_thread.start()

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
        if k == 's':
            print "System Halted. Press enter to Finish."
            for u in serv.users.u:
                u.connection.Disconnect();
                accept_thread.halt();
            while halt == False:
                k = msvcrt.getch()
                if (k == chr(13)):
                    halt = True  

