import pathlib
import enum

DEFAULT_USER_FILE = str(pathlib.Path('.', 'data', 'userfile.txt'))
DEFAULT_FILE_CHUNK_SIZE = 8192
host, port = "localhost", 8080

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

def create_client_hello(username, password):
    """
    Returns the byte sequence for a ClientHello 
    that can be written to the connection. Function 
    assumes that username and password lens are <= 255
    characters
    """
    frame = bytearray()
    frame.append(MsgType.ClientHello)
    frame.append(len(username))
    frame.append(len(password))
    frame.extend(username.encode("utf-8"))
    frame.extend(password.encode("utf-8"))
    return bytes(frame)

def create_server_hello(binary, compression, encryption):
    """
    Returns the byte sequence for a ServerHello 
    that can be written to the connection.
    """
    frame = bytearray()
    frame.append(MsgType.ServerHello)
    frame.append(int(binary))
    frame.append(int(compression))
    frame.append(int(encryption))
    return bytes(frame)

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
    buf = recvall(socket, 4)
    if not buf or buf[0] != MsgType.ServerHello:
        return (False, None)
    d = dict()
    d["id"] = MsgType.ServerHello
    d["binary"] = bool(buf[1])
    d["compression"] = bool(buf[2])
    d["encryption"] = bool(buf[3])
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
    buf = recvall(socket, 3)
    if not buf or buf[0] != MsgType.ClientHello:
        return (False, None)
    ulen = int(buf[1])
    plen = int(buf[2])
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