import irc_util
from irc_util import PrefixMessageFormat

class LadderConnection(irc_util.Base_IRC_Connection):
    def __init__(self, *args):
        super(self.__class__,self).__init__(*args)
        self.server = None
    def set_server(self, serverinstance):
        self.server = serverinstance
    def get_function_matrix(self):
        return {
            #LISTSEARCH 8448 -1 0 0 0 :cbwhiz:
            'unknown': self.OnRecvUnknown
        }