import socket
from pynput.mouse import Controller, Listener
import pyautogui

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.1.120', 9999)
client_socket.connect(server_address)

screen_width, screen_height = pyautogui.size()
middle_x = screen_width // 2
middle_y = screen_height // 2
mouse = Controller()
mouse.position = (middle_x, middle_y)

def send_event(event):
    client_socket.send(event.encode())

def on_mouse_event(x, y, button, pressed):
    if pressed:
        event = f"PRESS {button} {x} {y}"
        send_event(event)
    else:
        event = f"RELEASE {button} {x} {y}"
        send_event(event)
listener = Listener(on_click=on_mouse_event)
listener.start()
prev_x, prev_y = mouse.position

try:
    while True:
        x, y = mouse.position

        if x != prev_x or y != prev_y:
            event = f"MOVE {x} {y}"
            send_event(event)
            prev_x, prev_y = x, y
except KeyboardInterrupt:
    listener.stop()

client_socket.close()
