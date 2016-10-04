# EffTeePee Server

import socketserver
import hashlib


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
        # connection variables
        self.binary = True 
        self.compression = False 
        self.encryption = False
        self.username = None
        self.root_directory = None
        self.quit = False

        self.handlers = dict()
        # self.handlers[MsgType.CDRequest] = self._handle_cd
        # self.handlers[MsgType.LSRequest] = self._handle_ls
        # self.handlers[MsgType.GetRequest] = self._handle_get
        # self.handlers[MsgType.PutRequest] = self._handle_put
        self.handlers[MsgType.QuitRequest] = self._handle_quit
        # self.handlers[MsgType.ChangeSettingsRequest] = self._handle_change_setting

    def handle(self): 
        # Handshake 
        ok = self._handshake()
        if not ok:
            self.close()
            return
        
        self._handle_commands()

    def send_error_response(self, code):
        er = create_error_response(code)
        self.request.sendall(er)
        return
    
    def close(self):
        """
        Will centralize our connection close handling. 
        Close the connection and set quit to True
        so our _handle_commands will stop processing.
        """
        self.request.close()
        self.quit = True 
        return

    def _handle_quit(self):
        msg = create_quit_response()
        self.request.sendall(msg)
        self.close()
        return 

    def _handle_commands(self):
        # enter into a for loop and try
        # to read the request id and send it the
        # appropriate handler.
        while not self.quit:
            rid = recvid(self.request)
            if not rid:
                self.close()
            if rid not in self.handlers:
                print("Unknown handler: {}".format(rid))
            handler = self.handlers[rid]
            handler()
    
    def _handshake(self):
        # check to make sure we got a ClientHello
        rid = recvid(self.request)
        if not rid or rid != MsgType.ClientHello:
            print("failed to receive ClientHello: {}".format(rid))
            return False
        
        ok, res = parse_client_hello(self.request)
        if not ok:
            return False
        # check authentication
        username = res["username"]
        password = res["password"]
        ok, directory = self.server.auth_user(username, password)
        if not ok:
            self.send_error_response(ErrorCodes.FailedAuthentication)
            print("{} failed to authenticate.".format(username))
            return False

        print("{} authenticated.".format(username))
        self.username = username
        self.root_directory = directory
        # send back ServerHello
        data = create_server_hello(self.binary, self.compression, self.encryption)
        self.request.sendall(data)
        return True


def main():
    hostport = ("localhost", 8080)
    server = EffTeePeeServer(hostport, EffTeePeeHandler)
    ip, port = server.server_address
    print("Started EffTeePee server on {}:{}".format(ip, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    import sys
    sys.exit(int(main() or 0))