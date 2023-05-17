import socket
from pynput.keyboard import Key, Controller
import keyboard


keyboard = Controller()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HostName = socket.gethostname()
IP = socket.gethostbyname(HostName)
PORT = 1223
sock.bind((IP, PORT))
sock.listen(3)
print(f"[*] Listening as {IP}:{PORT}")

client_socket, addr = sock.accept()
print('GOT CONNECTION FROM:', addr)

while True:
    msg = client_socket.recv(1024).decode()
    try:
        if 'Key' not in msg:
            keyboard.type(eval(msg.split('.')[1]))
        else:
            key = getattr(Key, msg.split(".")[2])
            function = getattr(keyboard, msg.split(".")[0])
            function(key)
    except AttributeError:
        print("AttributeError: enterpress")
    except SyntaxError:
        print("SyntaxError: unexpected EOF while parsing")

client_socket.close()
sock.close()