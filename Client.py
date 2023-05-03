import socket,cv2, pickle,struct
from mss import mss
from PIL import Image
import numpy as np
import ctypes

user32 = ctypes.windll.user32
win_x, win_y = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)] 
win_cnt_x, win_cnt_y = [user32.GetSystemMetrics(0)/2, user32.GetSystemMetrics(1)/2]

# create socket
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_ip = '192.168.1.126' # paste your server ip address here
port = 9999
client_socket.connect((host_ip,port)) # a tuple
data = b""
packed_data = struct.pack("ii", win_x, win_y)
client_socket.sendall(packed_data)

payload_size = struct.calcsize("Q")
while True:
	while len(data) < payload_size:
		packet = client_socket.recv(4*1024) # 4K
		if not packet: break
		data+=packet
	packed_msg_size = data[:payload_size]
	data = data[payload_size:]
	msg_size = struct.unpack("Q",packed_msg_size)[0]
	
	while len(data) < msg_size:
		data += client_socket.recv(4*1024)
	frame_data = data[:msg_size]
	data  = data[msg_size:]
	frame = pickle.loads(frame_data)
	cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
	cv2.setWindowProperty("RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
	cv2.imshow("RECEIVING VIDEO",frame)
	key = cv2.waitKey(1) & 0xFF
	if key  == ord('q'):
		break
client_socket.close()
