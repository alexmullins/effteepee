# EffTeePee Client

import socket
import sys

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
        self.error = None
        self.closed = False
        return
    
    def get_error(self):
        """
        Returns the last error from the server and consumes it 
        returning None in the future until another error occurs.
        If no error is present returns None.
        """
        if self.error:
            err = self.error
            self.error = None
            return err
        return None

    def _close(self):
        """
        Will centralize our connection close handling. 
        Close the connection and set closed to True.
        """
        self.closed = True
        self.socket.close()
        return
    
    def connect(self, host, port):
        """
        Connect the clients socket to the server at 
        host:port. Will raise an exception.
        """
        # create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return

    def handshake(self, username, password):
        """
        Will try and authenticate with the server. Return True if successful 
        or False otherwise and the server will close the connection.
        """
        msg = create_client_hello_msg(username,password)
        sendmsg(self.socket, msg["id"], msg)
        (rid, msg) = recvmsg(self.socket)
        if rid == MsgType.ErrorResponse:
            self.error = msg["code"]
            self._close()
            return False
        if rid == MsgType.ServerHello:
            self.username = username 
            self.binary = msg["binary"]
            self.compression = msg["compression"]
            self.encryption = msg["encryption"]
            return True
        return False
    
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
        """
        msg = create_quit_request_msg()
        sendmsg(self.socket, msg["id"], msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.QuitResponse:
            print("Did not receive quit response from server")
        self._close()
    
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
    if len(sys.argv) < 3:
        print("Missing <ip> <port> to connect to.")
        return 1
    ip, port = sys.argv[1], int(sys.argv[2])
    username = input("Username: ")
    password = input("Password: ")
    if len(username) == 0 or len(password) == 0:
        print("Invalid username and password.")
        return 1
    client = EffTeePeeClient()
    try:
        client.connect(ip ,port)
    except OSError as err:
        print("Error trying to connect: " + err)
        return 1
    try:
        authed = client.handshake(username, password)
        if not authed:
            print("Could not auth: " + str(client.get_error()))
            return 0
        print("Welcome {}, type 'help' to get a list of commands.".format(client.username))
        while not client.closed:
            command = input("> ")
            if command == "help":
                print_help()
            if command == "quit":
                client.quit()
            else:
                print("Unknown command. Type 'help' to get a list of commands.")
    except ConnectionClosedException:
        print("Connection closed.")
    return


def print_help():
    help_str = '''Supported Commands
name - description

cd - Change directory on the server.
ls - Display files and folders in the current directory.
dir - Display files and folders in the current directory.
get - Download a file from the server.
put - Upload a file to the server.
mget - Download multiple files from the server.
mput - Upload multiple files to the server.
binary - Set the file transfer mode to binary (default).  
quit - Quit the program.
compress - Set compression on the file transfers.
encrypt - Set encryption on the file transfers. 
normal - Reset to no encryption or compression on file transfers.
'''
    print(help_str)

if __name__ == '__main__':
    sys.exit(int(main() or 0))
