import socket
from pynput.mouse import Listener, Controller
import pyautogui
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.1.120', 9999)
client_socket.connect(server_address)

screenW, screenH = pyautogui.size()
midX = screenW // 2
midY = screenH // 2

mouse = Controller()
mouse.position = (midX,midY)

def MouseMove(x, y):
    time.sleep(0.04) # you may want to change it to a lower or higher sleep time
    '''
    for a lower time.sleep you will lose a lot more data but it will run faster
    for a higher time.sleep you will lose less data but it will run slower
    so it's realy depends on your own free will
    '''
    client_socket.send(f'{x},{y}'.encode())

def MouseScroll(x, y, button, press):
    client_socket.send(f'scroll.{press}'.encode())

def MouseClick(x, y, button, press):
    if press:
        client_socket.send(f'press.{button}'.encode())

    else:
        client_socket.send(f'release.{button}'.encode())

listener = Listener(on_click=MouseClick,on_scroll=MouseScroll,on_move=MouseMove)
listener.start()
listener.join()
