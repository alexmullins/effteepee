# EffTeePee Server

import socketserver
import hashlib
import sys

from common import *

class EffTeePeeServer(socketserver.ThreadingTCPServer):
    """
    Code example from https://docs.python.org/3.5/library/socketserver.html
    This is the EffTeePee server that will create a new
    thread for each incoming connection. It will hold a 
    mapping of users with their associated password hash
    and root directory. 
    """

    def __init__(self, hostport, handler, user_file=DEFAULT_USER_FILE):
        super().__init__(hostport, handler)
        # declare instance variables
        self.users = dict()
        self.parse_user_file(user_file)
        return
    
    def parse_user_file(self, user_file):
        with open(user_file) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("::")
                name = parts[0]
                pass_hash = parts[1]
                directory = parts[2]
                # put into user dict
                self.users[name] = {
                    "pass_hash": pass_hash,
                    "directory": directory
                }
        return
    
    def auth_user(self, username, password):
        """
        auth_user will verify that the user is present
        in the users dict and then compare the password
        given to the hash in the users dict. Returns 
        a tuple (ok, root_directory). ok is a bool 
        and root_directory is a string from the users
        dict.
        """
        if username in self.users:
            user = self.users[username]
            test_pass_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            if user["pass_hash"] == test_pass_hash:
                return (True, user["directory"])
        return (False, "")    


class EffTeePeeHandler(socketserver.BaseRequestHandler):
    """
    Each connection will create a new EffTeePeeHandler. 
    """
    def setup(self):
        # setup is automatically called by the server when creating a new connection.
        # connection variables
        self.binary = True 
        self.compression = False 
        self.encryption = False
        self.username = None
        self.root_directory = None
        self.quit = False
        self.handlers = dict()
        self.handlers[MsgType.ClientHello] = self._handshake
        # self.handlers[MsgType.CDRequest] = self._handle_cd
        # self.handlers[MsgType.LSRequest] = self._handle_ls
        # self.handlers[MsgType.GetRequest] = self._handle_get
        # self.handlers[MsgType.PutRequest] = self._handle_put
        self.handlers[MsgType.QuitRequest] = self._handle_quit
        # self.handlers[MsgType.ChangeSettingsRequest] = self._handle_change_setting
        return

    def handle(self):
        """
        Called by the EffTeePee server when 
        it accepts a new connection.
        """
        try:
            self._handle_commands()
        except ConnectionClosedException:
            print("Connection closed unexpectedly")
            self._close()
        return
    
    def _handle_commands(self):
    # enter into a for loop and try
    # to read the request id and send it the
    # appropriate handler.
        while not self.quit:
            rid, msg = recvmsg(self.request)
            if rid not in self.handlers:
                print("Unknown handler: {}".format(rid))
                self._close()
            handler = self.handlers[rid]
            if not self.username and rid != MsgType.ClientHello:
                # We haven't authenticated and we didn't get a ClientHello
                # which is a protocol error so abort.
                print("Client did not try to authenticate")
                self._close()
                continue
            handler(msg)
        return
    
    def _close(self):
        """
        Will centralize our connection close handling. 
        Close the connection and set quit to True
        so our _handle_commands will stop processing.
        """
        self.request.close()
        self.quit = True 
        return

    def _handshake(self, msg):
        # check to make sure we got a ClientHello
        print("Called handshake")
        # check authentication
        username = msg["username"]
        password = msg["password"]
        ok, directory = self.server.auth_user(username, password)
        if not ok:
            print("{} failed to authenticate.".format(username))
            msg = create_error_response_msg(ErrorCodes.FailedAuthentication)
            sendmsg(self.request, msg["id"], msg)
            self._close()
            return
        print("{} authenticated.".format(username))
        self.username = username
        self.root_directory = directory
        # send back ServerHello
        msg = create_server_hello_msg(self.binary, self.compression, self.encryption)
        sendmsg(self.request, msg["id"], msg)
        return

    def _handle_quit(self, msg):
        msg = create_quit_response_msg()
        sendmsg(self.request, msg["id"], msg)
        self._close()
        print("{} has quit.".format(self.username))
        return 

def main():
    if len(sys.argv) < 3:
        print("Missing <ip> <port> to listen on.")
        return 1
    ip, port = sys.argv[1], int(sys.argv[2])
    server = EffTeePeeServer((ip, port), EffTeePeeHandler)
    print("Starting EffTeePee server on {}:{}".format(ip, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down EffTeePee server.")
        server.shutdown()
        server.server_close()
    return

if __name__ == '__main__':
    sys.exit(int(main() or 0))