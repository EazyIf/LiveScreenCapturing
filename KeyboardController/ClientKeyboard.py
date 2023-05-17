import socket
import pyWinhook
import pythoncom
from pynput import keyboard

class Client:
    def __init__(self):
        # self.HostName = socket.gethostname()
        self.IP = '192.168.1.120'
        self.PORT = 1223
        # self.client_socket = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def OnPress(self, key):
        # self.client_socket.connect((self.IP, self.PORT))   
        prr = f'press.{key}'
        if self.client_socket:
            self.client_socket.send(prr.encode())

    def OnRelease(self,key):
        rls = f'release.{key}'
        if self.client_socket:
            if 'Key' not in rls:
                pass
            else:
                self.client_socket.send(rls.encode())

    def OnKeyboardEvent(self, event):
        return False

    def RunClient(self):
        # self.client_socket = None   
        hook_manager = pyWinhook.HookManager()
        hook_manager.KeyDown = self.OnKeyboardEvent
        hook_manager.HookKeyboard()
        # listener = keyboard.Listener(on_press=self.OnPress)
        listener = keyboard.Listener(on_press=self.OnPress,on_release=self.OnRelease)
        listener.start()
        self.client_socket.connect((self.IP, self.PORT))
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            pythoncom.PumpMessages()
        except KeyboardInterrupt:
            pass

        hook_manager.UnhookKeyboard()
        self.client_socket.close()

if __name__ == "__main__":
    try:
        client = Client()
        client.RunClient()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
