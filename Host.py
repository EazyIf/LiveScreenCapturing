import socket
import cv2
import pickle
import struct
import imutils
import numpy as np
from mss import mss
import keyboard

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:',host_ip)
port = 9999
socket_address = (host_ip,port)

server_socket.bind(socket_address)
server_socket.listen(5)
print("LISTENING AT:",socket_address)

while True:
    client_socket,addr = server_socket.accept()
    print('GOT CONNECTION FROM:',addr)
    if client_socket:
        data = client_socket.recv(8)
        win_x, win_y = struct.unpack("ii",data)
        monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        sct = mss()
        
        while True:
            sct_img = sct.grab(monitor)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.IMREAD_COLOR)
            
            frame = imutils.resize(frame, win_x)
            a = pickle.dumps(frame)
            message = struct.pack("Q",len(a))+a
            client_socket.sendall(message)

            # cv2.imshow('TRANSMITTING SCREEN',frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        cv2.destroyAllWindows()
        client_socket.close()
