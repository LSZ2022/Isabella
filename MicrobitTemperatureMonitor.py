import serial
import serial.tools.list_ports
import time
import threading

MICROBIT_VENDOR_ID = "0D28"
MICROBIT_PRODUCT_ID = "0204"
SERIAL_BAUDRATE = 115200
TEMPERATURE_UPDATE_INTERVAL = 10

class MicrobitTemperatureMonitor:
    def __init__(self):
        self.serial_port = None
        self.current_temperature = None
        self.last_update = None
        self.monitoring_active = False
        self.thread = None
        self.display_mode = "celsius"
        
    def find_microbit(self):
        ports = serial.tools.list_ports.comports()
        print("\nAvailable COM ports:")
        
        for port in ports:
            print(f"- {port.device}: {port.description}")
            
            if "microbit" in port.description.lower():
                print(f"Found Micro:bit by description: {port.device}")
                return port.device
                
            if port.vid is not None and port.pid is not None:
                vid_str = hex(port.vid)[2:].upper().zfill(4)
                pid_str = hex(port.pid)[2:].upper().zfill(4)
                
                if vid_str == MICROBIT_VENDOR_ID and pid_str == MICROBIT_PRODUCT_ID:
                    print(f"Found Micro:bit by ID: {port.device}")
                    return port.device
        
        print("!!! No Micro:bit device detected")
        return None
    
    def connect(self):
        if self.serial_port and self.serial_port.is_open:
            return True
            
        port = self.find_microbit()
        if not port:
            print("\nDebug: All available ports:")
            ports = serial.tools.list_ports.comports()
            for p in ports:
                vid = hex(p.vid)[2:].upper().zfill(4) if p.vid else "N/A"
                pid = hex(p.pid)[2:].upper().zfill(4) if p.pid else "N/A"
                print(f"  - {p.device}: {p.description} (VID:{vid}, PID:{pid})")
            return False
            
        try:
            print(f"Connecting to {port} at {SERIAL_BAUDRATE} baud...")
            self.serial_port = serial.Serial(
                port=port,
                baudrate=SERIAL_BAUDRATE,
                timeout=1
            )
            time.sleep(2)
            print("Connection successful!")
            return True
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            print("Disconnected from Micro:bit")
    
    def start_monitoring(self):
        if not self.connect():
            return False
            
        self.monitoring_active = True
        self.thread = threading.Thread(target=self._monitor_temperature)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop_monitoring(self):
        self.monitoring_active = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.disconnect()
    
    def _monitor_temperature(self):
        print("Start monitoring indoor temperature...")
        
        self._send_command("START_TEMP")
        
        if self.monitoring_active:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line.startswith("TEMP:"):
                        try:
                            temp_str = line.split(":")[1]
                            self.current_temperature = float(temp_str)
                            self.last_update = time.time()
                            print(f"Update temperature: {self.current_temperature}°C")
                            self._send_command("STOP_TEMP")
                        except (ValueError, IndexError):
                            print(f"Invalid temperature data: {line}")
                
            except Exception as e:
                print(f"Temperature monitoring error: {str(e)}")
                time.sleep(1)
        
        self._send_command("STOP_TEMP")
        print("Temperature monitoring has stopped")
    
    def _send_command(self, command):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(f"{command}\n".encode('utf-8'))
        except Exception as e:
            print(f"Failed to send command: {str(e)}")
    
    def get_current_temperature(self):
        if not self.current_temperature:
            return None
            
        if self.display_mode == "fahrenheit":
            return self.current_temperature * 9/5 + 32
        return self.current_temperature
    
    def get_temperature_status(self):
        if not self.current_temperature:
            return "Temperature data not yet obtained"
            
        temp = self.get_current_temperature()
        unit = "°F" if self.display_mode == "fahrenheit" else "°C"
       
        if self.display_mode == "celsius":
            if temp < 15:
                status = "Cold"
            elif 15 <= temp < 22:
                status = "Cool"
            elif 22 <= temp < 26:
                status = "Comfortable"
            elif 26 <= temp < 30:
                status = "Warm"
            else:
                status = "Hot"
        else:
            if temp < 59:
                status = "Cold"
            elif 59 <= temp < 72:
                status = "Cool"
            elif 72 <= temp < 79:
                status = "Comfortable"
            elif 79 <= temp < 86:
                status = "Warm"
            else:
                status = "Hot"
        
        return f"Current indoor temperature: {temp:.1f}{unit} ({status})"
    
    def toggle_display_mode(self):
        self.display_mode = "fahrenheit" if self.display_mode == "celsius" else "celsius"
        return self.display_mode
