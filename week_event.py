import requests
import re
import datetime
from speech_engine import SpeechEngine

class WeekEvent:
    def __init__(self, speak):
        self.speak = speak
    def create_task(self, title, description, start_time, end_time):
        url = "http://192.168.68.54/tasks"
        payload = {
            "title": title,
            "description": description,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat()
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 201:
                task_data = response.json()
                print(f"任务创建成功! ID: {task_data.get('id')}")
                return task_data
            else:
                print(f"创建任务失败: {response.text}")
                return None
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return None

    def update_task(self, task_id, update_data):
        url = f"http://192.168.68.54/tasks/{task_id}"
        try:
            response = requests.put(url, json=update_data)
            if response.status_code == 200:
                print("任务更新成功")
                return response.json()
            else:
                print(f"更新任务失败: {response.text}")
                return None
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return None

    def delete_task(self, task_id):
        url = f"http://192.168.68.54/tasks/{task_id}"
        try:
            response = requests.delete(url)
            if response.status_code == 204:
                print("任务删除成功")
                return True
            else:
                print(f"删除任务失败: {response.text}")
                return False
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return False

    def list_tasks(self, user_id):
        url = "http://192.168.68.54/tasks"
        params = {"userId": user_id}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                tasks = response.json()
                return tasks
            else:
                print(f"获取任务列表失败: {response.text}")
                return []
        except Exception as e:
            print(f"Network Error: {str(e)}")
            return []

    def parse_date_time(self, text):
        now = datetime.datetime.now()
        if "today" in text:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if "tomorrow" in text:
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        for day, offset in weekdays.items():
            if day in text:
                days_ahead = (offset - now.weekday() + 7) % 7
                return now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
        if "next" in text:
            for day, offset in weekdays.items():
                if day in text:
                    days_ahead = (offset - now.weekday() + 7) % 7 + 7
                    return now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
        time_match = re.search(r'(\d{1,2}:\d{2})', text)
        if time_match:
            time_str = time_match.group(1)
            hour, minute = map(int, time_str.split(':'))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return now

    def weekevent(self, command_text, user_id="default_user"):
        command_text = command_text.lower()
        if 'add task' in command_text or 'create task' in command_text:
            title_match = re.search(r'add task (.+?)(?: from | to |$)', command_text)
            if not title_match:
                self.speak("Please provide a task title.")
                return
            title = title_match.group(1).strip()
            start_time = None
            if 'from' in command_text:
                from_idx = command_text.find('from') + 5
                start_text = command_text[from_idx:].split()[0]
                start_time = self.parse_date_time(start_text)
            end_time = None
            if 'to' in command_text:
                to_idx = command_text.find('to') + 3
                end_text = command_text[to_idx:].split()[0]
                end_time = self.parse_date_time(end_text)
            if not start_time:
                start_time = datetime.datetime.now()
            if not end_time:
                end_time = start_time + datetime.timedelta(hours=1)
            description = ""
            if 'about' in command_text:
                about_idx = command_text.find('about') + 6
                description = command_text[about_idx:].split('.')[0]
            result = self.create_task(user_id, title, description, start_time, end_time)
            if result:
                self.speak(f"Task created: {title}")
        elif 'list tasks' in command_text or 'show tasks' in command_text:
            tasks = self.list_tasks(user_id)
            if not tasks:
                self.speak("You currently have no tasks.")
                return
            response = "Your task list:"
            for task in tasks:
                title = task.get('title', 'Unknown task')
                start_time = task.get('startTime', 'Unknown start time')
                end_time = task.get('endTime', 'Unknown end time')
                try:
                    start_dt = datetime.datetime.fromisoformat(start_time)
                    end_dt = datetime.datetime.fromisoformat(end_time)
                    start_str = start_dt.strftime("%m/%d %H:%M")
                    end_str = end_dt.strftime("%H:%M")
                    time_str = f"{start_str} - {end_str}"
                except:
                    time_str = f"{start_time} - {end_time}"
                response += f"\n- {title} ({time_str})"
            print(response)
            self.speak(response)
        elif 'update task' in command_text or 'modify task' in command_text:
            id_match = re.search(r'task (\d+)', command_text)
            if not id_match:
                self.speak("Please specify the task ID.")
                return
            task_id = id_match.group(1)
            update_data = {}
            if 'title' in command_text:
                title_match = re.search(r'title (.+?)(?: to |$)', command_text)
                if title_match:
                    update_data['title'] = title_match.group(1).strip()
            if 'description' in command_text:
                desc_match = re.search(r'description (.+?)(?: to |$)', command_text)
                if desc_match:
                    update_data['description'] = desc_match.group(1).strip()
            if 'time' in command_text or 'reschedule' in command_text:
                if 'from' in command_text:
                    from_idx = command_text.find('from') + 5
                    start_text = command_text[from_idx:].split()[0]
                    start_time = self.parse_date_time(start_text)
                    update_data['startTime'] = start_time.isoformat()
                if 'to' in command_text:
                    to_idx = command_text.find('to') + 3
                    end_text = command_text[to_idx:].split()[0]
                    end_time = self.parse_date_time(end_text)
                    update_data['endTime'] = end_time.isoformat()
            if not update_data:
                self.speak("Please provide the content to update (title, description, or time).")
                return
            if self.update_task(task_id, update_data):
                self.speak(f"Task {task_id} has been updated.")
            else:
                self.speak(f"Failed to update task {task_id}.")
        elif 'delete task' in command_text or 'remove task' in command_text:
            id_match = re.search(r'task (\d+)', command_text)
            if not id_match:
                self.speak("Please specify the task ID to delete.")
                return
            task_id = id_match.group(1)
            if self.delete_task(task_id):
                self.speak(f"Task {task_id} has been deleted.")
            else:
                self.speak(f"Failed to delete task {task_id}.")
        else:
            self.speak("Unrecognized task command.")