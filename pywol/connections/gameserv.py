from .. import wol_logging
from .. import irc_util
from ..irc_util import PrefixMessageFormat
from .. import ip
import time

class GameServConnection(irc_util.Base_IRC_Connection):
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
            self.senddata(":%s!u@h PRIVMSG %s : %s\r\n"%(self.server.adminusername, self.user.GetName(), l))
    def __init__(self, *args):
        super(self.__class__,self).__init__(*args)
        self.server = None
        self.user = None
        self.didmotd = False
        self.senddata(":irc.westwood.com 999 :You connect. Take this +1 mace.\r\n");
    def set_server(self, serverinstance):
        self.server = serverinstance
    def get_function_matrix(self):
        return {
            #random mirc stuff
            'USERHOST': self.OnUserHost,
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
            'ADDBUDDY': self.OnAddBuddy,
            'DELBUDDY': self.OnDelBuddy,
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
            'STARTG': self.OnStartGame,
            
            'unknown': self.OnRecvUnknown
        }
    def OnIgnorableIRCLine(self, data):
        pass
    def OnPASS(self, data):
        pass
    def OnUserHost(self, data):
        self.senddata("302 %s :%s=+%s@%s\r\n"%(self.user.GetName(), self.user.GetName(), self.user.username, self.user.hostname))
    def OnNick(self, data):
        self.user = self.server.users.CreateUser(data[1][1], self)
    def OnUser(self, data):
        #USER UserName HostName irc.westwood.com :RealName
        try:
            self.user.username = data[1][1]
            self.user.hostname = data[1][2]
            self.user.realname = data[1][4]
        except e:
            self.senddata(": 999 :wrong format, use USER UserName HostName irc.westwood.com :RealName")
    def OnVerChk(self, data):
        self.senddata(": 379 u :none none none 1 32512 NONREQ\r\n")
        #: 379 u :none none none 1 32512 NONREQ
        #self.senddata(irc_util.PrefixMessageNoPostfixParamFormat(self.server.hostname, "602", (self.user.GetName(), "Update record non-existant")))

    def OnSetOpt(self, data):
        if self.didmotd == True:
            return
        self.didmotd = True
        self.senddata(":irc.westwood.com 001 %s :%s\r\n"%(self.user.GetName(), self.user.GetName()));
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
        self.senddata(": 333 u %s\r\n"%('`'.join(self.user.buddies)))
    def OnAddBuddy(self, data):
        self.user.buddies.add(data[1][1])
    def OnDelBuddy(self, data):
        self.user.buddies.discard(data[1][1])
    def OnQuit(self, data):
        self.user.LeaveChannel()
        self.user.LeaveGame()
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "607", ("Username", "goodbye")))
        self.user.Disconnect()
        self.user = None
        self.halt()
        self._sock.close()

    def OnList(self, data):
        if len(data[1]) < 2:
            self.OnListChannels(data)
        else:
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
                    u.connection.senddata(":%s!u@h PRIVMSG %s :%s\r\n"%(self.user.GetName(), c.GetName(), data[1][2]))
        else: #message to user
            usernames = data[1][1]
            text = data[1][2]
            usernames = usernames.split(',')
            for username in usernames:
                u = self.server.users.FindUser(username)
                if u == None:
                    self.TellClient("No such user %s"%(username))
                    #should probably return some sort of error, or something
                    pass
                else:
                    u.connection.senddata(":%s!u@h PRIVMSG %s :%s\r\n"%(self.user.GetName(), username, text))
    def CheckSpecialCommands(self, data):
        cmdstr = data[1][2]
        try:
            if cmdstr[0] == "/":
                params = cmdstr.split(" ")
                params[0] = params[0][1:].upper()
                if params[0] == "KILL":
                    un = params[1]
                    u = self.server.users.FindUser(un)
                    if u != None:
                        u.connection.senddata(": 398 u 0:#byebye,0\r\n")
                    else:
                        self.TellClient("%s not found."%(un))
                elif params[0] == "W" or params[0] == "M" or params[0] == "PAGE":
                    u = params[1]
                    t = ' '.join(params[2:])
                    self.OnPage(("", ("PAGE", u, t)))
                elif params[0] == "WHERE":
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
                else:
                        self.TellClient("Command not understood")
                        self.TellClient(repr(params))
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
            self.senddata(": 389 u 1\r\n") #RA2 displays "User isn't logged in"
        else:
            u.connection.senddata(":%s!u@h PAGE %s :%s\r\n"%(self.user.GetName(), data[1][1], data[1][2]))
            self.senddata(": 389 u 0\r\n")
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
            self.senddata(": 398 u 1\r\n")
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
            self.senddata(": 326 u %s %i 0 %s 0 0 %u 128::%s\r\n"%(g.GetName(),
                                                                len(g.GetUsers()),
                                                                g.gdata["clientgame"],
                                                                dip,
                                                                g.topic))
        self.senddata(": 323 u:\r\n")
        #wol_logging.log(wol_logging.INFO, "list.games", "Request game listing, but not yet implemented. Gametype: %i"%(gametype))
        pass
    def OnJoinGame(self, data):
        params = data[1][1:]
        c = len(params)
        if c == 2:
            self.OnEnterExistingGame(params)
        if (c >= 8): #or (c==9):
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

        #Tiberian Sun
        #
        #   JOINGAME #CBWhiz's_game 1 3 18 3 1 0 0 lol tib      < normal, passworded
        #   JOINGAME #CBWhiz's_game 1 2 18 3 1 1 0              < tourny, no password
        #           0 - Game Name       (#CBWhiz's Game)
        #           1 - Unknown1        (1) [always 1?]
        #           2 - Player Count    (3) (2)
        #           3 - Client Game     (18) [18 - TS, 33 - RA2, 41 - YR]
        #           4 - Unknown4        (3) [always 3?]
        #           5 - Unknown5        (1)
        #           6 - IsTournament    (0) (1)
        #           7 - ChanNumber      (0)         (ie, last number in channel name of #Lob_33_1)
        #           8>- Password        (lol tib) [interestingly, no : is used to mark password start]
        #
        #
        #   :CBWhiz!u@h JOINGAME 1 3 18 3 0 12345 0 :#CBWhiz's_game
        #                 Count   Desc      Cur         Index_Of_Sent_Str
        #                   1 - Unknown1    (1)                 1
        #                   2 - PlayerCount (3)                 2
        #                   3 - ClientGame  (18)                3
        #                   4 - Unknown4    (3)                 4 (7, channum?)
        #                   5 - ClanID?     (0)                 - [Can always pass zero]
        #                   6 - IPAddress   (12345)             -
        #                   7 - Tournament  (0)                 6
        #                   8 - GameName    (#CBWhiz's_game)    -
        gdata = { }
        try:
            gdata["name"] = params[0]
            gdata["unk1"] = params[1]
            gdata["playercount"] = params[2]
            gdata["clientgame"] = params[3] #41 = Yuri's Revenge
            gdata["unk4"] = params[4]
            gdata["unk5"] = params[5]
            gdata["tournament"] = params[6]
            gdata["channum"] = params[7]
            gdata["password"] = ' '.join(params[8:])
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
                                                                                            gdata["channum"],
                                                                                            "0", #clanID
                                                                                            ip.ip_to_long_external(self.rhost),
                                                                                            gdata["tournament"],
                                                                                            gdata["name"]))
        g.SendNameListToAll()
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
        t = ''.join(data[1][2:])
        g = self.server.games.FindGame(c)
        if g == None:
            wol_logging.log(wol_logging.ERROR, "games", "Requested set %s to topic %s but that game doesnt exist"%(c, t))
        else:
            g.topic = t
            users = g.GetUsers()
            for u in users:
                if u != self.user: #Confirmed, sender/hoster does not get this back
                    u.connection.senddata(": 332 %s %s :%s\r\n"%(self.user.GetName(), c, t))


    def OnGameOpt(self, data):
        #GAMEOPT CBWhiz :R1,2,-2,-2,200a8c0,1,552
        un = data[1][1]
        d = data[1][2]
        if un[0] == "#":
            #wol_logging.log(wol_logging.DEBUG, "games", "GAMEOPT for %s supposedly set to %s"%(un, d))
            g = self.user.GetGame()
            if g != None:
                for u in g.GetUsers():
                    if u != self.user: #Confirmed, host does not get channel GameOpts
                        u.connection.senddata(":"+self.user.GetName()+"!u@h GAMEOPT "+un+" :"+d+"\r\n")
        else:
            g = self.user.GetGame()
            if g != None:
                for u in g.GetUsers():
                    u.connection.senddata(":"+self.user.GetName()+"!u@h GAMEOPT "+un+" :"+d+"\r\n")
            #:CBWhiz!u@h GAMEOPT CBWhiz :R1,2,-2,-2,200a8c0,1,552
    def OnEnterExistingGame(self, params):
        gdata = {}
        gdata["name"] = params[0]
        g = self.server.games.FindGame(gdata["name"])
        if g == None:
            self.TellClient("That game does not exist")
            self.senddata(": 403 :\r\n")
            return
        gdata = g.gdata
        self.senddata(":" + self.user.GetName() + "!u@h JOINGAME %s %s %s %s %s %u %s :%s\r\n"%(gdata["unk1"],
                                                                                            gdata["playercount"],
                                                                                            gdata["clientgame"],
                                                                                            gdata["channum"],
                                                                                            "0",
                                                                                            ip.ip_to_long_external(g.GetHost().connection.rhost),
                                                                                            gdata["tournament"],
                                                                                            gdata["name"]))
        g.AddUser(self.user)
        g.SendNameListToAll()
    def OnStartGame(self, data):
        #self.TellClient(repr(data))
        #gamehost!WWOL@hostname STARTG u :user1 xxx.xxx.xxx.xxx user2 xxx.xxx.xxx.xxx :gameNumber cTime
        wol_logging.log(wol_logging.DEBUG, "games", "OnStartGame: %s"%(repr(data)))
        c = data[1][1] #total guess
        #interestingly data[1][2] is a comma delimited username list
        g = self.server.games.FindGame(c)
        gametime = int(time.time())
        if g == None:
            wol_logging.log(wol_logging.ERROR, "games", "Requested startgame %s but channel not found"%(c))
        else:
            users = g.GetUsers()
            userlist = []
            for u in users:
                #build IP list
                theip = u.connection.rhost
                userlist.append("%s %s"%(u.GetName(), str(theip)))
            userlist = ' '.join(userlist)
            for u in users:
                u.connection.senddata("%s!u@h STARTG u :%s :1337 %s\r\n"%(g.GetHost().GetName(), userlist, gametime))
