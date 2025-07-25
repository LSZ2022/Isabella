import requests
import re

class AlarmClock:
    def __init__(self, speak):
        self.speak = speak  # 接收语音接口
    def add_alarm(self, time, label=None, enabled=True, days=None):
        url = "http://192.168.68.54/alarms"
        payload = {
            "time": time,
            "label": label,
            "enabled": enabled,
            "days": days
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                alarm_data = response.json()
                print(f"Alarm added successfully! ID: {alarm_data.get('id')}")
                return alarm_data
            else:
                print(f"Failed to add alarm: {response.text}")
                return None
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return None

    def toggle_alarm(self, alarm_id, enabled):
        url = f"http://192.168.68.54/alarms/{alarm_id}/toggle"
        payload = {"enabled": enabled}
        try:
            response = requests.put(url, json=payload)
            if response.status_code == 200:
                print(f"Alarm {'enabled' if enabled else 'disabled'} successfully")
                return True
            else:
                print(f"Failed to switch status: {response.text}")
                return False
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return False

    def delete_alarm(self, alarm_id):
        url = f"http://192.168.68.54/alarms/{alarm_id}"
        try:
            response = requests.delete(url)
            if response.status_code == 200:
                self.speak("Alarm deleted successfully", None)
                return True
            else:
                print(f"Deletion failed: {response.text}")
                return False
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return False

    def list_alarms(self):
        url = "http://192.168.68.54/alarms"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                alarms = response.json()
                return alarms
            else:
                print(f"Failed to get the alarm list: {response.text}")
                return []
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return []

    def alarmclock(self, command_text):
        command_text = command_text.lower()
        if 'set alarm' in command_text or 'add alarm' in command_text:
            time_match = re.search(r'(\d{1,2}:\d{2})', command_text)
            if not time_match:
                self.speak("Please specify the time in the format hour:minute, for example 8:30")
                return
            time = time_match.group(1)
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time):
                self.speak("Invalid time format, please use HH:MM format")
                return
            label = None
            if 'for' in command_text:
                label_start = command_text.find('for') + 4
                label = command_text[label_start:].split()[0]
            days = None
            if 'every' in command_text:
                days_start = command_text.find('every') + 5
                days = command_text[days_start:].split()[0]
                day_mapping = {
                    'monday': '1', 'tuesday': '2', 'wednesday': '3',
                    'thursday': '4', 'friday': '5', 'saturday': '6', 'sunday': '7',
                    'weekdays': '1,2,3,4,5', 'weekends': '6,7'
                }
                days = day_mapping.get(days.lower(), days)
            result = self.add_alarm(time, label, True, days)
            if result:
                self.speak(f"Alarm set for {time}{' ' + label if label else ''}")
        elif 'list alarms' in command_text or 'show alarms' in command_text:
            alarms = self.list_alarms()
            if not alarms:
                self.speak("No alarms are set")
                return
            response = "Your alarm settings:"
            for alarm in alarms:
                time = alarm.get('time', 'Unknown time')
                label = alarm.get('label', '')
                days = alarm.get('days', '')
                status = "Enabled" if alarm.get('enabled') else "Disabled"
                day_names = {
                    '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday',
                    '5': 'Friday', '6': 'Saturday', '7': 'Sunday',
                    '1,2,3,4,5': 'Weekdays', '6,7': 'Weekend'
                }
                days_display = day_names.get(days, days)
                response += f"\n{time} {label} - {status}"
            print(response)
            self.speak(response)
        elif 'enable alarm' in command_text or 'disable alarm' in command_text:
            id_match = re.search(r'alarm (\d+)', command_text)
            if not id_match:
                self.speak("Please specify the alarm ID")
                return
            alarm_id = id_match.group(1)
            enabled = 'enable' in command_text
            if self.toggle_alarm(alarm_id, enabled):
                status = "enabled" if enabled else "disabled"
                self.speak(f"Alarm {alarm_id} has been {status}")
        elif 'delete alarm' in command_text or 'remove alarm' in command_text:
            id_match = re.search(r'alarm (\d+)', command_text)
            if not id_match:
                self.speak("Please specify the alarm ID to delete")
                return
            alarm_id = id_match.group(1)
            if self.delete_alarm(alarm_id):
                self.speak(f"Alarm {alarm_id} has been deleted")
        else:
            self.speak("Unrecognized alarm command")