
import socket

def host_id_gen(ip):
    """use hostname as host's id"""
    hostname = ''
    try:
        host = socket.gethostbyaddr(ip)
        if len(host[1]) > 0:
            hostname = host[1][0]
        else:
            hostname = host[0]
    except socket.herror:
        hostname = ip
    return hostname
