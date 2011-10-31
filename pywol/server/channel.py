from .. import wol_logging


class Channel:
    def __repr__(self):
        return "Channel [PyID: %i] %s: %i users (%s)"%(id(self), self.name, len(self.users), ', '.join([u.GetName() for u in self.users]))
    def __init__(self, name, chan_mgr):
        self.name = name
        self.topic = ""
        self.users = []
        self.chan_mgr = chan_mgr
    def GetName(self):
        return self.name
    def __del__(self):
        wol_logging.log(wol_logging.DEBUG, "chan", "Channel Instance Destroyed (%s)"%(repr(self)))
    def AddUser(self, user):
        try:
            self.users.remove(user)
        except ValueError:
            pass #User not already in channel
        user.LeaveChannel()
        self.users.append(user)
        user.channel = self
    def RemoveUser(self, user):
        try:
            self.users.remove(user)
            user.channel = None
        except ValueError:
            return False
    def GetUsers(self):
        return self.users

class Channel_Manager:
    def __init__(self):
        self.g = [ ]
    def CreateChannel(self, channel_name):
        """Returns a new Channel instance"""
        if self.FindChannel(channel_name) != None:
            wol_logging.log_caller(wol_logging.ERROR, "chans", "Channel_Manager::CreateChannel called when a channel by that name exists!")
            return None
        g = Channel(channel_name, self)
        self.g.append(g)
        return g
        #pt = Ping_Thread(user)
        #pt.start()
    def RemoveChannel(self, channel):
        try:
            self.g.remove(channel)
        except:
            wol_logging.log_caller(wol_logging.ERROR, "chans", "Channel_Manager::RemoveChannel called with invalid channel argument")
    def GetChannels(self):
        return self.g
    def FindChannel(self, name=None):
        """Specify channel name"""
        if (name != None):
            u = [u for u in self.g if u.GetName() == name]
            if len(u) == 0:
                return None
            return u[0]

maxgid = 1
class Game(Channel):
    def __repr__(self):
        return "Game [PyID: %i] %s: %i users (%s)"%(id(self), self.name, len(self.users), ', '.join([u.GetName() for u in self.users]))
    def __del__(self):
        wol_logging.log(wol_logging.DEBUG, "game", "Game Instance Destroyed (%s)"%(repr(self)))
    def __init__(self, name, game_mgr):
        Channel.__init__(self, name, game_mgr)
        global maxgid
        self.gid = maxgid
        maxgid += 1
        gdata = { }
        gdata["name"] = name
        gdata["2"] = "0"
        gdata["playercount"] = "8"
        gdata["clientgame"] = "41"
        gdata["5"] = "0"
        gdata["6"] = "0"
        gdata["tournament"] = "0"
        gdata["8"] = "0"
        self.gdata = gdata
        wol_logging.log(wol_logging.DEBUG, "game", "Game Instance Created (%s)"%(repr(self)))
    def AddUser(self, user):
        Channel.AddUser(self, user)
        user.channel = None
        user.game = self
    def GetHost(self):
        return self.users[0]
    def GetGID(self):
        return self.gid
    def RemoveUser(self, user):
        Channel.RemoveUser(self, user)
        if len(self.users) == 0:
            self.chan_mgr.RemoveGame(self)
    def SendNameListToAll(self):
        for u in self.users:
            u.connection.SendGameNamesList()
class Game_Manager:
    def __init__(self):
        self.g = [ ]
    def CreateGame(self, game_name):
        """Returns a new Game instance"""
        if self.FindGame(name=game_name) != None:
            wol_logging.log_caller(wol_logging.ERROR, "games", "Game_Manager::CreateGame called when a game by that name exists!")
            return None
        g = Game(game_name, self)
        self.g.append(g)
        return g
        #pt = Ping_Thread(user)
        #pt.start()
    def RemoveGame(self, game):
        try:
            self.g.remove(game)
        except:
            wol_logging.log_caller(wol_logging.ERROR, "games", "Game_Manager::RemoveGame called with invalid game argument")
    def GetGames(self):
        return self.g
    def FindGame(self, name=None, id=None):
        """Specify name or id, but not both. Returns a user instance"""
        if (name == None) and (id==None):
            wol_logging.log_caller(wol_logging.ERROR, "games", "Game_Manager::FindGame called with None name and id!")
        if (name != None):
            u = [u for u in self.g if u.GetName().upper() == name.upper()]
            if len(u) == 0:
                return None
            return u[0]
        if (id != None):
            u = [u for u in self.g if u.GetGID() == id]
            if len(u) == 0:
                return None
            return u[0]
