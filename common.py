import pathlib
import enum

DEFAULT_USER_FILE = str(pathlib.Path('.', 'data', 'userfile.txt'))
DEFAULT_FILE_CHUNK_SIZE = 8192
host, port = "localhost", 8080

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ErrorCodes(enum.IntEnum):
    # Fatal Errors 10-19 (server will close connection)
    FailedAuthentication = 10

def is_fatal_error(code):
    if code < 20:
        return True
    return False

class MsgType(enum.IntEnum):
    # Normal command message types
    ClientHello = 1
    ServerHello = 2
    CDRequest = 3
    CDResponse = 4
    LSRequest = 5
    LSResponse = 6
    GetRequest = 7
    GetResponse = 8
    PutRequest = 9
    PutResponse = 10
    QuitRequest = 11
    QuitResponse = 12
    ChangeSettingsRequest = 13
    ChangeSettingsResponse = 14
    
    # Error message type
    ErrorResponse = 15

    # File data message type
    File = 16
    FileChunk = 17
    EndOfFileChunks = 18
    EndOfFiles = 19

def create_quit_request():
    frame = bytearray()
    frame.extend(int(MsgType.QuitRequest).to_bytes(1, byteorder="big"))
    return bytes(frame)

def create_quit_response():
    frame = bytearray()
    frame.extend(int(MsgType.QuitResponse).to_bytes(1, byteorder="big"))
    return bytes(frame)

def create_error_response(code):
    frame = bytearray()
    frame.extend(int(MsgType.ErrorResponse).to_bytes(1, byteorder="big"))
    frame.extend(int(code).to_bytes(1, byteorder="big"))
    return bytes(frame)

def create_client_hello(username, password):
    """
    Returns the byte sequence for a ClientHello 
    that can be written to the connection. Function 
    assumes that username and password lens are <= 255
    characters
    """
    frame = bytearray()
    frame.extend(int(MsgType.ClientHello).to_bytes(1, byteorder="big"))
    frame.extend(int(len(username)).to_bytes(1, byteorder="big"))
    frame.extend(int(len(password)).to_bytes(1, byteorder="big"))
    frame.extend(username.encode("utf-8"))
    frame.extend(password.encode("utf-8"))
    return bytes(frame)

def create_server_hello(binary, compression, encryption):
    """
    Returns the byte sequence for a ServerHello 
    that can be written to the connection.
    """
    frame = bytearray()
    frame.extend(int(MsgType.ServerHello).to_bytes(1, byteorder="big"))
    frame.extend(int(binary).to_bytes(1, byteorder="big"))
    frame.extend(int(compression).to_bytes(1, byteorder="big"))
    frame.extend(int(encryption).to_bytes(1, byteorder="big"))
    return bytes(frame)

def parse_error_response(socket):
    """
    Will try and parse a ErrorResponse message from the socket.
    Returns a tuple (True, message) if everything went ok.
    message will be a ErrorResponse structure like:
    {
        "id": 15,
        "code": 10
    }
    """
    buf = recvall(socket, 1)
    if not buf:
        return (False, None)
    d = dict()
    d["id"] = MsgType.ErrorResponse
    d["code"] = ErrorCodes(buf[0])
    return (True, d)

def parse_server_hello(socket):
    """
    Will try and parse a ServerHello message from the socket. 
    Returns a tuple (True, message) if everything went ok. 
    message will be a ServerHello stucture like:
    {
        "id": 2,
        "binary": True,
        "compression": False,
        "encryption": False 
    } 
    """
    buf = recvall(socket, 3)
    if not buf:
        return (False, None)
    d = dict()
    d["id"] = MsgType.ServerHello
    d["binary"] = bool(buf[0])
    d["compression"] = bool(buf[1])
    d["encryption"] = bool(buf[2])
    return (True, d)

def parse_client_hello(socket):
    """
    Will try and parse a ClientHello message from the socket. 
    Returns a tuple (True, message) if everything went ok. 
    message will be a ClientHello stucture like:
    {
        "id": 1,
        "username": "alex",
        "password": "password",
    } 
    """
    buf = recvall(socket, 2)
    if not buf:
        return (False, None)
    ulen = int(buf[0])
    plen = int(buf[1])
    ubuf = recvall(socket, ulen)
    pbuf = recvall(socket, plen)
    if not ubuf or not pbuf:
        return (False, None)
    d = dict()
    d["id"] = MsgType.ClientHello
    d["username"] = ubuf.decode("utf-8")
    d["password"] = pbuf.decode("utf-8")
    return (True, d)

def recvall(socket, n):
    """
    recvall will receive all n bytes of information
    and return it as a bytes sequence. Returns None 
    if the socket closes.
    """
    frame = bytearray()
    while len(frame) < n:
        packet = socket.recv(n - len(frame))
        if not packet:
            return None
        frame.extend(packet)
    return bytes(frame)

def recvid(socket):
    """
    recvid will receive a message's id 
    and return a MsgType or None if something 
    went wrong or the socket is closed.
    """
    rid = recvall(socket, 1)
    if not rid:
        return None 
    msg = MsgType(int.from_bytes(rid, byteorder="big"))
    return msg 