import psutil

class HardwareStatusReporter:
    def __init__(self, speak):
        self.speak = speak
        
    def ReportCurrentHardwareStatus(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        mem_total = round(memory.total / (1024 ** 3), 2)
        mem_used = round(memory.used / (1024 ** 3), 2)
        mem_percent = memory.percent
        try:
            battery = psutil.sensors_battery()
            battery_percent = battery.percent
            power_plugged = "plugged in" if battery.power_plugged else "not plugged"
        except:
            battery_percent = "N/A"
            power_plugged = "N/A"
        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_used = round(disk.used / (1024 ** 3), 2)
        disk_percent = disk.percent
        report = (
            f"CPU usage: {cpu_percent}%. "
            f"Memory: {mem_used} gigabytes used out of {mem_total}, {mem_percent}%. "
            f"Disk: {disk_used} gigabytes used out of {disk_total}, {disk_percent}%. "
            f"Battery: {battery_percent}% and {power_plugged}."
        )
        print(report)
        self.speak(report)