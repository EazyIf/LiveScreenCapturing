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

def get_button_from_string(button_str):
    if button_str == 'Button.left':
        return Button.left
    elif button_str == 'Button.right':
        return Button.right
    elif button_str == 'Button.middle':
        return Button.middle
    else:
        return Button.unknown

try:
    while True:
        data = client_socket.recv(1024).decode()
        if not data:
            break
        events = data.split('\n')
        for event in events:
            event_parts = event.split()
            if len(event_parts) < 2:
                continue
            
            event_type = event_parts[0]

            if event_type == 'MOVE':
                if len(event_parts) < 3:
                    continue
                try:
                    x, y = int(event_parts[1]), int(event_parts[2])
                    mouse.position = (x, y)
                except ValueError:
                    continue
            
            elif event_type == 'PRESS' or event_type == 'RELEASE':
                if len(event_parts) < 4:
                    continue
                button_str = event_parts[1]
                button = get_button_from_string(button_str)
                try:
                    x, y = int(event_parts[2]), int(event_parts[3])
                    if event_type == 'PRESS':
                        mouse.position = (x, y)
                        if button == mouse.scroll:
                            if len(event_parts) < 5:
                                continue
                            scroll_amount = int(event_parts[4])
                            mouse.scroll(100, scroll_amount)
                        else:
                            mouse.press(button)
                    else:
                        mouse.position = (x, y)
                        if button != mouse.scroll:
                            mouse.release(button)
                except ValueError:
                    continue
except KeyboardInterrupt:
    pass

client_socket.close()
server_socket.close()
