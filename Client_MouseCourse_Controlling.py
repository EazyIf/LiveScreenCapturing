import socket
from pynput.mouse import Listener, Controller
import pyautogui
import time
 
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.108.99', 9999)
client_socket.connect(server_address)
 
screenW, screenH = pyautogui.size()
midX = screenW // 2
midY = screenH // 2
 
mouse = Controller()
mouse.position = (midX,midY)
 
last_sent = time.time()
last_sent_2 = time.time()
 
def MouseMove(x, y):
    global last_sent

    if time.time() - last_sent > 0.1:
        client_socket.send(f'{x},{y}'.encode())
        last_sent = time.time()
 
def MouseScroll(x, y, button, press):
    global last_sent_2
    
    if time.time() - last_sent_2 > 0.1:
        client_socket.send(f'scroll.{press}'.encode())
        last_sent_2 = time.time()

def MouseClick(x, y, button, press):
    if press:
        client_socket.send(f'press.{button}'.encode())
 
    else:
        client_socket.send(f'release.{button}'.encode())
 
listener = Listener(on_click=MouseClick,on_scroll=MouseScroll,on_move=MouseMove)
listener.start()
listener.join()

client_socket.close()
