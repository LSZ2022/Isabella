import comtypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume

class VolumeControl:
    def __init__(self):
        # 初始化音量控制
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # 获取默认音频会话（用于设置应用音量）
        sessions = AudioUtilities.GetAllSessions()
        self.default_session = None
        for session in sessions:
            if session.Process and session.Process.name() == "SystemSoundsDevice.exe":
                self.default_session = session
                break
        if not self.default_session:
            self.default_session = sessions[0] if sessions else None
        
        # 创建一个空的 GUID 用于事件上下文（可固定值或随机生成）
        self.event_context = comtypes.GUID('{00000000-0000-0000-0000-000000000000}')

    def get_system_volume(self):
        """获取当前系统音量（0.0-1.0）"""
        return self.volume.GetMasterVolumeLevelScalar()

    def set_system_volume(self, level):
        """设置系统音量（0.0-1.0）"""
        try:
            # 确保音量在有效范围内
            level = max(0.0, min(1.0, level))
            # 添加 pguidEventContext 参数（使用空 GUID）
            self.volume.SetMasterVolumeLevelScalar(level, self.event_context)
        except Exception as e:
            print(f"Error setting volume: {e}")

    def adjust_system_volume(self, delta):
        """调整系统音量（增加/减少）"""
        current = self.get_system_volume()
        new_level = current + delta
        self.set_system_volume(new_level)