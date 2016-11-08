# EffTeePee Client

import socket
import sys
import getpass
import re

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
        msg = ClientHello(username,password)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid == MsgType.ErrorResponse:
            self.error = msg["code"]
            self._close()
            return False
        if rid == MsgType.ServerHello:
            self.username = username 
            self.binary = msg.binary
            self.compression = msg.compression
            self.encryption = msg.encryption
            return True
        return False
    
    def cd(self, directory):
        """
        Change directory on the server. Return True if everything 
        went ok.
        """
        print(directory, "cd")
    
    def ls(self, path):
        """
        Retuns a listing of the files and folders in the 
        path on the remote server. Returns a LSResponse object.
        """
        msg = LSRequest(path)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid == MsgType.ErrorResponse:
            print("TODO: Got an error")
            return None
        elif rid == MsgType.LSResponse:
            return msg
        print("Got an unknown response")
        return None 
    
    def get(self, file_name):
        """
        Get a file from a directory on the server and save it to
        the local host machine. 
        """
        print(file_name, "get")
    
    def put(self, file_name):
        """
        Put a file from the local host machine on the server in its 
        current working directory. 
        """
        print(file_name, "put")
    
    def mget(self, file_names):
        """
        Same as put but for multiple files.
        """
        print(file_names, "mget")
    
    def mput(self, file_names):
        """
        Same as get but for multiple files.
        """
        print(file_names, "mput")
    
    def quit(self):
        """
        Sends a quit request to the server for proper cleanup. 
        """
        msg = QuitRequest()
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.QuitResponse:
            print("Did not receive quit response from server")
        self._close()
    
    def toggle_binary(self):
        """
        Toggle binary mode on the connection. Doesn't do anything at the moment.
        """
        print("binary")
    
    def toggle_compression(self):
        """
        Toggle compression on the connection.
        """
        print("compression")
    
    def toggle_encryption(self):
        """
        Toggle encryption on the connection.
        """
        print("encryption")
    
    def normal(self):
        """
        Resets the compression and encryption to Off.
        """
        print("normal")
        
def main():
    #if len(sys.argv) < 3:
        #print("Missing <ip> <port> to connect to.")
        #return 1
    #ip, port = sys.argv[1], int(sys.argv[2])
    ip, port = input("Ip: "), 12345
    client = EffTeePeeClient()
    try:
        client.connect(ip ,port)
    except OSError as err:
        print("Error trying to connect: " + err)
        return 1

    username = input("Username: ")
    password = getpass.getpass("Password: ")
    if len(username) == 0 or len(password) == 0:
        print("Invalid username or password.")
        return 1
   # if re.match("^([a-z][A-Z][0-9][@][a-z][A-Z][0-9][.][a-z][A-Z][0-9])$", password) == None:
        #print("Invalid password.")
        #return 1
    try:
        authed = client.handshake(username, password)
        if not authed:
            print("Could not auth: " + str(client.get_error()))
            return 0
        print("Welcome {}, type 'help' to get a list of commands.".format(client.username))
        while not client.closed:
            command_str = input("> ")
            command = None 
            args = None
            com = command_str.split(' ', 1)
            command = com[0]
            if len(com) > 1:
                args = com[1]
            # Match command
            if command == "help":
                print_help()
            elif command == "quit":
                client.quit()
            elif command == "ls" or command == "dir":
                if args == None:
                    args = "."
                msg = client.ls(args)
                if msg is None:
                    print("Could not ls with path: ", args)
                print("Folders:")
                for f in msg.folders:
                    print("\t", f)
                print("Files:")
                for f in msg.files:
                    print("\t", f)
            else:
                print("Unknown command. Type 'help' to get a list of commands.")
    except ConnectionClosedException:
        print("Connection closed.")
    return


def print_help():
    help_str = ''''Supported Commands
name - description

cd - Change directory on the server. (Takes one argument.)
ls - Display files and folders in the current directory. (Takes no argument.)
dir - Display files and folders in the current directory. (Takes no argument.)
get - Download a file from the server. (Takes one argument.)
put - Upload a file to the server. (Takes one argument.)
mget - Download multiple files from the server. (Takes multiple arguments.)
mput - Upload multiple files to the server. (Takes multiple arguments.)
binary - Set the file transfer mode to binary (default). (Takes no argument.)
compress - Toggle compression on the file transfers. (Takes no argument.)
encrypt - Toggle encryption on the file transfers. (Takes no argument.)
normal - Reset to no encryption or compression on file transfers. (Takes no argument.)
quit - Quit the program. (Takes no argument.)

Example command call:
"> get textfile.txt"
"> mget textfile.txt binfile.bin"
'''
    print(help_str)

if __name__ == '__main__':
    sys.exit(int(main() or 0))
