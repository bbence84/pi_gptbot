import alsaaudio
import sys
import socket

class Utils:

    def __init__(self):
        pass
    
    def __get_mixer(self, device_index, device_name):
        try:
            if (device_name != ""):
                mixer = alsaaudio.Mixer(control='Mic', device = device_name)
            else:
                mixer = alsaaudio.Mixer(control='Mic', cardindex = device_index)
            return mixer
        except alsaaudio.ALSAAudioError:
            print("No such mixer", file=sys.stderr)
            
    def mute_mic(self, device_index=0, device_name=""):
        
        mixer = self.__get_mixer(device_index, device_name)
         
        mixer.setrec(0)
        # mixer.setvolume(0)
        
        
    def unmute_mic(self, device_index=0, device_name=""):
        
        mixer = self.__get_mixer(device_index, device_name)
         
        mixer.setrec(1)   
        # mixer.setvolume(90)            
        
    def has_internet(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error as ex:
            return False        