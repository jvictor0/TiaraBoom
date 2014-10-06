import socket
import sys

def Reply(con):
    pass

if __name__ == '__main__':

    server_address = ('localhost', 10001)
    con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
