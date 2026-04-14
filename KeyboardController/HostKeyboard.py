import socket
from pynput.keyboard import Key, Controller


def get_local_ip():
    """Get LAN IP address (works on both Windows and Linux)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


keyboard = Controller()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = get_local_ip()
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