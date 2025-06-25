# -*- coding: utf-8 -*-
"""
GPIO统一管理器
防止多个模块之间的GPIO冲突
确保GPIO模式一致性和引脚使用不冲突
"""

import threading
import time

# 尝试导入GPIO模块
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("警告: 无法导入GPIO模块，将使用模拟模式")
    
    # 模拟GPIO类
    class MockGPIO:
        BOARD = "BOARD"
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        PUD_UP = "PUD_UP"
        PUD_DOWN = "PUD_DOWN"
        
        _pin_states = {}
        _mode = None
        
        @classmethod
        def setwarnings(cls, state):
            pass
        
        @classmethod
        def setmode(cls, mode):
            cls._mode = mode
        
        @classmethod
        def getmode(cls):
            return cls._mode
        
        @classmethod
        def setup(cls, pin, mode, **kwargs):
            cls._pin_states[pin] = cls.LOW
        
        @classmethod
        def output(cls, pin, value):
            cls._pin_states[pin] = value
        
        @classmethod
        def input(cls, pin):
            return cls._pin_states.get(pin, cls.LOW)
        
        @classmethod
        def gpio_function(cls, pin):
            return 0  # ALT0
        
        @classmethod
        def cleanup(cls, pin=None):
            if pin is None:
                cls._pin_states.clear()
            else:
                cls._pin_states.pop(pin, None)
        
        @classmethod
        def PWM(cls, pin, frequency):
            return MockPWM(pin, frequency)
    
    class MockPWM:
        def __init__(self, pin, frequency):
            self.pin = pin
            self.frequency = frequency
            
        def start(self, duty_cycle):
            pass
            
        def stop(self):
            pass
            
        def ChangeFrequency(self, freq):
            self.frequency = freq
    
    GPIO = MockGPIO


class GPIOManager:
    """GPIO统一管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GPIOManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.allocated_pins = {}  # {pin: module_name}
        self.gpio_mode = None
        self.gpio_initialized = False
        self.initialization_lock = threading.Lock()
        
        # 引脚映射表 (BCM -> BOARD)
        self.bcm_to_board = {
            2: 3, 3: 5, 4: 7, 5: 29, 6: 31, 7: 26, 8: 24, 9: 21,
            10: 19, 11: 23, 12: 32, 13: 33, 14: 8, 15: 10, 16: 36,
            17: 11, 18: 12, 19: 35, 20: 38, 21: 40, 22: 15, 23: 16,
            24: 18, 25: 22, 26: 37, 27: 13
        }
        
        # 引脚映射表 (BOARD -> BCM)
        self.board_to_bcm = {v: k for k, v in self.bcm_to_board.items()}
        
        print("GPIO管理器已初始化")
    
    def init_gpio(self, mode=GPIO.BOARD):
        """初始化GPIO系统（只能调用一次）"""
        with self.initialization_lock:
            if self.gpio_initialized:
                if self.gpio_mode != mode:
                    print(f"警告: GPIO已初始化为{self.gpio_mode}模式，无法更改为{mode}模式")
                    return False
                return True
            
            try:
                if GPIO_AVAILABLE:
                    GPIO.setwarnings(False)
                    GPIO.setmode(mode)
                    self.gpio_mode = mode
                    self.gpio_initialized = True
                    print(f"GPIO已初始化为{mode}模式")
                else:
                    GPIO.setmode(mode)
                    self.gpio_mode = mode
                    self.gpio_initialized = True
                    print(f"模拟GPIO已初始化为{mode}模式")
                return True
            except Exception as e:
                print(f"GPIO初始化失败: {e}")
                return False
    
    def allocate_pin(self, pin, module_name, pin_mode, **kwargs):
        """分配引脚给指定模块"""
        if not self.gpio_initialized:
            print("错误: GPIO未初始化，请先调用init_gpio()")
            return False
        
        # 标准化引脚号（根据当前模式）
        normalized_pin = self._normalize_pin(pin)
        if normalized_pin is None:
            print(f"无效的引脚号: {pin}")
            return False
        
        # 检查引脚是否已被占用
        if normalized_pin in self.allocated_pins:
            current_module = self.allocated_pins[normalized_pin]
            if current_module != module_name:
                print(f"引脚{normalized_pin}已被{current_module}占用，{module_name}无法使用")
                return False
            else:
                print(f"引脚{normalized_pin}已分配给{module_name}")
                return True
        
        try:
            # 配置引脚
            GPIO.setup(normalized_pin, pin_mode, **kwargs)
            self.allocated_pins[normalized_pin] = module_name
            print(f"引脚{normalized_pin}已分配给{module_name} (模式: {pin_mode})")
            return True
        except Exception as e:
            print(f"引脚{normalized_pin}配置失败: {e}")
            return False
    
    def release_pin(self, pin, module_name):
        """释放引脚"""
        normalized_pin = self._normalize_pin(pin)
        if normalized_pin is None:
            return
        
        if normalized_pin in self.allocated_pins:
            if self.allocated_pins[normalized_pin] == module_name:
                try:
                    if GPIO_AVAILABLE:
                        GPIO.cleanup(normalized_pin)
                    del self.allocated_pins[normalized_pin]
                    print(f"引脚{normalized_pin}已从{module_name}释放")
                except Exception as e:
                    print(f"释放引脚{normalized_pin}失败: {e}")
            else:
                print(f"引脚{normalized_pin}不属于{module_name}")
    
    def _normalize_pin(self, pin):
        """根据当前模式标准化引脚号"""
        if self.gpio_mode == GPIO.BOARD:
            return pin
        elif self.gpio_mode == GPIO.BCM:
            return pin
        else:
            print(f"未知的GPIO模式: {self.gpio_mode}")
            return None
    
    def convert_pin(self, pin, from_mode, to_mode=None):
        """转换引脚号（BCM <-> BOARD）"""
        if to_mode is None:
            to_mode = self.gpio_mode
        
        if from_mode == to_mode:
            return pin
        
        if from_mode == GPIO.BCM and to_mode == GPIO.BOARD:
            return self.bcm_to_board.get(pin)
        elif from_mode == GPIO.BOARD and to_mode == GPIO.BCM:
            return self.board_to_bcm.get(pin)
        else:
            return None
    
    def output(self, pin, value):
        """GPIO输出"""
        normalized_pin = self._normalize_pin(pin)
        if normalized_pin and normalized_pin in self.allocated_pins:
            try:
                GPIO.output(normalized_pin, value)
                return True
            except Exception as e:
                print(f"GPIO输出失败 (引脚{normalized_pin}): {e}")
        return False
    
    def input(self, pin):
        """GPIO输入"""
        normalized_pin = self._normalize_pin(pin)
        if normalized_pin and normalized_pin in self.allocated_pins:
            try:
                return GPIO.input(normalized_pin)
            except Exception as e:
                print(f"GPIO输入失败 (引脚{normalized_pin}): {e}")
        return 0
    
    def test_pin(self, pin, module_name="test"):
        """测试引脚是否可用"""
        if not self.gpio_initialized:
            return False
        
        normalized_pin = self._normalize_pin(pin)
        if normalized_pin is None:
            return False
        
        # 检查是否已被占用
        if normalized_pin in self.allocated_pins:
            return False
        
        try:
            # 临时分配测试
            GPIO.setup(normalized_pin, GPIO.OUT)
            GPIO.output(normalized_pin, GPIO.LOW)
            low_state = GPIO.input(normalized_pin)
            GPIO.output(normalized_pin, GPIO.HIGH)
            high_state = GPIO.input(normalized_pin)
            GPIO.output(normalized_pin, GPIO.LOW)
            
            # 清理测试配置
            if GPIO_AVAILABLE:
                GPIO.cleanup(normalized_pin)
            
            return low_state == 0 and high_state == 1
        except Exception as e:
            print(f"引脚{normalized_pin}测试失败: {e}")
            return False
    
    def get_allocated_pins(self):
        """获取已分配的引脚列表"""
        return dict(self.allocated_pins)
    
    def find_available_pins(self, count=1, exclude_pins=None):
        """查找可用的引脚"""
        if exclude_pins is None:
            exclude_pins = []
        
        # 安全的GPIO引脚列表（避开I2C、SPI等特殊功能引脚）
        if self.gpio_mode == GPIO.BOARD:
            safe_pins = [11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40]
        else:  # BCM
            safe_pins = [17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7, 5, 6, 12, 13, 19, 16, 26, 20, 21]
        
        available_pins = []
        for pin in safe_pins:
            if pin not in exclude_pins and pin not in self.allocated_pins:
                if self.test_pin(pin):
                    available_pins.append(pin)
                    if len(available_pins) >= count:
                        break
        
        return available_pins
    
    def cleanup_all(self, force=False):
        """清理所有GPIO资源"""
        if force or len(self.allocated_pins) > 0:
            print("清理所有GPIO资源...")
            try:
                if GPIO_AVAILABLE:
                    GPIO.cleanup()
                self.allocated_pins.clear()
                self.gpio_initialized = False
                self.gpio_mode = None
                print("GPIO资源已清理")
            except Exception as e:
                print(f"GPIO清理失败: {e}")
    
    def get_status(self):
        """获取GPIO管理器状态"""
        return {
            "initialized": self.gpio_initialized,
            "mode": self.gpio_mode,
            "allocated_pins": dict(self.allocated_pins),
            "gpio_available": GPIO_AVAILABLE
        }


# 全局GPIO管理器实例
gpio_manager = GPIOManager()

# 便捷函数
def init_gpio(mode=GPIO.BOARD):
    """初始化GPIO系统"""
    return gpio_manager.init_gpio(mode)

def allocate_pin(pin, module_name, pin_mode, **kwargs):
    """分配引脚"""
    return gpio_manager.allocate_pin(pin, module_name, pin_mode, **kwargs)

def release_pin(pin, module_name):
    """释放引脚"""
    gpio_manager.release_pin(pin, module_name)

def output(pin, value):
    """GPIO输出"""
    return gpio_manager.output(pin, value)

def input_pin(pin):
    """GPIO输入"""
    return gpio_manager.input(pin)

def cleanup_all():
    """清理所有GPIO"""
    gpio_manager.cleanup_all()

def get_status():
    """获取状态"""
    return gpio_manager.get_status()
