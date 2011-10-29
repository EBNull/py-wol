import socket
from select import select
from threading import Thread
import logging
log = logging.getLogger('pywol.listenthread')

from connections.director import DirectorConnection
from connections.gameserv import GameServConnection
#from connections.gameres import GameResConnection
from connections.ladder import LadderConnection

def CreateServerSocket(port):
    """Creates a listening socket on port, and sets it to non-blocking mode"""
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', port))
    serversocket.listen(5)
    serversocket.setblocking(0)
    return serversocket

class ListenThread(Thread):
    """Defines the thread that listens for incoming connections
    """
    def __repr__(self):
        return "Server incoming connection thread"
    def __init__(self, wolserver_to_connect_to):
        Thread.__init__(self, group=None, target=None, name="Server incoming connection thread")
        self.setDaemon(True)
        log.debug("Server incoming connection thread Created")
        self.__serv = wolserver_to_connect_to
        self.__halt = False
    def halt(self):
        self.__halt = True
    def run(self):
        sock_info = {
            4005: ("Director_Sock", DirectorConnection),
            4002: ("GameServ_Sock", GameServConnection),
            4001: ("GameResolution_Sock", None),
            4003: ("Ladder_Sock", LadderConnection)
        }
        socks = { }
        for port, (name, klass) in sock_info.iteritems():
            try:
                socks[port] = CreateServerSocket(port)
            except socket.error, (n, e):
                if n==10048:
                    raise PortError("Port %s in use."%(p))
                raise socket.error(n, e)
            logging.info("Listening for %s connection on port %s"%(name, port))
        
        while (self.__halt == False):
            readable_socks = select(socks.values(), [],[])[0] #select blocks
            if (self.__halt == True):
                break
            for s in readable_socks:
                (clientsocket, address) = (None, None)
                port = None
                try:
                    port = s.getsockname()[1]
                    (clientsocket, address) = socks[port].accept()
                except socket.error as (n, e):
                    if n!=10035: #no data
                        raise
                if clientsocket != None:
                    name, klass = sock_info[port]
                    if klass is not None:
                        ct = klass(name, clientsocket, address[0], address[1])
                        ct.set_server(self.__serv)
                        ct.start()
                    else:
                        clientsocket.close()
                        log.warn("Tried to open connection on port %s, dropped due to no handler"%(port))
                        