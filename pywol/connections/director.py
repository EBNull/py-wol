from .. import irc_util
from ..irc_util import PrefixMessageFormat

class DirectorConnection(irc_util.Base_IRC_Connection):
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
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "605", ("Username", "%s 4003 '0,1,2,3,4,5,6,7,8,9,10:%s' -8 36.1083 -115.0582"%(self.server.ip, "PyWOL WOL Server 0.02"))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "605", ("Username", "%s 4003 'Live chat server' -8 36.1083 -115.0582"%(self.server.ip))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "608", ("Username", "%s 4001 'Gameres server' -8 36.1083 -115.0582"%(self.server.ip))))
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "609", ("Username", "%s 4002 'Ladder server' -8 36.1083 -115.0582"%(self.server.ip))))
    def OnQuit(self, data):
        self.senddata(irc_util.PrefixMessageFormat(self.server.hostname, "607", ("Username", "goodbye")))
        self.halt()
        self._sock.close()