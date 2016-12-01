import sys 
import pathlib
import hashlib
import re

from common import *

def main():
    if len(sys.argv) != 2:
        print("error: need command.")
        return 1
    user_file = DEFAULT_USER_FILE
    command = sys.argv[1]
    if command == "adduser":
        adduser(user_file)


def adduser(user_file):
    username = input("Username:")
    password = input("Password:")
    if not re.match("[^@]+@[^@]+\.[^@]+", password):
        print("Invalid password. Must match email address.")
        return 1
    pass_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    directory = input("Root directory (needs to be absolute):")
    line = "::".join((username, pass_hash, directory))
    line += "\n"
    with open(user_file, "a") as f:
        f.write(line)
    print("User added.")

if __name__ == '__main__':
    import sys
    sys.exit(int(main() or 0)) 