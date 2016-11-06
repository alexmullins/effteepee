import pathlib
import enum

DEFAULT_USER_FILE = str(pathlib.Path('.', 'data', 'userfile.txt'))
DEFAULT_FILE_CHUNK_SIZE = 8192

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

class ConnectionClosedException(Exception):
    pass

class UnknownMsgTypeException(Exception):
    def __init__(self, code):
        self.code = code 

class ErrorCodes(enum.IntEnum):
    # Fatal Errors 10-19 (server will close connection)
    FailedAuthentication = 10
    UnknownRequest = 11
    ConnectionClosed = 12

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

    TextRequest = 20
    TextResponse = 21

def create_client_hello_msg(username, password):
    d = dict()
    d["id"] = MsgType.ClientHello
    d["username"] = username
    d["password"] = password
    return d

def encode_client_hello(msg):
    """
    Returns the byte sequence for a ClientHello 
    that can be written to the connection. Function 
    assumes that username and password lens are <= 255
    characters
    """
    username = msg["username"]
    password = msg["password"]
    userlen = int(len(username))
    passlen = int(len(password))
    msglen = 1 + 1 + userlen + passlen
    frame = bytearray()
    frame.extend(int(MsgType.ClientHello).to_bytes(1, byteorder="big"))
    frame.extend(msglen.to_bytes(2, byteorder="big"))
    frame.extend(userlen.to_bytes(1, byteorder="big"))
    frame.extend(passlen.to_bytes(1, byteorder="big"))
    frame.extend(username.encode("utf-8"))
    frame.extend(password.encode("utf-8"))
    return bytes(frame)

def decode_client_hello(data):
    """
    Will try and parse a ClientHello message from the binary data. 
    Returns a ClientHello stucture like:
    {
        "id": 1,
        "username": "alex",
        "password": "password",
    } 
    """
    userlen = int(data[0])
    passlen = int(data[1])
    useroff = 2
    passoff = useroff + userlen
    username = data[useroff:passoff].decode("utf-8")
    password = data[passoff:passoff+passlen].decode("utf-8")
    return create_client_hello_msg(username, password)

def create_server_hello_msg(binary, compression, encryption):
    d = dict()
    d["id"] = MsgType.ServerHello
    d["binary"] = binary
    d["compression"] = compression
    d["encryption"] = encryption
    return d

def encode_server_hello(msg):
    """
    Returns the byte sequence for a ServerHello 
    that can be written to the connection.
    """
    frame = bytearray()
    frame.extend(int(MsgType.ServerHello).to_bytes(1, byteorder="big"))
    frame.extend((3).to_bytes(2, byteorder="big"))
    frame.extend(int(msg["binary"]).to_bytes(1, byteorder="big"))
    frame.extend(int(msg["compression"]).to_bytes(1, byteorder="big"))
    frame.extend(int(msg["encryption"]).to_bytes(1, byteorder="big"))
    return bytes(frame)

def decode_server_hello(data):
    """
    Will try and parse a ServerHello message from binary data. 
    Returns ServerHello stucture like:
    {
        "id": 2,
        "binary": True,
        "compression": False,
        "encryption": False 
    } 
    """
    binary = bool(data[0])
    compression = bool(data[1])
    encryption = bool(data[2])
    return create_server_hello_msg(binary, compression, encryption)

def create_quit_request_msg():
    d = dict()
    d["id"] = MsgType.QuitRequest
    return d

def encode_quit_request(msg):
    frame = bytearray()
    frame.extend(int(MsgType.QuitRequest).to_bytes(1, byteorder="big"))
    frame.extend((0).to_bytes(2, byteorder="big"))
    return bytes(frame)

def decode_quit_request(data):
    return create_quit_request_msg()

def create_quit_response_msg():
    d = dict()
    d["id"] = MsgType.QuitResponse
    return d

def encode_quit_response(msg):
    frame = bytearray()
    frame.extend(int(MsgType.QuitResponse).to_bytes(1, byteorder="big"))
    frame.extend((0).to_bytes(2, byteorder="big"))
    return bytes(frame)

def decode_quit_response(data):
    return create_quit_response_msg()

def create_error_response_msg(code):
    d = dict()
    d["id"] = MsgType.ErrorResponse
    d["code"] = ErrorCodes(code)
    return d

def encode_error_response(msg):
    frame = bytearray()
    frame.extend(int(MsgType.ErrorResponse).to_bytes(1, byteorder="big"))
    frame.extend((1).to_bytes(2, byteorder="big"))
    frame.extend(int(msg["code"]).to_bytes(1, byteorder="big"))
    return bytes(frame)

def decode_error_response(data):
    """
    Will try and parse a ErrorResponse message from binary data.
    Returns an ErrorResponse structure like:
    {
        "id": 15,
        "code": 10
    }
    """
    return create_error_response_msg(data[0])

def create_ls_request_msg(path):
    d = dict()
    d["id"] = MsgType.LSRequest
    d["path"] = path
    return d

def encode_ls_request(msg):
    path_len = len(msg["path"])
    frame = bytearray()
    frame.extend(int(MsgType.LSRequest).to_bytes(1, byteorder="big"))
    frame.extend(path_len.to_bytes(2, byteorder="big"))
    frame.extend(msg["path"].encode("utf-8"))
    return bytes(frame)

def decode_ls_request(data):
    path = data.decode("utf-8")
    return create_ls_request_msg(path) 

def create_ls_response_msg(folders, files):
    """
    folders and files are a list of strings 
    that contain the respective folders and files 
    found in the ls request path. 
    """
    d = dict()
    d["id"] = MsgType.LSResponse
    d["folders"] = folders 
    d["files"] = files 
    return d 

def encode_ls_response(msg):
    folders_str = ";".join(msg["folders"])
    folders_len = len(folders_str)
    files_str = ";".join(msg["files"])
    files_len = len(files_str)
    msg_len = 4 + 4 + folders_len + files_len

    frame = bytearray()
    frame.extend(int(MsgType.LSResponse).to_bytes(1, byteorder="big"))
    frame.extend(msg_len.to_bytes(2, byteorder="big"))
    frame.extend(folders_len.to_bytes(4, byteorder="big"))
    frame.extend(files_len.to_bytes(4, byteorder="big"))
    frame.extend(folders_str.encode("utf-8"))
    frame.extend(files_str.encode("utf-8"))
    return bytes(frame)

def decode_ls_response(data):
    folders_len = int.from_bytes(data[0:4], byteorder="big")
    files_len = int.from_bytes(data[4:8], byteorder="big")
    folders_str = data[8:8+folders_len].decode("utf-8")
    files_str = data[8+folders_len:8+folders_len+files_len].decode("utf-8")
    folders = folders_str.split(";")
    files = files_str.split(";")
    return create_ls_response_msg(folders, files)

def recvmsg(socket):
    """
    recvmsg will read an effteepee protocol message
    from the socket. it will return a tuple 
    (msgid, msg) where msgid is the id for the MsgType
    and msg is a structure matching the MsgType. 
    """
    # recv the id 
    # recv the 2-byte msg len. 
    # read msg len bytes from the socket. 
    # pass data to parse method to return structure. 
    msgid = recvid(socket)
    if not msgid in decoders:
        raise UnknownMsgTypeException(msgid)
    msglen = int.from_bytes(recvall(socket, 2), byteorder="big")
    data = recvall(socket, msglen)
    dec = decoders[msgid]
    msg = dec(data)
    return (msgid, msg)

def sendmsg(socket, msgid, msg):
    """
    sendmsg will send an effteepee protocol message
    on the socket. 
    """
    if not msgid in encoders:
        raise UnknownMsgTypeException(msgid)
    enc = encoders[msgid]
    data = enc(msg)
    socket.sendall(data)

def recvid(socket):
    """
    recvid will receive a message's id 
    and return a MsgType.
    """
    rid = recvall(socket, 1)
    msgid = MsgType(int.from_bytes(rid, byteorder="big"))
    return msgid

def recvall(socket, n):
    """
    recvall will receive all n bytes of information
    and return it as a bytes sequence. Raises a 
    ConnectionClosedException if the socket closes.
    """
    frame = bytearray()
    while len(frame) < n:
        packet = socket.recv(n - len(frame))
        if not packet:
            raise ConnectionClosedException()
        frame.extend(packet)
    return bytes(frame)

def encode_file_data(data, compression, encryption, key):
    """
    encode will do the job of 1st encrypting data 
    with key if encryption flag is True. Then will 
    compress the resulting data if compression is True.
    Will return the resulting data. If neither is True 
    then encode is a NOP.
    """
    pass

def decode_file_data(data, compression, encryption, key):
    """
    decode will undo what encode has done. It will
    first decompress data if compression flag is True.
    Then will decrypt data with key if encryption flag 
    is True. Will return the resulting data. If neither
    is True then decode is a NOP.
    """
    pass

def create_text_message(text, comtyp):
    d = dict()
    d["id"] = MsgType.TextRequest
    d["text"] = text
    return d

def encode_text(msg):
    frame = bytearray()
    frame.extend(int(MsgType.TextRequest).to_bytes(1, byteorder="big"))
    frame.extend(len(msg["text"]).to_bytes(2, byteorder="big"))
    frame.extend(msg["text"].encode("utf-8"))
    return bytes(frame)

def decode_text(data):
    text = str(data)
    return create_text_message(text, ' ')


decoders = dict()
decoders[MsgType.ClientHello] = decode_client_hello
decoders[MsgType.ServerHello] = decode_server_hello
decoders[MsgType.TextRequest] = decode_text
decoders[MsgType.TextResponse] = decode_text
decoders[MsgType.CDRequest] = decode_text
# decoders[MsgType.CDResponse] =
decoders[MsgType.LSRequest] = decode_ls_request
decoders[MsgType.LSResponse] = decode_ls_response
# decoders[MsgType.GetRequest] =
# decoders[MsgType.GetResponse] =
# decoders[MsgType.PutRequest] =
# decoders[MsgType.PutResponse] =
decoders[MsgType.QuitRequest] = decode_quit_request
decoders[MsgType.QuitResponse] = decode_quit_response
# decoders[MsgType.ChangeSettingsRequest] =
# decoders[MsgType.ChangeSettingsResponse] =
decoders[MsgType.ErrorResponse] = decode_error_response
# decoders[MsgType.File] =
# decoders[MsgType.FileChunk] =
# decoders[MsgType.EndOfFileChunks] =
# decoders[MsgType.EndOfFiles] =

encoders = dict()
encoders[MsgType.ClientHello] = encode_client_hello
encoders[MsgType.ServerHello] = encode_server_hello
encoders[MsgType.TextRequest] = encode_text
encoders[MsgType.TextResponse] = encode_text
encoders[MsgType.CDRequest] = encode_text
# encoders[MsgType.CDResponse] =
encoders[MsgType.LSRequest] = encode_ls_request
encoders[MsgType.LSResponse] = encode_ls_response
# encoders[MsgType.GetRequest] =
# encoders[MsgType.GetResponse] =
# encoders[MsgType.PutRequest] =
# encoders[MsgType.PutResponse] =
encoders[MsgType.QuitRequest] = encode_quit_request
encoders[MsgType.QuitResponse] = encode_quit_response
# encoders[MsgType.ChangeSettingsRequest] =
# encoders[MsgType.ChangeSettingsResponse] =
encoders[MsgType.ErrorResponse] = encode_error_response
# encoders[MsgType.File] =
# encoders[MsgType.FileChunk] =
# encoders[MsgType.EndOfFileChunks] =
# encoders[MsgType.EndOfFiles] =

