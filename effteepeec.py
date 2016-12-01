# EffTeePee Client

import socket
import sys
import getpass
import re
import os
from os.path import isfile, join

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
            self.error = msg.error_code
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
        msg = CDRequest(directory)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.CDResponse:
            return False
        return True
    
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
    
    def get(self, filenames):
        """
        Get a file from a directory on the server and save it to
        the local host machine. 
        """
        msg = GetRequest(filenames)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid == MsgType.ErrorResponse:
            return False
        if rid != MsgType.GetResponse:
            # protocol error, close conn.
            print("Expected a GetResponse, got: {}".format(msg))
            self._close()
            return False
        # Read file from server 
        print("Got GetResponse")
        num_files = msg.num_files
        cwd = os.getcwd()
        return get_files(self.socket, cwd, num_files, self.compression, self.encryption)

    def put(self, filenames):
        """
        Put a file from the local host machine on the server in its 
        current working directory. 
        """
        cwd = os.getcwd()
        # check all files exist 
        for f in filenames:
            if not isfile(join(cwd, f)):
                print("{} does not exist".format(join(cwd, f)))
                return False
        msg = PutRequest(len(filenames))
        sendmsg(self.socket, msg)
        ok = put_files(self.socket, cwd, filenames, self.compression, self.encryption)
        if not ok:
            return False
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.PutResponse:
            return False
        return True
        
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
        Toggle binary mode on the connection. 
        Doesn't do anything at the moment. Returns
        true if everything went alright
        """
        value = not self.binary
        msg = ChangeSettingsRequest("binary", value)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.ChangeSettingsResponse:
            return False
        self.binary = value
        return True
    
    def toggle_compression(self):
        """
        Toggle compression on the connection. Returns
        true if everything went alright.
        """
        value = not self.compression
        msg = ChangeSettingsRequest("compression", value)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.ChangeSettingsResponse:
            return False
        self.compression = value
        return True
    
    def toggle_encryption(self):
        """
        Toggle encryption on the connection. Returns
        true if everything went alright.
        """
        value = not self.encryption
        msg = ChangeSettingsRequest("encryption", value)
        sendmsg(self.socket, msg)
        (rid, msg) = recvmsg(self.socket)
        if rid != MsgType.ChangeSettingsResponse:
            return False
        self.encryption = value
        return True
    
    def normal(self):
        """
        Resets the compression and encryption to Off. Returns 
        truen if everything went alright.
        """
        if self.encryption:
            ok1 = self.toggle_encryption()
        else: ok1 = False
        if self.compression:
            ok2 = self.toggle_compression()
        else: ok2 = False
        return (ok1 or ok2)
        
def main():
    #if len(sys.argv) < 3:
        #print("Missing <ip> <port> to connect to.")
        #return 1
    #ip, port = sys.argv[1], int(sys.argv[2])
    ip, port = input("Ip (localhost): "), 12345
    if ip == "":
        ip = "localhost"
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
    # if not re.match("[^@]+@[^@]+\.[^@]+", password):
    #     print("Invalid password.")
    #     return 1
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
            elif command == "encrypt":
                ok = client.toggle_encryption()
                if not ok:
                    print("Could not change setting.")
            elif command == "compress":
                ok = client.toggle_compression()
                if not ok:
                    print("Could not change setting.")
            elif command == "binary":
                ok = client.toggle_binary()
                if not ok:
                    print("Could not change setting.")
            elif command == "normal":
                ok = client.normal()
                if not ok:
                    print("Could not change setting.")
            elif command == "settings":
                print("Binary: ", client.binary)
                print("Compression: ", client.compression)
                print("Encryption: ", client.encryption)
            elif command == "cd":
                ok = client.cd(args)
                if not ok:
                    print("Could not change directory.")
            elif command == "get":
                filename = args.split(" ")
                if len(filename) > 1:
                    print("Can only GET 1 file at a time. Use MGET instead.")
                    continue
                ok = client.get(filename)
                if not ok:
                    print("Could not get {} from the server.".format(filename))
            elif command == "mget":
                filenames = args.split(" ")
                ok = client.get(filenames)
                if not ok:
                    print("Could not get {} from the server.".format(filenames))
            elif command == "put":
                filename = args.split(" ")
                if len(filename) > 1:
                    print("Can only PUT 1 file at a time. Use MPUT instead.")
                    continue
                ok = client.put(filename)
                if not ok:
                    print("Could not get {} from the server.".format(filename))
            elif command == "mput":
                filenames = args.split(" ")
                ok = client.put(filenames)
                if not ok:
                    print("Could not get {} from the server.".format(filenames))
            else:
                print("Unknown command. Type 'help' to get a list of commands.")
    except ConnectionClosedException:
        print("Connection closed.")
    return


def print_help():
    help_str = '''Supported Commands
name - (arguments) - description

cd - (path) - Change directory on the server. 
ls - (path) - Display files and folders in the current directory.
dir - (path) - Display files and folders in the current directory.
get - (file1) - Download a file from the server.
put - (file1) - Upload a file to the server.
mget - (file1, file2, ...) - Download multiple files from the server.
mput - (file1, file2, ...) - Upload multiple files to the server.
binary - () - Toggle binary mode on the connection. (not implemented)
compress - () - Toggle compression on the file transfers.
encrypt - () - Toggle encryption on the file transfers.
normal - () - Reset to no encryption and no compression on file transfers.
settings - () - Print the current connection settings.
quit - () - Quit the program.

Example command call:
"> get textfile.txt"
"> mget textfile.txt binfile.bin"
'''
    print(help_str)

if __name__ == '__main__':
    sys.exit(int(main() or 0))
