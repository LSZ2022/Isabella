import datetime
import threading
import re
import time
import pyaudio
import speech_recognition as sr 
from volume_control import VolumeControl
from speech_engine import SpeechEngine
from greeting_generator import GreetingGenerator
from weather_service import WeatherService
from alarm_clock import AlarmClock
from week_event import WeekEvent
from os_controller import OSController
from hardware_status_reporter import HardwareStatusReporter
from server_security_checker import ServerSecurityChecker
import MicrobitTemperatureMonitor
from greeting_generator import GreetingGenerator



class MainAssistant:
    def __init__(self):
        # 1. 初始化语音引擎（核心）
        self.speech_engine = SpeechEngine(
            pause_recording=self.pause_recording,  # 傳入暫停方法
            resume_recording=self.resume_recording  # 傳入恢復方法
        )
        self.speak = self.speech_engine.speak  # 统一语音接口

        # 2. 初始化其他组件，并注入 speak 方法
        self.recording_paused = False
        self.volume_control = VolumeControl()
        self.weather_service = WeatherService(speak=self.speak)  # 注入
        self.alarm_clock = AlarmClock(speak=self.speak)          # 注入
        self.week_event = WeekEvent(speak=self.speak)            # 注入
        self.os_controller = OSController(
            volume_control=self.volume_control,
            speak=self.speak  # 注入
        )
        self.hardware_reporter = HardwareStatusReporter(speak=self.speak)  # 注入
        self.security_checker = ServerSecurityChecker(speak=self.speak)    # 注入
        self.greeting_generator = GreetingGenerator(speak=self.speak)
        # 其他初始化（线程控制、设备监控等）
        self.alarm_thread_running = True
        self.temp_monitor = MicrobitTemperatureMonitor.MicrobitTemperatureMonitor()
        self.active = True

   
    def alarm_monitor(self):
        """闹钟监控线程：精确匹配时间，避免重复触发"""
        print("Alarm monitor thread started...")
        last_triggered = {}  # 记录 {闹钟ID: 最后触发的分钟}
        
        while self.alarm_thread_running:
            try:
                now = datetime.datetime.now()
                current_time_str = now.strftime("%H:%M")  # 格式如 "08:30"
                current_minute = now.minute  # 当前分钟（0-59）
                current_weekday = now.isoweekday()  # 1=周一，7=周日
                
                # 获取所有启用的闹钟
                all_alarms = self.alarm_clock.list_alarms()
                triggered_alarms = []
                
                for alarm in all_alarms:
                    alarm_id = alarm.get('id')
                    # 过滤未启用或无ID的闹钟
                    if not alarm_id or not alarm.get('enabled', False):
                        continue
                    
                    # 1. 时间匹配：精确到分钟
                    alarm_time = alarm.get('time', '').strip()
                    if alarm_time != current_time_str:
                        continue  # 时间不匹配则跳过
                    
                    # 2. 日期匹配（支持工作日/周末/特定日期）
                    alarm_days = alarm.get('days', '').strip().lower()
                    if alarm_days == 'weekdays' and current_weekday not in [1,2,3,4,5]:
                        continue  # 非工作日跳过
                    if alarm_days == 'weekends' and current_weekday not in [6,7]:
                        continue  # 非周末跳过
                    if alarm_days and alarm_days not in ['weekdays', 'weekends']:
                        # 特定日期（如 "1,3,5" 表示周一/三/五）
                        if str(current_weekday) not in alarm_days.split(','):
                            continue
                    
                    # 3. 防重复触发：同一分钟内只触发一次
                    if last_triggered.get(alarm_id) == current_minute:
                        continue
                    last_triggered[alarm_id] = current_minute
                    
                    triggered_alarms.append(alarm)
                
                # 触发闹钟逻辑
                if triggered_alarms:
                    self.handle_alarm_trigger(triggered_alarms)
                
                # 精确休眠到下一分钟（减少CPU占用）
                sleep_seconds = 60 - now.second
                time.sleep(max(1, sleep_seconds))  # 至少休眠1秒，避免负数值
                
            except Exception as e:
                print(f"Alarm monitor error: {str(e)}")
                time.sleep(10)  # 出错时延迟重试，避免频繁报错
    
    def handle_alarm_trigger(self, alarms):
        """处理闹钟触发逻辑"""
        # 播放提示音
        self.speech_engine.speak("Ding dong! Alarm time!")
        
        # 生成问候语
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            self.speech_engine.speak("Good morning! It's time to wake up.")
        elif 12 <= hour < 18:
            self.speech_engine.speak("Good afternoon! This is your reminder.")
        else:
            self.speech_engine.speak("Good evening! Here's your reminder.")
        
        # 播报今日任务
        today_tasks = self.get_today_tasks()
        if today_tasks:
            self.speech_engine.speak("Here are your tasks for today:")
            for i, task in enumerate(today_tasks, 1):
                title = task.get('title', 'Untitled')
                start_time = task.get('startTime', '').split('T')[-1][:5]
                self.speech_engine.speak(f"Task {i}: {title} at {start_time}")
        else:
            self.speech_engine.speak("You have no tasks scheduled for today.")

    def get_today_tasks(self, user_id="default_user"):
        """获取今日任务"""
        now = datetime.datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        all_tasks = self.week_event.list_tasks(user_id)
        today_tasks = []
        
        for task in all_tasks:
            try:
                start_time = datetime.datetime.fromisoformat(task['startTime'])
                if today_start <= start_time <= today_end:
                    today_tasks.append(task)
            except:
                continue
        return today_tasks

    def handle_iot(self, query):
        """处理物联网设备控制（温度、电视等）"""
        query = query.lower()
        if "temperature" in query or "temp" in query:
            # 温度监控逻辑
            if "current" in query or "now" in query:
                if not self.temp_monitor.start_monitoring():
                    self.speak("Failed to start temperature monitoring. Check Micro:bit connection.")
                    return
                
                start_time = time.time()
                while self.temp_monitor.current_temperature is None and time.time() - start_time < 2:
                    time.sleep(5)
                
                temp = self.temp_monitor.get_current_temperature()
                unit = "Celsius" if self.temp_monitor.display_mode == "celsius" else "Fahrenheit"
                if temp:
                    self.speak(f"Current temperature is {temp:.1f} degrees {unit}")
                else:
                    self.speak("Could not get temperature data.")
                self.temp_monitor.stop_monitoring()
            
            elif "unit" in query:
                new_mode = self.temp_monitor.toggle_display_mode()
                unit = "Celsius" if new_mode == "celsius" else "Fahrenheit"
                self.speak(f"Switched temperature unit to {unit}")
        
        elif "television" in query:
            self.speak('小維小維')
            time.sleep(0.7)
            if "turn on" in query: 
                print("open")
                self.speak('開機')
            elif 'turn off' in query:
                self.speak('關機')
            else:
                self.speak('Execute TV operation')
    
    def pause_recording(self):
        self.recording_paused = True

    def resume_recording(self):
        self.recording_paused = False

    def AIVoice(self):
        if self.recording_paused:
            return ""
    
        # 原有参数
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1  # 虚拟设备支持立体声
        RATE = 44100  # 与设备默认采样率一致
        RECORD_SECONDS = 10

        p = pyaudio.PyAudio()
        target_device_index = 1  # 虚拟输入设备ID

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=target_device_index,
            frames_per_buffer=CHUNK
        )

        print("Start Recording...")
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        # 后续识别逻辑...
        stream.stop_stream()
        stream.close()
        p.terminate()

        # 原有语音识别代码...
        # 将录制的音频数据转换为字节流
        audio_data = b''.join(frames)

        # 使用speech_recognition库进行语音识别
        r = sr.Recognizer()
        audio = sr.AudioData(audio_data, sample_rate=RATE, sample_width=p.get_sample_size(FORMAT))

        try:
            text = r.recognize_google(audio, language='en-US')
            text_lower = text.lower()
            print(f"Recognize: {text}")
            return text_lower
        except sr.UnknownValueError:
            print("Unable to recognize speech.")
        except sr.RequestError as e:
            print(f"Request Error; {e}")


    def run(self):
        """主程序入口"""
        # 启动语音线程和闹钟线程
        alarm_thread = threading.Thread(target=self.alarm_monitor, daemon=True)
        alarm_thread.start()
        
        # 初始问候（关键修改：确保问候语播放时完全暂停录音）
        self.pause_recording()  # 暂停录音
        greeting = self.greeting_generator.generate_greeting()
        self.speech_engine.speak(greeting)  # 播放问候语
        # 动态计算暂停时间：根据问候语长度估算（每个字符约0.1秒，最少3秒）
        pause_seconds = max(3, len(greeting) * 0.1)
        time.sleep(pause_seconds)  # 等待问候语播放完毕
        self.resume_recording()  # 恢复录音
        
        # 主循环
        try:
            while True:
                # 只有在录音未暂停时才执行录音和命令处理
                if not self.recording_paused:
                    query = self.AIVoice()  # 获取语音输入
                    if query:  # 仅当有有效输入时处理命令
                        # 激活助手
                        if 'hey isabella' in query:
                            self.active = True
                            self.speech_engine.speak("I'm here, what can I do for you?")
                            # 播放响应后暂停录音，避免自录
                            self.pause_recording()
                            time.sleep(2)  # 等待响应播放完毕
                            self.resume_recording()
                            continue
                        if not self.active:
                            continue
                        
                        # 功能路由（原有逻辑保持不变）
                        if 'temperature' in query or 'television' in query:
                            self.handle_iot(query)
                        elif 'check the weather' in query:
                            match = re.search(r'in (\w+(?: \w+)*)', query)
                            if match:
                                place = match.group(1)
                                self.weather_service.getLocationWeather(place)
                            else:
                                self.speech_engine.speak("Could not extract the location from the query.")
                        elif 'check today weather information' in query:
                            self.weather_service.getWeatherInformation()
                            time.sleep(90)
                        elif 'report hardware status' in query:
                            self.hardware_reporter.ReportCurrentHardwareStatus()
                        elif 'volume' in query.lower():
                            self.os_controller.ControlOSFunction(query)
                        elif 'check server security' in query:
                            self.speak(f"Starting security scanning")
                            self.security_checker.CheckServerSecurity('192.168.68.54')
                        elif 'alarm' in query:
                            self.alarm_clock.alarmclock(query)
                        elif 'task' in query:
                            self.week_event.weekevent(query)
                        elif 'exit' in query or 'quit' in query:
                            break
                        else:
                            self.speech_engine.speak("Sorry, I didn't understand that command.")
                        self.pause_recording()
                        time.sleep(2.5)  # 等待响应播放完毕
                        self.resume_recording()
                        self.active = False  # 重置激活状态
                else:
                    time.sleep(5)  # 暂停时短暂休眠，降低CPU占用
        except Exception as e:
            print(f"Main loop error: {str(e)}")
        
if __name__ == '__main__':
    assistant = MainAssistant()
    assistant.run()