import socket
import msvcrt

import ip
import irc_util
from irc_util import PrefixMessageFormat
from py_util import *
import channel
import user
from select import select
from threading import Thread

import wol_logging
wol_logging.SetupLogging(1)

class WOL_Main_Connection(irc_util.Base_IRC_Connection):
    def __init__(self, *args):
        super(self.__class__,self).__init__(*args)
        self.server = None
    def set_server(self, serverinstance):
        self.server = serverinstance
    def get_function_matrix(self):
        return {
            'VERCHK': self.OnVerChk,
            'LOBCOUNT': self.OnLobCount,
            'WHERETO': self.OnWhereTo,
            'QUIT': self.OnQuit,
            'unknown': self.OnRecvUnknown
        }
    def OnVerChk(self, data):
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "602", ("Username", "Update record non-existant")))
    def OnLobCount(self, data):
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "610", ("Username", "1")))
    def OnWhereTo(self, data):
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "605", ("Username", "%s 4003 '0,1,2,3,4,5,6,7,8,9,10:%s' -8 36.1083 -115.0582"%(self.server.ip, "PyWOL WOL Server 0.01"))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "605", ("Username", "%s 4003 'Live chat server' -8 36.1083 -115.0582"%(self.server.ip))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "608", ("Username", "%s 4001 'Gameres server' -8 36.1083 -115.0582"%(self.server.ip))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "609", ("Username", "%s 4002 'Ladder server' -8 36.1083 -115.0582"%(self.server.ip))))
    def OnQuit(self, data):
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "607", ("Username", "goodbye")))
        self.halt()
        self._sock.close()
        pass
    
class WOL_Chat_Connection(irc_util.Base_IRC_Connection):
    #YR Initial connection:
    #    CVERS 11016 10496
    #    PASS supersecret
    #    NICK CBWhiz
    #    apgar akWcGcGk 0
    #    SERIAL 1337
    #    USER UserName HostName irc.westwood.com :RealName
    #    verchk 32512 720912
    #    SETOPT 17,33
    def TellClient(self, lines):
        lines = lines.split("\n")
        for l in lines:
            self.senddata(":%s!u@h PRIVMSG %s :%s\r\n"%(self.server.adminusername, self.user.GetName(), l))
    def __init__(self, *args):
        super(self.__class__,self).__init__(*args)
        self.server = None
        self.user = None
        self.didmotd = False
    def set_server(self, serverinstance):
        self.server = serverinstance
    def get_function_matrix(self):
        return {
            #login procedure
            'CVERS': self.OnIgnorableIRCLine,
            'PASS': self.OnPASS,
            'NICK': self.OnNick,
            'APGAR': self.OnIgnorableIRCLine,
            'SERIAL': self.OnIgnorableIRCLine,
            'USER': self.OnUser,
            'VERCHK': self.OnVerChk,
            'SETOPT': self.OnSetOpt,
            #behind-the-scenes stuff
            'SETCODEPAGE': self.OnSetCodePage,
            'GETCODEPAGE': self.OnGetCodePage,
            'SETLOCALE': self.OnSetLocale,
            'GETLOCALE': self.OnGetLocale,
            'SQUADINFO': self.OnSquadInfo,
            'GETBUDDY': self.OnGetBuddy,
            'FINDUSEREX': self.OnFindUserEx,
            #channels
            'LIST': self.OnList,
            'JOIN': self.OnJoin,
            'PART': self.OnPart,
            'QUIT': self.OnQuit,
            'PRIVMSG': self.OnPrivMsg,
            'PAGE': self.OnPage,
            #games
            'JOINGAME': self.OnJoinGame,
            'GAMEOPT': self.OnGameOpt,
            'TOPIC': self.OnTopic,
            
            'unknown': self.OnRecvUnknown
        }
    def OnIgnorableIRCLine(self, data):
        pass
    def OnPASS(self, data):
        pass
    def OnNick(self, data):
        self.user = self.server.users.CreateUser(data[1][1], self)
    def OnUser(self, data):
        #USER UserName HostName irc.westwood.com :RealName
        self.user.username = data[1][1]
        self.user.hostname = data[1][2]
        self.user.realname = data[1][4]
    def OnVerChk(self, data):
        self.senddata(": 379 u :none none none 1 32512 NONREQ\r\n")
        #: 379 u :none none none 1 32512 NONREQ
        #self.senddata(irc_util.PrefixMessageNoPostfixParamFormat(self.server.hostname, "602", (self.user.GetName(), "Update record non-existant")))

    def OnSetOpt(self, data):
        if self.didmotd == True:
            return
        self.didmotd = True
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "375", (self.user.name, "- Welcome to " + self.server.name)))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "372", (self.user.name, "- MOTD: " + self.server.motd)))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "376", (self.user.name, "- End of MOTD")))
        pass
    def OnGetCodePage(self, data):
        others = data[1][1:]
        others = [n+"`"+self.user.codepage for n in others] #TODO: This is broken. It needs to /not/ lie about the user's locales
        r_str = '`'.join(others)
        self.senddata(": 328 u " + r_str+"\r\n")
    def OnSetCodePage(self, data):
        self.user.codepage = data[1][1]
        #echo it back:
        #:irc.westwood.com 329 CBWhiz 1252
        self.senddata(": 329 u " + data[1][1] + "\r\n")
    def OnSetLocale(self, data):
        self.user.locale = data[1][1]
        self.senddata(": 310 u " + data[1][1] + "\r\n")
    def OnGetLocale(self, data):
        others = data[1][1:]
        others = [n+"`2" for n in others] #TODO: This is broken. It needs to /not/ lie about the user's locales
        r_str = '`'.join(others)
        #:irc.westwood.com 309 CBWhiz CBWhiz`2
        self.senddata(": 309 u " + r_str+"\r\n")
    def OnSquadInfo(self, data):
        #:irc.westwood.com 439 CBWhiz ID does not exist
        #: 358 u 12852`pwns`pwns`407688`1739712`-4262304`33`520408`540095032`0`0`0`0`x`x`x
        self.senddata(": 439\r\n") #439 = No Squad with that ID
        pass
    def OnGetBuddy(self, data):
        self.senddata(": 333 u\r\n")
        pass
    def OnQuit(self, data):
        self.user.LeaveChannel()
        self.user.LeaveGame()
        self.server.users.RemoveUser(self.user)
        self.user.connection = None
        self.user = None
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "607", ("Username", "goodbye")))
        self.halt()
        self._sock.close()
        pass
    def OnList(self, data):
        if data[1][1] == "0":
            self.OnListChannels(data)
        else:
            self.OnListGames(data)
    def OnPrivMsg(self, data):
        #To channel:
        #PRIVMSG #Lob_41_1 :this is text 
        #To user:
        #PRIVMSG CBWhiz :this is highlighted text  
        c = None
        if data[1][1][0] == "#": #message to channel /or game/
            special = self.CheckSpecialCommands(data)
            if special == True:
                return
            c = self.server.channels.FindChannel(data[1][1])
            if c == None:
                c = self.server.games.FindGame(data[1][1])
            if c == None:
                wol_logging.log(wol_logging.WARNING, "chan", "Channel message received, but %s not found! (%s: %s)"%(data[1][1], self.user.GetName(), data[1][2]))
                return
            for u in c.GetUsers():
                if u != self.user:
                    #this output is a total guess
                    self.senddata(":%s!u@h PRIVMSG %s :%s\r\n"%(self.user.GetName(), c.GetName(), data[1][2]))
        else: #message to user
            u = self.server.users.FindUser(data[1][1])
            if c == None:
                #should probably return some sort of error, or something
                pass
            else:
                u.connection.senddata(":%s!u@h PRIVMSG %s :%s\r\n"%(self.user.GetName(), data[1][1], data[1][2]))
    def CheckSpecialCommands(self, data):
        cmdstr = data[1][2]
        try:
            if cmdstr[0] == "/":
                params = cmdstr.split(" ")
                params[0] = params[0][1:].upper()
                self.TellClient(repr(params))
                if params[0] == "KILL":
                    un = params[1]
                    u = self.server.users.FindUser(un)
                    if u != None:
                        u.connection.senddata(": 398 u 0:#byebye,0\r\n")
                    else:
                        self.TellClient("%s not found."%(un))
                if params[0] == "W":
                    u = params[1]
                    t = params[2:]
                    self.OnPage(("", ("PAGE", u, t)))
                if params[0] == "WHERE":
                    un = params[1]
                    u = self.server.users.FindUser(un)
                    if u == None:
                        self.TellClient("%s not online."%(un))
                    else:
                        loc = u.GetChannel()
                        if loc == None:
                            loc = u.GetGame()
                        loc = loc.GetName()
                        self.TellClient("%s is in %s"%(un, loc))
                return True
        except LookupError, e:
            self.TellClient(repr(e))
            try:
                self.TellClient(e.value)
            except:
                pass
            self.TellClient(repr(data))
            return True
            
            
    def OnPage(self, data):
        #to:
        #PAGE cbwhiz :this is a page  
        #out to dest:
        #:CBWhiz!u@h PAGE u :this is a page 
        #out to sender:
        #: 389 u 0
        u = self.server.users.FindUser(data[1][1])
        if u == None:
            #should probably return some sort of error, or something
            pass
        else:
            u.connection.senddata(":%s!u@h PAGE %s :%s\r\n"%(self.user.GetName(), data[1][1], data[1][2]))
            self.senddata(": 389 u 0") #i assume this is "page has succeded"
    def OnFindUserEx(self, data):
        #in:
        #FINDUSEREX cbwhiz 0
        #out:
        #: 398 u 0 :#Lob_41_1,0
        wol_logging.log(wol_logging.DEBUG, "finduser", "Looking for user %s..."%(data[1][1]))
        u = self.server.users.FindUser(data[1][1])
        wol_logging.log(wol_logging.DEBUG, "finduser", "Result: %s"%(repr(u)))
        if u == None:
            #should probably return some sort of error, or something
            pass
        else:
            loc = u.GetChannel()
            if loc == None:
                loc = u.GetGame()
            if loc == None:
                loc = "#Null???"
            self.senddata(": 398 u 0 :%s,0\r\n"%(loc.GetName()))
    def OnListChannels(self, data):
        #XWIS's reply:
        #: 321 u:
        #: 327 u #Lob_40_0 6 0 388
        #: 327 u #Lob_41_0 27 0 388
        #: 327 u #Lob_41_1 11 0 388
        #: 327 u #Lob_41_2 5 0 388
        #: 327 u #Lob_41_3 4 0 388
        #: 327 u #Lob_41_4 3 0 388
        #: 327 u #Lob_41_5 3 0 388
        #: 327 u #Lob_41_6 3 0 388
        #: 327 u #Lob_41_7 4 0 388
        #: 327 u #Lob_41_8 3 0 388
        #: 327 u #Lob_41_9 3 0 388
        #: 323 u:
        self.senddata(": 321 u:\r\n")
        for room in self.server.channels.GetChannels():
            self.senddata(": 327 u %s %i 0 388\r\n"%(room.GetName(), len(room.GetUsers())))
        self.senddata(": 323 u:\r\n")
        pass
    def OnJoin(self, data):
        #JOIN #Lob_41_1 zotclot9
        #CBWhiz!u@h JOIN :0,0 #Lob_41_1
        room = data[1][1]
        self.user.LeaveChannel()
        self.user.LeaveGame()
        r = self.server.channels.FindChannel(room)
        if r == None:
            wol_logging.log(wol_logging.ERROR, "chan", "User attempted to join %s, but that room doesnt exist"%(room))
            return
        r.AddUser(self.user)
        for u in r.GetUsers():
            u.connection.senddata(":" + self.user.name + "!u@h JOIN :0,0 " + room + "\r\n")
        self.senddata(": 353 u = " + r.GetName() + " :@"+self.server.adminusername+",0,0\r\n")
        for u in r.GetUsers():    
            self.senddata(": 353 u = " + r.GetName() + " :" + u.GetName() + ",0,0\r\n")
        self.senddata(": 366 u " + r.GetName() + " :\r\n")
        #: 353 u * #Lob_41_1 :CBWhiz,0,0 TrnyAdmin,0,0 A0game,0,0 @RiZ,0,0 clauto,12852,0 ebsSaddam,0,0 @XWISAdmin,0,0 bear4040,0,0 onemach,0,0 twoomuch,0,0 DrizzLPK,0,0 ZeusXGod,0,0
        #: 366 u #Lob_41_1 :


    def OnPart(self, data):
        #PART #Lob_41_1
        #:CBWhiz!u@h PART #Lob_41_1
        room = data[1][1]
        self.user.LeaveChannel()
        self.user.LeaveGame()
        self.senddata(":"+self.user.name + "!u@h PART " + room + "\r\n")
        #TODO: notify other users in the channel about the join
    def OnListGames(self, data):
        gametype = int(data[1][1])
        #XWIS's reply:
        #: 321 u:
        #: 326 u #denzo187's_game 2 0 41 0 0 1145054100 128::g16P25,2097731398,0,0,0,WARISW~1.YRM
        #: 326 u #friz13's_game 3 0 41 0 0 1420819094 128::g16O25,2097731398,2,0,0,XMP25T6.MAP
        #: 326 u #henry999's_game 2 0 41 0 1 3679319085 128::g16S25,2097731398,0,0,0,TourOfEgypt.MAP
        #: 326 u #JGWomg's_game 1 0 41 0 0 1135983209 384::g14U25,2097731398,0,0,0,FourCornersmw.MAP
        #: 326 u #paolooo's_game 3 0 41 0 0 1151471755 128::g14O25,2097731398,1,0,0,XMP23T4.MAP
        #: 323 u:
        self.senddata(": 321 u:\r\n")
        for g in self.server.games.GetGames():
            dip = ip.ip_to_long_external(g.GetHost().connection.rhost)
            self.senddata(": 326 u %s %i 0 %s 0 %u 128::%s\r\n"%(g.GetName(),
                                                                len(g.GetUsers()),
                                                                g.gdata["clientgame"],
                                                                dip,
                                                                g.GetTopic()))
        self.senddata(": 323 u:\r\n")
        #wol_logging.log(wol_logging.INFO, "list.games", "Request game listing, but not yet implemented. Gametype: %i"%(gametype))
        pass
    def OnJoinGame(self, data):
        params = data[1][1:]
        c = len(params)
        if c == 2:
            self.OnEnterExistingGame(params)
        if (c > 8): #or (c==9):
            #8 = game with no password
            #9 = game with a password
            #>9 = game with a password with spaces
            self.OnCreateNewGame(params)
        else:
            self.TellClient(repr(params))
    def OnCreateNewGame(self, params):
	#>       JOINGAME #user's_game unk1 numberOfPlayers gameType unk4 unk5 gameIsTournament unk7 password
	#< user!WWOL@hostname JOINGAME unk1 numberOfPlayers gameType unk4 clanID longIP gameIsTournament :#game_channel_name
        
        #JOINGAME #CBWhiz's_game 1 7 41 3 1 0 1 creating
        #:CBWhiz!u@h JOINGAME 1 7 41 1 0 1165753248 0 :#CBWhiz's_game
        #: 332 u #CBWhiz's_game :
        #: 353 u = #CBWhiz's_game :@CBWhiz,0,1165753248
        #: 366 u #CBWhiz's_game :
        gdata = { }
        try:
            gdata["name"] = params[0]
            gdata["unk1"] = params[1]
            gdata["playercount"] = params[2]
            gdata["clientgame"] = params[3] #41 = Yuri's Revenge
            gdata["unk4"] = params[4]
            gdata["unk5"] = params[5]
            gdata["tournament"] = params[6]
            gdata["unk7"] = params[7]
        except LookupError:
            pass
        g = self.server.games.FindGame(gdata["name"])
        if g != None:
            self.TellClient("That game already exists")
            wol_logging.log(wol_logging.ERROR, "games", "%s already exists!"%(gdata["name"]))
            return
        g = self.server.games.CreateGame(gdata["name"])
        g.gdata = gdata
        g.AddUser(self.user)
        self.senddata(":" + self.user.GetName() + "!u@h JOINGAME %s %s %s %s %s %u %s :%s  \r\n"%(gdata["unk1"],
                                                                                            gdata["playercount"],
                                                                                            gdata["clientgame"],
                                                                                            gdata["unk4"],
                                                                                            "0", #clanID
                                                                                            ip.ip_to_long_external(self.rhost),
                                                                                            gdata["tournament"],
                                                                                            gdata["name"]))
        #self.SendGameNamesList()
    def SendGameNamesList(self):
        g = self.user.GetGame()
        if g != None:
            self.senddata(": 332 u " + g.GetName() + " :"+g.GetTopic()+"\r\n")
            omghost = 0
            for u in g.GetUsers():
                n = u.GetName()
                if omghost == 0:
                    n = "@" + n
                omghost += 1
                dip = ip.ip_to_long_external(u.connection.rhost)
                self.senddata(": 353 u = " + g.GetName() + " :%s,0,%u\r\n"%(n,dip))
                #: 353 u = #CBWhiz's_game :@CBWhiz,0,1165753248
            self.senddata(": 366 u " + g.GetName() + " :\r\n")
    def OnTopic(self, data):
        #TOPIC #CBWhiz's_game :g17D25,2097731398,0,0,0,
        #:irc.westwood.com 332 CBWhiz CBWhiz's game :g15N39,1878366581,0,0,0,MP13S4.MAP
        c = data[1][1]
        t = data[1][2]
        g = self.server.games.FindGame(c)
        if g == None:
            wol_logging.log(wol_logging.ERROR, "games", "Requested set %s to topic %s but that game doesnt exist"%(c, t))
        else:
            g.SetTopic(t)
            users = g.GetUsers()
            self.SendGameNamesList()
            #for u in users:               
                #u.connection.senddata(": 332 %s %s :%s\r\n"%(self.user.GetName(), c, t))


    def OnGameOpt(self, data):
        #GAMEOPT CBWhiz :R1,2,-2,-2,200a8c0,1,552
        un = data[1][1]
        d = data[1][2]
        if un[0] == "#":
            #wol_logging.log(wol_logging.DEBUG, "games", "GAMEOPT for %s supposedly set to %s"%(un, d))
            g = self.user.GetGame()
            if g != None:
                for u in g.GetUsers():
                    if u != self.user:
                        u.connection.senddata(":"+self.user.GetName()+"!u@h GAMEOPT "+un+" :"+d+"\r\n")
        else:
            g = self.user.GetGame()
            if g != None:
                for u in g.GetUsers():
                    u.connection.senddata(":"+self.user.GetName()+"!u@h GAMEOPT "+un+" :"+d+"\r\n")
            #:CBWhiz!u@h GAMEOPT CBWhiz :R1,2,-2,-2,200a8c0,1,552
    def OnEnterExistingGame(self, params):
        gdata = {}
        gdata["name"] = params[1][1]
        g = self.server.games.FindGame(gdata["name"])
        if g == None:
            self.TellClient("That game does not exist")
            self.senddata(": 403 :")
            return
        gdata = g.gdata
        self.senddata(":" + self.user.GetName() + "!u@h JOINGAME %s %s %s %s %s %u %s :%s\r\n"%(gdata["2"],
                                                                                            gdata["playercount"],
                                                                                            gdata["clientgame"],
                                                                                            gdata["6"],
                                                                                            "0",
                                                                                            ip.ip_to_long_external(self.rhost),
                                                                                            gdata["tournament"],
                                                                                            gdata["name"]))
        g.AddUser(self.user)
        self.SendGameNamesList()
    
def CreateServerSocket(port):
    """Creates a listening socket on port, and sets it to non-blocking mode"""
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', port))
    serversocket.listen(5)
    serversocket.setblocking(0)
    return serversocket

class WOLServer:
    def __init__(self):
        self.name = "PyWOL 0.1"
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
                 "#Lob_41_0", #YR
                 #"#Lob_41_1"  #YR
                 )
        self.channels = channel.Channel_Manager()
        for name in chans:
            self.channels.CreateChannel(name)
        self.games = channel.Game_Manager()
        self.adminusername = "PyWOL_0.1"


class Server_Listener_Thread(Thread):
    """Defines the thread that listens for incoming connections
    """
    def __repr__(self):
        return "Server incoming connection thread"
    def __init__(self, wolserver_to_connect_to):
        Thread.__init__(self, group=None, target=None, name="Server incoming connection thread")
        self.setDaemon(True)
        wol_logging.log(wol_logging.DEBUG, "accept", "Server incoming connection thread Created")
        self.__serv = wolserver_to_connect_to
    def run(self):
        sock_info = {
            4005: "Main_Sock",
            4003: "Chat_Sock",
            4001: "Game_Sock",
            4002: "Ladder_Sock"
        }
        while (True):
            readable_socks = select(socks.values(), [],[])[0] #select blocks
            for s in readable_socks:
                (clientsocket, address) = (None, None)
                try:
                    p = s.getsockname()[1] #p = port
                    (clientsocket, address) = socks[p].accept()
                except socket.error, (n, e):
                    if n==10035: #no data
                        pass
                    else:
                        raise socket.error, (n, e)
                if clientsocket != None:
                    n = sock_info[p]
                    if p == 4005:
                        ct = WOL_Main_Connection(n, clientsocket, address[0], address[1])
                        ct.set_server(self.__serv)
                    elif p == 4003:
                        ct = WOL_Chat_Connection(n, clientsocket, address[0], address[1])
                        ct.set_server(self.__serv)
                    else:
                        ct = irc_util.Base_IRC_Connection("???? (" + str(p) + ") Sock", clientsocket, address[0], address[1])
                    ct.start()
#-----------------------------------------------------------------
#-----------------------------------------------------------------
#-----------------------------------------------------------------
if (__name__ == "__main__"):
    wol_logging.log(wol_logging.INFO, "", "PyWOL started")
    
    serv = WOLServer()

    sock_info = (
        (4005, "Main_Sock"),
        (4003, "Chat_Sock"),
        (4001, "Game_Sock"),
        (4002, "Ladder_Sock")
        )
    socks = { }
    for (p, n) in sock_info:
        try:
            socks[p] = CreateServerSocket(p)
        except socket.error, (n, e):
            if n==10048:
                raise PortError, "Port " + str(p) + " in use."
            raise socket.error, (n, e)
        wol_logging.log(wol_logging.INFO, 'listen', "Listening for " + n + " conection on port " + str(p))


    #tidy = Tidy_Thread()
    #tidy.start()

    accept_thread = Server_Listener_Thread(serv)
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
            while halt == False:
                k = msvcrt.getch()
                if (k == chr(13)):
                    halt = True  
#    for (s) in socks.values():
#        s.close()
