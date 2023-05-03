import socket, cv2, pickle, struct, imutils
import numpy as np
from mss import mss

# Socket Create
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:',host_ip)
port = 9999
socket_address = (host_ip,port)

# Socket Bind
server_socket.bind(socket_address)

# Socket Listen
server_socket.listen(5)
print("LISTENING AT:",socket_address)

# Socket Accept
while True:
    client_socket,addr = server_socket.accept()
    print('GOT CONNECTION FROM:',addr)
    if client_socket:
        # Initialize the screen capture object
        monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        sct = mss()
        

        while True:
            sct_img = sct.grab(monitor)
            frame = np.array(sct_img)
            frame = cv2.cvtColor(frame, cv2.IMREAD_COLOR)
            
            # frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            frame = imutils.resize(frame, width=1280)
            a = pickle.dumps(frame)
            message = struct.pack("Q",len(a))+a
            client_socket.sendall(message)

            cv2.imshow('TRANSMITTING SCREEN',frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        cv2.destroyAllWindows()
        client_socket.close()
