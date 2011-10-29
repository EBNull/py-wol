from .. import ip
from .. import wol_logging

import user
import channel

class ServerConfig:
    channels = (
        "#Lob_18_0", #TS
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

class WOLServer:
    def __init__(self, config=ServerConfig):
        self.config = config
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
        self.channels = channel.Channel_Manager()
        for name in config.channels:
            self.channels.CreateChannel(name)
        self.games = channel.Game_Manager()
        self.adminusername = "PyWOL_0.3"