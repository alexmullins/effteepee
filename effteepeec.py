# EffTeePee Client

import socket 
from common import *

class EffTeePeeClient():
    def __init__(self):
        """
        Setup the EffTeePee Client.
        """
        # declare instance variables
        self.username = None 
        self.binary = False 
        self.compression = False 
        self.encryption = False 
        self.socket = None
        self.encrypt_key = None
    
    def connect(self, host, port):
        """
        Connect the clients socket to the server at 
        host:port. Will raise an exception.
        """
        # create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def handshake(self, username, password):
        """
        Will try and authenticate with the server. Return True if successful 
        or False otherwise and the server will close the connection.
        """
        msg = create_client_hello(username,password)
        self.socket.sendall(msg)
        rid = recvid(self.socket)
        if not rid or rid != MsgType.ServerHello:
            self.socket.close()
            return False  
        ok, res = parse_server_hello(self.socket)
        if not ok:
            self.socket.close()
            return False
        self.username = username 
        self.binary = res["binary"]
        self.compression = res["compression"]
        self.encryption = res["encryption"]
        return True
    
    def cd(self, directory):
        """
        Change directory on the server. Return True if everything 
        went ok.
        """
        pass 
    
    def ls(self):
        """
        Return a list the files and folders in the current directory.
        The structure returned will look like:
        {
            "folders": [...],
            "files": [...]
        }
        """
        pass 
    
    def dir(self):
        """
        Calls self.ls()
        """
        return self.ls() 
    
    def get(self, file_name):
        """
        Get a file from a directory on the server and save it to
        the local host machine. 
        """
        pass 
    
    def put(self, file_name):
        """
        Put a file from the local host machine on the server in its 
        current working directory. 
        """
        pass 
    
    def mget(self, file_names):
        """
        Same as put but for multiple files.
        """
        pass 
    
    def mput(self, file_names):
        """
        Same as get but for multiple files.
        """
        pass 
    
    def quit(self):
        """
        Sends a quit request to the server for proper cleanup. 
        Returns True if everything went ok.
        """
        msg = create_quit_request()
        self.socket.sendall(msg)

        rid = recvid(self.socket)
        if not rid or rid != MsgType.QuitResponse:
            print("Did not receive quit response from server")
        self.socket.close()
    
    def toggle_binary(self):
        """
        Toggle binary mode on the connection. Doesn't do anything at the moment.
        """
        pass 
    
    def toggle_compression(self):
        """
        Toggle compression on the connection.
        """
        pass 
    
    def toggle_encryption(self):
        """
        Toggle encryption on the connection.
        """
        pass 
    
    def normal(self):
        """
        Resets the compression and encryption to Off.
        """
        pass


def main():
    client = EffTeePeeClient()
    try:
        client.connect(host,port)
    except OSError as err:
        print("Error trying to connect.")
        return 1
    
    username = input("Username:")
    password = input("Password:")
    authed = client.handshake(username, password)
    if not authed:
        print("Could not auth.")
        return 1
    print("authed as {}".format(client.username))

    client.quit()


if __name__ == '__main__':
    import sys
    sys.exit(int(main() or 0))