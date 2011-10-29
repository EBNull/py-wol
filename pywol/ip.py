
def ip_to_long(ip):
    """Converts a dotted-quad IP to a long.
    
    Input:  "192.168.0.1"
    Output: 3232235521L
    """
    import struct, socket
    return struct.unpack(">L", socket.inet_aton(ip))[0]

def long_to_ip(long):
    """Converts a long IP to a dotted-quad string.
    
    Input:  3232235521L
    Output: "192.168.0.1"
    """  
    import struct, socket
    return socket.inet_ntoa(struct.pack(">L", long))




#Helper Functions relying on external data:
External_IP = None

class IPError:
    def __init__(self, error=""):
        self.error = error
    def __repr__(self):
        return self.error

def ip_to_long_external(ip):
    """Converts a dotted-quad IP to a long, while automaticly changing it to an external IP.

    Relies on a global named External_IP, which is a string in dotted-quad IP notation

    Assuming your WAN IP is 69.123.251.160,
    Input:  "192.168.0.1"
    Output: 1165753248L (69.123.251.160 encoded)
    """
    global External_IP
    dip = ip_to_long(ip)            #Assume ip is okay
    foct = long(ip.split('.')[0])   #grab first octet
    internalipoct = (192, 127)
    if(foct in internalipoct):      #check it against pre-defined "internal" list
        if External_IP == None:
            raise IPError
        dip = ip_to_long(External_IP)
    return dip

def get_external_ip(nocache=False):
    """Gets external IP from checkdns.dyndns.org, and sets global External_IP
    Warning: no timeout"""
    global External_IP
    if (External_IP != None) and (nocache != True):
        return External_IP
    try:
        import urllib
        u = urllib.urlopen("http://checkip.dyndns.org/")
        n = u.read(1024)
        u.close()
        import re
        ip = re.findall("<body>Current IP Address: ([^<]*)</body>", n)
        if len(ip) == 0:
            raise IPError("Unable to get IP from http://checkip.dyndns.org/: %s"%(n))
        ip = ip[0]
        External_IP = ip
        return ip
    except:
        raise IPError("Unable to get IP from http://checkip.dyndns.org/")
        return None


if __name__ == "__main__":
    import unittest

    class IPConversionTestCase(unittest.TestCase):
        def runTest(self):
            assert ip_to_long("192.168.0.1") == 3232235521L, 'ip_to_long failure'
            assert long_to_ip(3232235521L) == "192.168.0.1", 'long_to_ip failure'
            #print "IP converstion tests OK"
    class ExternalIPTestcase(unittest.TestCase):
        def runTest(self):
            ip = get_external_ip()
            #print "External IP is %s"%(ip)
            assert ip != None, 'get_external_ip() failed'
    import time
    print time.strftime("[%Y-%m-%d %H:%M]: ") + "Running ip.py testcases..."
    unittest.main()