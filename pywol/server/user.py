from .. import wol_logging


maxuid = 1;
class User:
    def __repr__(self):
        return "User %i: %s (Room: %s, Game: %s)"%(self.uid, self.name, repr(self.channel), repr(self.game))
    def __init__(self, name, connection, user_mgr):
        global maxuid;
        self.uid = maxuid
        maxuid += 1
        self.user_mgr = user_mgr
        self.name = name
        self.codepage = ""
        self.locale = "2"
        self.opts = ""
        self.channel = ""
        self.hostname = ""
        self.realname = ""
        self.username = ""
        self.channel = None    #Holds refrences to Channel instances
        self.game = None       #Holds references to Game instances
        self.connection = connection
    def __del__(self):
        wol_logging.log(wol_logging.DEBUG, "user", "User Instance Destroyed (%s)"%(repr(self)))
    def GetName(self):
        return self.name
    def IsInGame(self):
        return self.game != None
    def IsInLobby(self):
        if self.channel == None:
            return False
        return True
    def GetUID(self):
        return self.uid
    def GetGame(self):
        return self.game
    def GetChannel(self):
        return self.channel
    def GetAddrString(self):
        return self.name + "!" + self.username + "@" + self.hostname
    def LeaveGame(self):
        if self.game != None:
            self.game.RemoveUser(self)
            self.game = None
    def LeaveChannel(self):
        if self.channel != None:
            self.channel.RemoveUser(self)
            self.channel = None
    def Disconnect(self):
        self.LeaveChannel()
        self.LeaveGame()
        self.user_mgr.RemoveUser(self)
        self.user_mgr = None
        if self.connection != None:
            self.connection.Disconnect()



class User_Manager:
    def __init__(self):
        self.u = [ ]
    def CreateUser(self, username, connection):
        """Returns a new User instance"""
        if self.FindUser(name=username) != None:
            wol_logging.log_caller(wol_logging.ERROR, "users", "User_Manager::CreateUser called when a user by that name exists!")
            wol_logging.log_caller(wol_logging.ERROR, "users", "User_Manager::CreateUser - removing old %s"%(username))
            self.RemoveUser(self.FindUser(name=username))
            #return None
        u = User(username, connection, self)
        self.u.append(u)
        return u
        #pt = Ping_Thread(user)
        #pt.start()
    def RemoveUser(self, user):
        try:
            user.LeaveChannel()
            user.LeaveGame()
            self.u.remove(user)
        except:
            wol_logging.log_caller(wol_logging.ERROR, "users", "User_Manager::RemoveUser called with invalid user argument")
    def GetUsers(self):
        return self.u
    def FindUser(self, name=None, id=None):
        """Specify name or id, but not both. Returns a user instance"""
        if (name == None) and (id==None):
            wol_logging.log_caller(wol_logging.ERROR, "users", "User_Manager::FindUser called with None name and id!")
        if (name != None):
            u = [u for u in self.u if u.GetName().upper() == name.upper()]
            if len(u) == 0:
                return None
            return u[0]
        if (id != None):
            u = [u for u in self.u if u.GetUID() == id]
            if len(u) == 0:
                return None
            return u[0]
