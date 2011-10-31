from threading import Thread
import socket
import wol_logging
import select
import colorama

def PrefixMessageFormat(prefix, command, params):
    """Formats an outgoing message with the specified prefix, command, and paramaters.
    Puts the last paramater after the :"""
    if len(params) > 1:
        return ":%s %s %s :%s\r\n"%(prefix, command, ' '.join(params[:-1]), params[-1])
    else:
        return ":%s %s :%s\r\n"%(prefix, command, params[0])

def PrefixMessageNoPostfixParamFormat(prefix, command, params):
    """Formats an outgoing message with the specified prefix, command, and paramaters.
    Does not include a : seperator for last param"""
    return ":%s %s %s\r\n"%(prefix, command, ' '.join(params))

def split_irc_line(ircline):
    """Parses any incoming IRC string into its component parts, and returns a list holding prefix and a list of params

    Input: :prefix cmd param param :param with spaces
    Output: ["prefix", ["cmd", "param", "param", "param with spaces"]]
    """
    prefix = ""
    ret = []
    if ircline[0] == ":":
        idx = ircline.find(" ")
        if (idx > -1):
            prefix = ircline[1:idx]
            ircline = ircline[idx+1:]
        else:
            prefix = ircline[1:]
            ircline = ""
    idx = 0
    idx = ircline.find(" ")
    while ircline != "":
        if (ircline[0] == ":"):
            ret.append(ircline[1:])
            ircline = ""
            break
        if (idx > -1):
            ret.append(ircline[0:idx])
            ircline = ircline[idx+1:]
        else:
            ret.append(ircline)
            ircline = ""
        idx = ircline.find(" ")
    r = [prefix, ret]
    return r

def ParseIRCLine(ircline, functionmatrix):
    """Parses ircline according it irc rules, and calls the function specified in functionmatrix depending on the irc command.
    example:
    functionmatrix = {
        'NICK':     OnNickLine,
        'unknown':  OnUnknownLine
        }
    """
    parsed = split_irc_line(ircline)
    if len(parsed[1]) == 0:
        #no command?!
        return None
    cmd = parsed[1][0].upper()
    func = None
    try:
        func = functionmatrix[cmd]
    except:
        try:
            func = functionmatrix["unknown"]
        except:
            func = None
    if func == None:
        return None
    return func(parsed)

class IRC_Buffer:
    """Provides a simple buffer interface for reading from an IRC connection.
    
    push() any amount of data.
    pop() is gaurenteed to only return full lines."""
    def __init__(self):
        self.__data = ""
        pass
    def push(self, str):
        self.__data += str
    def pop(self):
        sdf = self.__data.find("\n")
        if (sdf > -1):
            ret = self.__data[0:sdf]
            self.__data = self.__data[sdf+1:]
            return ret.strip()
        else:
            return ""    

maxconn = 1;
class Base_IRC_Connection(Thread):
    """Defines a basic IRC connection handler.
    
    Override get_function_matrix() or OnRecvStr(ircline) to expand functionality.
    """
    def debug(self, level, dtype, strn):
        cid = self.conid
        if getattr(self, 'user', None):
            cid = "%s - %s"%(cid, self.user.name)
        wol_logging.log_caller(level, dtype, " [%s] "%(cid) + strn)
    def __repr__(self):
        return "%s: remote thread for %s"%(self.__class__, self.rhost)
    def __init__(self, sockname, sock, remotehost, remoteport):
        global maxconn;
        self.conid = maxconn
        maxconn = maxconn + 1
        Thread.__init__(self, group=None, target=None, name="Remote %s thread for %s:%i"%(self.__class__, remotehost, remoteport))
        self.setDaemon(True)
        self.__halt=False
        sock.setblocking(0)
        self._sock=sock
        self.__buf = IRC_Buffer()
        self.name = sockname
        self.rhost = remotehost
        self.rport = remoteport
        self.debug(wol_logging.DEBUG, "conn", "Socket Created")
        self.OnConnect();
    def senddata(self, str):
        try:
            self._sock.setblocking(1)
            self._sock.sendall(str)
            if str[-2:] != "\r\n":
                print "!!! Error no newline: %s"%(str)
            self.debug(wol_logging.DEBUG, "raw.out", colorama.Fore.YELLOW + str.strip())
            self._sock.setblocking(0)
        except Exception, e:
            if (e[0] == 10054):
                #Connection reset by peer
                self.debug(wol_logging.DEBUG, "connection", "Connection reset by peer")
                self.Disconnect()
            else:
                import StringIO
                import traceback
                f = StringIO.StringIO()
                traceback.print_exc(file=f)
                f = f.getvalue()
                wol_logging.log(wol_logging.ERROR, "out", f)
                raise e
    def Disconnect(self):
        try:
            self._sock.close()
        except Exception, e:
            pass
        self.OnDisconnect()
        self.halt()
    def stop(self):
        self.__halt=True
    def dumpbuf(self):
        print "incoming buffer: " + self.__buf._IRC_Buffer__data
    def run(self):
        while (self.__halt == False):
            select.select([self._sock],[],[self._sock])
            r = ""
            try:
                r = self._sock.recv(1024)
                if (r == ""):
                    self.OnDisconnect()
                    break
            except socket.error, (n, e):
                if n==10035: #no data
                    pass
                else:
                    self.OnDisconnect()
                    self.OnError(n, e)
                    break;
            self.__buf.push(r)

            l = self.__buf.pop()
            while l != "": #we have a full line we can process now
                try:
                    self.OnRecvStr(l)
                except:

                    import traceback
                    import sys
                    import StringIO
                    f = StringIO.StringIO()
                    
                    traceback.print_exc(file=f)
                    f = f.getvalue()
                    try:
                        self.TellClient(f)
                    except:
                        pass #i dont have an TellClient method
                    f = f.split("\n")
                    for l in f:
                        wol_logging.log(wol_logging.CRITICAL, "except", l)
                    print '-'*60
                    print '-'*60
                    print '-'*60
                    print "Exception in %s" %(repr(self))
                    print '\n'.join(f)
                    print '-'*60
                    print '-'*60
                    print '-'*60
                    self._sock.close()
                    self.OnDisconnect()
                    self.halt()
                l = self.__buf.pop()
    def halt(self):
        self.__halt = True
    def OnConnect(self):
        self.debug(wol_logging.INFO, "conn", "Accepted " + self.name + " connection from " + self.rhost + ":" + str(self.rport))
        
    def OnDisconnect(self):
        self.debug(wol_logging.INFO, "conn", "Disconnected")
        self._sock.close()
        
    def OnError(self, num, str):
        self.debug(wol_logging.ERROR,"conn", "Error %i: %s" % (num, str))
        
    def get_function_matrix(self):
        return {
            'unknown':  self.OnRecvUnknown
        }
    def OnRecvStr(self, ircline):
        self.debug(wol_logging.DEBUG,"raw.in", ircline)
        functionmatrix = self.get_function_matrix()
        r = ParseIRCLine(ircline, functionmatrix)
        if (r == None):
            pass
            #self.debug(wol_logging.DEBUG,"raw", "%s::OnRecvStr() returned None; ircline=%s"%(self.__class__, ircline))
        pass
    def OnRecvUnknown(self, data):
        self.debug(wol_logging.INFO, "unknown", "Unrecognized Command %s: " %(repr(data)))
        return True #Processed

if __name__ == "__main__":
    import unittest

    class SplitLineTestcase(unittest.TestCase):
        def runTest(self):
            tl = ":what_person CMD param1 param2 :param three"
            a = split_irc_line(tl)
            omg =  "SplitLine Failure: Sent: " + tl + "\n"
            omg += "                    Got: " + repr(a)
            assert a[0] == "what_person", omg
            assert a[1][0] == "CMD", omg
            assert a[1][1] == "param1", omg
            assert a[1][2] == "param2", omg
            assert a[1][3] == "param three", omg
    
    class IRCBufferTestcase(unittest.TestCase):
        def runTest(self):
            z = IRC_Buffer()
            assert z.pop() == "", "Blank IRC_Buffer error"
            z.push("omgomgomg")
            assert z.pop() == "", "IRC_Buffer no terminated line error"
            z.push("\r\n")
            assert z.pop() == "omgomgomg", "IRC_Buffer returned bad line"

    class BaseIRCClientTestcase(unittest.TestCase):
        def runTest(self):
            pass #TODO: write me

    import time
    print time.strftime("[%Y-%m-%d %H:%M]: ") + "Running irc_util.py testcases..."
    unittest.main()
