# EffTeePee Client

import socket 

host, port = "localhost", 8080

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        while True:
            data = input("Say: ")
            if not data:
                continue
            sock.sendall(bytes(data + "\n", "utf-8"))

            received = str(sock.recv(1024), "utf-8")

            if not received:
                break
            print("Received: {}".format(received))

if __name__ == '__main__':
    import sys
    sys.exit(int(main() or 0))