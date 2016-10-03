# EffTeePee Server

import socketserver
import hashlib
import pprint

from common import *

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

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
        debug_print("Users file: {}".format(pprint.pformat(self.users)))
    
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
    def handle(self):
        self.binary = True 
        self.compression = False 
        self.encryption = False
        self.username = None
        self.root_directory = None
        
        ok = self._handshake()
        if not ok:
            self.request.close()
            return
        print("Authenticated a user.")
    
    def _handshake(self):
        ok, res = parse_client_hello(self.request)
        if not ok:
            return False
        ok, directory = self.server.auth_user(res["username"], res["password"])
        if not ok:
            return False 
        self.username = res["username"]
        self.root_directory = directory

        data = create_server_hello(self.binary, self.compression, self.encryption)
        self.request.sendall(data)
        return True



def main():
    hostport = ("localhost", 8080)
    server = EffTeePeeServer(hostport, EffTeePeeHandler)
    ip, port = server.server_address
    print("started EffTeePee server on {}:{}".format(ip, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    import sys
    sys.exit(int(main() or 0))