
import werkzeug.security as wsecurity
import random
import string
import sys

def randomstring(length):
   letters = (random.choice(string.ascii_lowercase) for i in range(length))
   return ''.join(letters)

def main():
    password = randomstring(16)

    if len(sys.argv) > 1:
        password = sys.argv[1]

    hashed = wsecurity.generate_password_hash(password)
    print(password)
    print(hashed)

if __name__ == '__main__':
    main()
