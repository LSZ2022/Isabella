import os
import win32api
import win32con
import win32gui
from speech_engine import SpeechEngine

class OSController:
    def __init__(self, volume_control, speak):
        self.volume_control = volume_control
        self.speak = speak

    def ControlOSFunction(self, command_text):
        command_text = command_text.lower()
        if 'volume' in command_text:
            current_vol = self.volume_control.get_system_volume()
            percent = int(current_vol * 100)
            if 'up' in command_text or 'increase' in command_text:
                self.volume_control.adjust_system_volume(0.1)
                new_percent = int(self.volume_control.get_system_volume() * 100)
                self.speak(f"Volume increased from {percent}% to {new_percent}%")
                return
            elif 'down' in command_text or 'decrease' in command_text:
                self.volume_control.adjust_system_volume(-0.1)
                new_percent = int(self.volume_control.get_system_volume() * 100)
                self.speak(f"Volume decreased from {percent}% to {new_percent}%")
                return
            elif 'max' in command_text or 'full' in command_text:
                self.volume_control.set_system_volume(1.0)
                self.speak("Volume set to maximum")
                return
            elif 'min' in command_text or 'mute' in command_text:
                self.volume_control.set_system_volume(0.0)
                self.speak("Volume muted")
                return
            elif 'set' in command_text:
                try:
                    words = command_text.split()
                    for word in words:
                        if word.isdigit():
                            level = int(word)
                            if 0 <= level <= 100:
                                self.volume_control.set_system_volume(level / 100.0)
                                self.speak(f"Volume set to {level} percent")
                                return
                    self.speak(f"Current volume is {percent} percent")
                    return
                except:
                    self.speak("Could not set volume level")
                    return
            else:
                self.speak(f"Current volume is {percent} percent")
                return
        command = command_text.lower()
        if 'shutdown' in command:
            os.system("shutdown /s /t 1")
        elif 'restart' in command or 'reboot' in command:
            os.system("shutdown /r /t 1")
        elif 'sleep' in command or 'suspend' in command:
            win32api.SetSystemState(win32con.SYSTEM_STATE_SUSPEND)
        elif 'lock' in command:
            win32gui.LockWorkStation()
        elif 'logout' in command:
            os.system("shutdown /l")
        elif 'hibernate' in command:
            os.system("shutdown /h")
        else:
            self.speak("Unsupported OS command")

            