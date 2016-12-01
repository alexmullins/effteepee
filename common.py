import pathlib
import enum
import abc
import lzma
from os.path import join

DEFAULT_USER_FILE = str(pathlib.Path('.', 'data', 'userfile.txt'))
DEFAULT_FILE_CHUNK_SIZE = 8192
ENCRYPTION_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" # or a random string

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

    UnknownSetting = 20
    BadCDPath = 21
    NotExists = 23
    PutFilesFailed = 23

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

class Message(metaclass=abc.ABCMeta):
    """
    Abstract base class for all MessageTypes.
    Each message should know how to encode itself
    to a byte array, and decode a byte array and
    update itself.
    """
    @abc.abstractmethod
    def id(self):
        """
        Should return the MsgType id for the 
        subclassed Message.
        """

    @abc.abstractmethod
    def encode(self):
        """
        Should encode all values and return a byte array.
        Should not worry about encoding the MsgType id or 
        the msg len value. That will be handle elsewhere.
        """

    @abc.abstractmethod
    def decode(self, data):
        """
        Should decode the given data byte array
        and set the appropriate member variables.
        Should not worry about decoding the MsgType id or 
        the msg len value from data, those will be stripped off.
        """

class ClientHello(Message):
    """
    ClientHello Message.
    """
    def __init__(self, username="",password=""):
        self.username = username
        self.password = password

    def id(self):
        return MsgType.ClientHello
    
    def encode(self):
        userlen = len(self.username)
        passlen = len(self.password)
        frame = bytearray()
        frame.extend(userlen.to_bytes(1, byteorder="big"))
        frame.extend(passlen.to_bytes(1, byteorder="big"))
        frame.extend(self.username.encode("utf-8"))
        frame.extend(self.password.encode("utf-8"))
        return bytes(frame)
    
    def decode(self, data):
        userlen = data[0]
        passlen = data[1]
        useroff = 2
        passoff = useroff + userlen
        self.username = data[useroff:passoff].decode("utf-8")
        self.password = data[passoff:passoff+passlen].decode("utf-8")


class ServerHello(Message):
    """
    ServerHello Message.
    """
    def __init__(self, binary=True, compression=False, encryption=False):
        self.binary = binary 
        self.compression = compression 
        self.encryption = encryption

    def id(self):
        return MsgType.ServerHello
    
    def encode(self):
        frame = bytearray()
        frame.extend(int(self.binary).to_bytes(1, byteorder="big"))
        frame.extend(int(self.compression).to_bytes(1, byteorder="big"))
        frame.extend(int(self.encryption).to_bytes(1, byteorder="big"))
        return bytes(frame) 
    
    def decode(self, data):
        self.binary = bool(data[0])
        self.compression = bool(data[1])
        self.encryption = bool(data[2])

class QuitRequest(Message):
    """
    QuitRequest Message. 
    """
    def id(self):
        return MsgType.QuitRequest

    def encode(self):
        return bytes()

    def decode(self, data):
        pass

class QuitResponse(Message):
    """
    QuitResponse Message. 
    """
    def id(self):
        return MsgType.QuitResponse

    def encode(self):
        return bytes() 
    
    def decode(self, data):
        pass 

class ErrorResponse(Message):
    """
    ErrorResponse Message. 
    """
    def __init__(self, error_code=None):
        self.error_code = error_code

    def id(self):
        return MsgType.ErrorResponse

    def encode(self):
        frame = bytearray()
        frame.extend(int(self.error_code).to_bytes(1, byteorder="big"))
        return bytes(frame) 
    
    def decode(self, data):
        self.error_code = ErrorCodes(data[0])

class LSRequest(Message):
    """
    LSRequest Message. 
    """
    def __init__(self, path=""):
        self.path = path

    def id(self):
        return MsgType.LSRequest

    def encode(self):
        frame = bytearray()
        frame.extend(self.path.encode("utf-8"))
        return bytes(frame)
    
    def decode(self, data):
        self.path = data.decode("utf-8")   

class LSResponse(Message):
    """
    LSResponse Message.
    """
    def __init__(self, folders=list(), files=list()):
        self.folders = folders
        self.files = files

    def id(self):
        return MsgType.LSResponse

    def encode(self):
        folders_str = ";".join(self.folders)
        folders_len = len(folders_str)
        files_str = ";".join(self.files)
        files_len = len(files_str)

        frame = bytearray()
        frame.extend(folders_len.to_bytes(4, byteorder="big"))
        frame.extend(files_len.to_bytes(4, byteorder="big"))
        frame.extend(folders_str.encode("utf-8"))
        frame.extend(files_str.encode("utf-8"))
        return bytes(frame)

    def decode(self, data):
        folders_len = int.from_bytes(data[0:4], byteorder="big")
        files_len = int.from_bytes(data[4:8], byteorder="big")
        folders_str = data[8:8+folders_len].decode("utf-8")
        files_str = data[8+folders_len:8+folders_len+files_len].decode("utf-8")
        self.folders = folders_str.split(";")
        self.files = files_str.split(";")

class CDRequest(Message):
    """
    CDRequest Message.
    """
    def __init__(self, path=""):
        self.path = path

    def id(self):
        return MsgType.CDRequest

    def encode(self):
        frame = bytearray()
        frame.extend(self.path.encode("utf-8"))
        return bytes(frame) 
    
    def decode(self, data):
        self.path = data.decode("utf-8") 

class CDResponse(Message):
    """
    CDResponse Message.
    """
    def id(self):
        return MsgType.CDResponse

    def encode(self):
        return bytes()
    
    def decode(self, data):
        pass

class GetRequest(Message):
    """
    GetRequest Message.
    """
    def __init__(self, filenames=None):
        self.filenames = filenames 

    def id(self):
        return MsgType.GetRequest

    def encode(self):
        file_str = ";".join(self.filenames)
        file_str_len = len(file_str)
        frame = bytearray()
        frame.extend(file_str_len.to_bytes(2, byteorder="big"))
        frame.extend(file_str.encode("utf-8"))
        return bytes(frame) 
    
    def decode(self, data):
        file_str_len = int.from_bytes(data[0:2], byteorder="big")
        file_str = data[2:2+file_str_len]
        self.filenames = file_str.decode('utf-8').split(";")
        return 

class GetResponse(Message):
    """
    GetResponse Message.
    """
    def __init__(self, num_files=0):
        self.num_files = num_files

    def id(self):
        return MsgType.GetResponse

    def encode(self):
        frame = bytearray()
        frame.extend(self.num_files.to_bytes(2, byteorder="big"))
        return bytes(frame)  

    def decode(self, data):
        self.num_files = int.from_bytes(data[0:2], byteorder="big")
        return

class PutRequest(Message):
    """
    PutRequest Message.
    """
    def __init__(self, num_files=0):
        self.num_files = num_files

    def id(self):
        return MsgType.PutRequest

    def encode(self):
        frame = bytearray()
        frame.extend(self.num_files.to_bytes(2, byteorder="big"))
        return bytes(frame)   
    
    def decode(self, data):
        self.num_files = int.from_bytes(data[0:2], byteorder="big")
        return 

class PutResponse(Message):
    """
    PutResponse Message.
    """
    def id(self):
        return MsgType.PutResponse

    def encode(self):
        return bytes() 
    
    def decode(self, data):
        pass

class ChangeSettingsRequest(Message):
    """
    ChangeSettingsRequest Message.
    """
    def __init__(self, setting="", value=False):
        self.setting = setting
        self.value = value

    def id(self):
        return MsgType.ChangeSettingsRequest

    def encode(self):
        setting_str_len = len(self.setting)

        frame = bytearray()
        frame.extend(setting_str_len.to_bytes(1, byteorder="big"))
        frame.extend(self.setting.encode("utf-8"))
        frame.extend(self.value.to_bytes(1, byteorder="big"))
        return bytes(frame) 
    
    def decode(self, data):
        settings_str_len = int(data[0])
        self.setting = data[1:1+settings_str_len].decode("utf-8")
        self.value = bool(data[-1])


class ChangeSettingsResponse(Message):
    """
    ChangeSettingsResponse Message.
    """
    def id(self):
        return MsgType.ChangeSettingsResponse

    def encode(self):
        return bytes() 
    
    def decode(self, data):
        pass

class File(Message):
    """
    File Message.
    """
    def __init__(self, filename=None):
        self.filename = filename

    def id(self):
        return MsgType.File

    def encode(self):
        filename_len = len(self.filename)

        frame = bytearray()
        frame.extend(filename_len.to_bytes(1, byteorder="big"))
        frame.extend(self.filename.encode("utf-8"))
        return bytes(frame)
    
    def decode(self, data):
        filename_len = int.from_bytes(data[0:1], byteorder="big")
        self.filename = data[1:1+filename_len].decode("utf-8")
        return

class FileChunk(Message):
    """
    FileChunk Message.
    """
    def __init__(self, data=None):
        self.data = data

    def id(self):
        return MsgType.FileChunk

    def encode(self):
        frame = bytearray()
        frame.extend(self.data)
        return bytes(frame)
    
    def decode(self, data):
        self.data = data

class EndOfFileChunks(Message):
    """
    EndOfFileChunks Message.
    """
    def id(self):
        return MsgType.EndOfFileChunks

    def encode(self):
        return bytes() 
    
    def decode(self, data):
        pass

class EndOfFiles(Message):
    """
    EndOfFiles Message.
    """
    def id(self):
        return MsgType.EndOfFiles

    def encode(self):
        return bytes() 
    
    def decode(self, data):
        pass


messages = dict()
messages[MsgType.ClientHello] = ClientHello
messages[MsgType.ServerHello] = ServerHello
messages[MsgType.CDRequest] = CDRequest
messages[MsgType.CDResponse] = CDResponse
messages[MsgType.LSRequest] = LSRequest
messages[MsgType.LSResponse] = LSResponse
messages[MsgType.GetRequest] = GetRequest
messages[MsgType.GetResponse] = GetResponse
messages[MsgType.PutRequest] = PutRequest
messages[MsgType.PutResponse] = PutResponse
messages[MsgType.QuitRequest] = QuitRequest
messages[MsgType.QuitResponse] = QuitResponse
messages[MsgType.ChangeSettingsRequest] = ChangeSettingsRequest
messages[MsgType.ChangeSettingsResponse] = ChangeSettingsResponse
messages[MsgType.ErrorResponse] = ErrorResponse
messages[MsgType.File] = File 
messages[MsgType.FileChunk] = FileChunk
messages[MsgType.EndOfFileChunks] = EndOfFileChunks
messages[MsgType.EndOfFiles] = EndOfFiles

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
    if not msgid in messages:
        raise UnknownMsgTypeException(msgid)
    msglen = int.from_bytes(recvall(socket, 2), byteorder="big")
    data = recvall(socket, msglen)
    msgtype = messages[msgid]
    msg = msgtype()
    msg.decode(data)
    return (msgid, msg)

def wrap_in_id_length(msgid, data):
    msglen = len(data)
    frame = bytearray()
    frame.extend(int(msgid).to_bytes(1, byteorder="big"))
    frame.extend((msglen).to_bytes(2, byteorder="big"))
    frame.extend(data)
    return bytes(frame)

def sendmsg(socket, msg):
    """
    sendmsg will send an effteepee protocol message
    on the socket. 
    """
    if not msg.id() in messages:
        raise UnknownMsgTypeException(msg.id())
    data = msg.encode()
    data = wrap_in_id_length(msg.id(), data)
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
    if encryption:
        data = encrypt(key, data)
    if compression:
        data = compress(data)
    return data

def decode_file_data(data, compression, encryption, key):
    """
    decode will undo what encode has done. It will
    first decompress data if compression flag is True.
    Then will decrypt data with key if encryption flag 
    is True. Will return the resulting data. If neither
    is True then decode is a NOP.
    """
    if compression:
        data = decompress(data)
    if encryption:
        data = decrypt(key, data)
    return data

# Credit to https://gist.github.com/ilogik/6f9431e4588015ecb194 
# for the vigenere cipher. Both functions take the plaintext
# and ciphertext as bytearrays instead of strings. The key is a 
# string of characters.
def encrypt(key, plaintext):
    b = []
    for i in range(len(plaintext)):
        k = key[i % len(key)]
        c = (plaintext[i] + ord(k) % 256)
        b.append(c)
    return bytes(b)

def decrypt(key, ciphertext):
    b = []
    for i in range(len(ciphertext)):
        k = key[i % len(key)]
        p = abs(ciphertext[i] - ord(k) % 256)
        b.append(p)
    return bytes(b)

# Compress with LZMA with a 
# CRC32 checksum to ensure file data 
# is not corrupted during transfer.
def compress(data):
    return lzma.compress(data, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC32)

# Decompress with LZMA with a 
# CRC32 checksum to ensure file data 
# is not corrupted during transfer.
def decompress(data):
    return lzma.decompress(data, format=lzma.FORMAT_XZ)


def get_files(socket, cwd, num_files, compression, encryption):
    # Will read File messages from the socket. 
    # Reads num_files in the following order:
    # File -> FileChunk -> EndOfFileChunks 
    # Will lastly read an EndOfFiles msg to 
    # signal that there are no more files.
    for i in range(num_files):
        (rid, msg) = recvmsg(socket)
        if rid != MsgType.File:
            return False 
        filename = join(cwd, msg.filename)
        f = open(filename, 'wb')
        while True:
            (rid, msg) = recvmsg(socket)
            if rid == MsgType.ErrorResponse:
                # we got an error from the the other 
                # side.
                f.close()
                return False
            if rid == MsgType.EndOfFileChunks:
                # we've read all the file chunks
                f.close()
                break 
            if rid != MsgType.FileChunk:
                print("Expected a FileChunk, got {}".format(msg))
                f.close()
                return False
            # write chunk data to file
            data = msg.data
            data = decode_file_data(data, compression, encryption, ENCRYPTION_KEY)
            f.write(data)
    (rid, msg) = recvmsg(socket)
    if rid != MsgType.EndOfFiles:
        return False 
    return True

def put_files(socket, cwd, filenames, compression, encryption):
    # Will put File messages on the socket.
    # Writes file data for each file in filenames:
    # File -> FileChunk -> EndOfFileChunks
    # Ending with an EndOfFiles message to finish
    # up.
    first = True
    for filename in filenames:
        chunk_num = 0
        total_size = 0
        msg = File(filename)
        sendmsg(socket, msg)
        f = open(join(cwd, filename), "rb")
        while True:
            data = f.read(DEFAULT_FILE_CHUNK_SIZE)
            if not data:
                # Reached end of file.
                # Write end of file chunk.
                # And move on to next file.
                msg = EndOfFileChunks()
                sendmsg(socket, msg)
                break
            # write data chunks
            data = encode_file_data(data, compression, encryption, ENCRYPTION_KEY)
            if first:
                debug_print(data)
                first = False
            chunk_num += 1
            total_size += len(data)
            msg = FileChunk(data)
            sendmsg(socket, msg)
        debug_print("File: {}, Chunks: {}, Size: {}".format(filename, chunk_num, total_size))
        f.close()
    msg = EndOfFiles()
    sendmsg(socket, msg)
    return True

