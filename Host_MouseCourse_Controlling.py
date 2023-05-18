import socket
from pynput.mouse import Button, Controller
import pyautogui

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:',host_ip)
port = 9999
server_address = (host_ip,port)
server_socket.bind(server_address)
server_socket.listen(1)
client_socket, client_address = server_socket.accept()

screenW, screenH = pyautogui.size()
midX = screenW // 2
midY = screenH // 2

mouse = Controller()
mouse.position = (midX,midY)

while True:
    try:
        data = client_socket.recv(1024).decode()
        if ',' in data:
            x, y = map(int, data.split(","))
            mouse.position = (x, y)

        elif 'scroll' in data:
            mouse.scroll(0, int(data.split('.')[1]))
        else:
            buttonn = getattr(Button,f'{data.split(".")[2]}')
            action = getattr(mouse,f'{data.split(".")[0]}')
            action(buttonn)

    except ValueError:
        pass
        # print(ValueError, " too many values to unpack (expected 2)")
    except AttributeError:
        pass
        # print(AttributeError, " 'Button' object has no attribute '",data.split(".")[0],"'")
