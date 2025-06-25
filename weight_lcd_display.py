"""
HX711称重传感器 + 1602 I2C LCD显示屏
集成重量显示系统

基于现有的HX711.py模块，添加LCD显示功能
"""

import sys
import os
import time
from datetime import datetime
import json

# 添加HX711模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'HX711'))

# 导入现有的HX711模块
try:
    from hx711 import HX711
    print("✓ 成功导入HX711模块")
except ImportError as e:
    print(f"✗ 无法导入HX711模块: {e}")
    print("请确保HX711文件夹和hx711.py文件存在")
    sys.exit(1)

# 导入LCD模块
import smbus

class LCD1602_I2C:
    def __init__(self, addr=0x27, bus=1):
        self.addr = addr
        try:
            self.bus = smbus.SMBus(bus)
            self.init_lcd()
            self.set_brightness(True)
            print(f"✓ LCD初始化成功，I2C地址：0x{addr:02X}")
        except Exception as e:
            print(f"✗ LCD初始化失败：{e}")
            raise
    
    def write_byte(self, data):
        self.bus.write_byte(self.addr, data)
    
    def write_command_with_backlight(self, cmd, backlight=True):
        backlight_bit = 0x08 if backlight else 0x00
        buf = cmd & 0xF0
        buf |= 0x04 | backlight_bit
        self.write_byte(buf)
        time.sleep(0.002)
        buf &= 0xFB
        buf |= backlight_bit
        self.write_byte(buf)
        
        buf = (cmd & 0x0F) << 4
        buf |= 0x04 | backlight_bit
        self.write_byte(buf)
        time.sleep(0.002)
        buf &= 0xFB
        buf |= backlight_bit
        self.write_byte(buf)
    
    def write_data_with_backlight(self, data, backlight=True):
        backlight_bit = 0x08 if backlight else 0x00
        buf = data & 0xF0
        buf |= 0x05 | backlight_bit
        self.write_byte(buf)
        time.sleep(0.002)
        buf &= 0xFB
        buf |= backlight_bit
        self.write_byte(buf)
        
        buf = (data & 0x0F) << 4
        buf |= 0x05 | backlight_bit
        self.write_byte(buf)
        time.sleep(0.002)
        buf &= 0xFB
        buf |= backlight_bit
        self.write_byte(buf)
    
    def init_lcd(self):
        self.write_byte(0x08)
        time.sleep(0.1)
        self.write_command_with_backlight(0x33)
        time.sleep(0.005)
        self.write_command_with_backlight(0x32)
        time.sleep(0.005)
        self.write_command_with_backlight(0x28)
        time.sleep(0.005)
        self.write_command_with_backlight(0x0C)
        time.sleep(0.005)
        self.write_command_with_backlight(0x06)
        time.sleep(0.005)
        self.write_command_with_backlight(0x01)
        time.sleep(0.5)
    
    def set_brightness(self, bright=True):
        if bright:
            self.write_command_with_backlight(0x0C)
            self.write_byte(0x0F)
    
    def clear(self):
        self.write_command_with_backlight(0x01)
        time.sleep(0.002)
    
    def set_cursor(self, line, column):
        if line == 0:
            addr = 0x80 + column
        else:
            addr = 0xC0 + column
        self.write_command_with_backlight(addr)
    
    def print(self, text, line=0, column=0):
        self.set_cursor(line, column)
        for char in str(text):
            self.write_data_with_backlight(ord(char), True)

class WeightLCDDisplay:
    def __init__(self):
        """初始化重量LCD显示系统"""
        self.lcd = None
        self.scale = None
        self.unit = "g"
        self.max_weight = 0
        self.min_weight = float('inf')
        self.is_stable = False
        self.stable_count = 0
        self.last_weight = 0
        self.weight_history = []
        self.display_mode = 0  # 0:重量 1:统计 2:时间
        
        # 新增：重量监控功能
        self.config = self.load_monitoring_config()
        self.weight_monitor = None
        if self.config.get('enable_music', False):
            try:
                from raspberry_pi_badapple_beep import BadAppleBuzzer
                self.buzzer_class = BadAppleBuzzer
            except ImportError:
                print("警告: 无法导入蜂鸣器模块")
                self.buzzer_class = None
    
    def load_monitoring_config(self):
        """加载监控配置"""
        config_file = "hx711_calibration.json"
        default_config = {
            "standard_weight": 200.0,
            "weight_tolerance": 10.0,
            "check_timeout": 10.0,
            "enable_music": True,
            "buzzer_pin": 18
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return default_config
        except Exception as e:
            print(f"加载监控配置失败: {e}")
            return default_config
    
    def initialize_hardware(self):
        """初始化硬件设备"""
        try:
            print("正在初始化硬件...")
            
            # 初始化LCD
            self.lcd = LCD1602_I2C()
            self.lcd.clear()
            self.lcd.print("Initializing...", 0, 0)
            self.lcd.print("HX711 + LCD", 1, 0)
            time.sleep(2)
            
            # 初始化HX711（使用现有的HX711类）
            print("正在初始化HX711称重传感器...")
            self.scale = HX711()  # 使用您的HX711类
            
            self.lcd.clear()
            self.lcd.print("Hardware Ready", 0, 0)
            self.lcd.print("Starting...", 1, 0)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            error_msg = f"硬件初始化失败: {e}"
            print(error_msg)
            if self.lcd:
                self.lcd.clear()
                self.lcd.print("Init Error!", 0, 0)
                self.lcd.print(str(e)[:16], 1, 0)
            return False
    
    def perform_tare(self):
        """执行去皮操作"""
        self.lcd.clear()
        self.lcd.print("Taring...", 0, 0)
        self.lcd.print("Remove all items", 1, 0)
        
        # 倒计时
        for i in range(3, 0, -1):
            self.lcd.print(f"Wait {i}s", 1, 12)
            time.sleep(1)
        
        # 执行去皮
        self.scale.tare(times=15)
        self.max_weight = 0
        self.min_weight = float('inf')
        self.weight_history.clear()
        
        self.lcd.clear()
        self.lcd.print("Tare Complete!", 0, 0)
        self.lcd.print("Ready to weigh", 1, 0)
        time.sleep(2)
    
    def format_weight(self, weight):
        """格式化重量显示"""
        if self.unit == "kg":
            weight_kg = weight / 1000
            if weight_kg < 0.01:
                return "0.00kg"
            else:
                return f"{weight_kg:.2f}kg"
        else:
            if weight < 0.1:
                return "0.0g"
            elif weight < 10:
                return f"{weight:.1f}g"
            else:
                return f"{int(weight)}g"
    
    def check_stability(self, current_weight):
        """检查重量稳定性"""
        tolerance = 1.0  # 1克的稳定容差
        
        if abs(current_weight - self.last_weight) <= tolerance:
            self.stable_count += 1
        else:
            self.stable_count = 0
        
        self.is_stable = self.stable_count >= 3
        self.last_weight = current_weight
    
    def update_statistics(self, weight):
        """更新重量统计"""
        if weight > 0.5:  # 只有重量大于0.5g时才更新统计
            if weight > self.max_weight:
                self.max_weight = weight
            if weight < self.min_weight:
                self.min_weight = weight
        
        # 保持重量历史记录
        self.weight_history.append(weight)
        if len(self.weight_history) > 10:
            self.weight_history.pop(0)
    
    def display_weight_mode(self, weight):
        """显示重量模式"""
        weight_str = self.format_weight(weight)
        stability_indicator = "●" if self.is_stable else "○"
        
        # 第一行：重量 + 稳定性指示
        line1 = f"{weight_str:>11s} {stability_indicator}"
        
        # 第二行：最大值 + 时间
        max_str = self.format_weight(self.max_weight) if self.max_weight > 0 else "---"
        current_time = time.strftime("%H:%M")
        line2 = f"Max:{max_str:>6s} {current_time}"
        
        self.lcd.clear()
        self.lcd.print(line1, 0, 0)
        self.lcd.print(line2, 1, 0)
    
    def display_statistics_mode(self, weight):
        """显示统计模式"""
        avg_weight = sum(self.weight_history) / len(self.weight_history) if self.weight_history else 0
        
        line1 = f"Avg:{self.format_weight(avg_weight):>9s}"
        line2 = f"Min:{self.format_weight(self.min_weight if self.min_weight != float('inf') else 0):>9s}"
        
        self.lcd.clear()
        self.lcd.print(line1, 0, 0)
        self.lcd.print(line2, 1, 0)
    
    def display_time_mode(self, weight):
        """显示时间模式"""
        current_time = datetime.now()
        line1 = current_time.strftime("%Y-%m-%d")
        line2 = current_time.strftime("%H:%M:%S") + f" {self.format_weight(weight):>6s}"
        
        self.lcd.clear()
        self.lcd.print(line1, 0, 0)
        self.lcd.print(line2, 1, 0)
    
    def display_current_mode(self, weight):
        """根据当前模式显示信息"""
        if self.display_mode == 0:
            self.display_weight_mode(weight)
        elif self.display_mode == 1:
            self.display_statistics_mode(weight)
        elif self.display_mode == 2:
            self.display_time_mode(weight)
    
    def run_measurement_loop(self):
        """运行主测量循环"""
        print("\n开始重量测量...")
        print("控制命令：")
        print("- t: 去皮")
        print("- u: 切换单位(g/kg)")
        print("- m: 切换显示模式")
        print("- r: 重置统计")
        print("- q: 退出")
        print("- Enter: 继续")
        
        measurement_count = 0
        
        try:
            while True:
                # 获取稳定重量（使用您的HX711类的方法）
                weight = self.scale.get_stable_weight(times=5)
                
                # 检查稳定性
                self.check_stability(weight)
                
                # 更新统计
                self.update_statistics(weight)
                
                # 显示当前模式的信息
                self.display_current_mode(weight)
                
                # 控制台输出（每10次测量输出一次）
                measurement_count += 1
                if measurement_count % 10 == 0:
                    stability_text = "稳定" if self.is_stable else "变化"
                    mode_text = ["重量", "统计", "时间"][self.display_mode]
                    print(f"重量: {weight:.1f}g ({stability_text}) - 模式: {mode_text}")
                
                # 检查用户输入
                try:
                    import select
                    import sys
                    
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        command = input().strip().lower()
                        
                        if command == 't':
                            self.perform_tare()
                        elif command == 'u':
                            self.unit = "kg" if self.unit == "g" else "g"
                            self.lcd.clear()
                            self.lcd.print(f"Unit: {self.unit}", 0, 0)
                            time.sleep(1)
                        elif command == 'm':
                            self.display_mode = (self.display_mode + 1) % 3
                            mode_names = ["Weight", "Statistics", "Time"]
                            self.lcd.clear()
                            self.lcd.print("Mode:", 0, 0)
                            self.lcd.print(mode_names[self.display_mode], 1, 0)
                            time.sleep(1)
                        elif command == 'r':
                            self.max_weight = 0
                            self.min_weight = float('inf')
                            self.weight_history.clear()
                            self.lcd.clear()
                            self.lcd.print("Statistics", 0, 0)
                            self.lcd.print("Reset!", 1, 0)
                            time.sleep(1)
                        elif command == 'q':
                            break
                
                except:
                    pass  # 忽略输入检查错误
                
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\n用户中断测量")
    
    def run(self):
        """运行主程序"""
        print("=" * 60)
        print("    HX711称重传感器 + LCD1602显示屏 系统")
        print("=" * 60)
        
        if not self.initialize_hardware():
            print("硬件初始化失败，程序退出")
            return
        
        try:
            # 显示欢迎信息
            self.lcd.clear()
            self.lcd.print("Weight Display", 0, 0)
            self.lcd.print("System Ready", 1, 0)
            time.sleep(2)
            
            # 检查校准状态
            if not self.scale.is_calibrated:
                self.lcd.clear()
                self.lcd.print("Not Calibrated!", 0, 0)
                self.lcd.print("Check setup", 1, 0)
                print("⚠ 警告：传感器未校准")
                print("建议先运行 HX711/hx711_calibration.py 进行校准")
                time.sleep(3)
            
            # 询问是否需要去皮
            self.lcd.clear()
            self.lcd.print("Need Tare?", 0, 0)
            self.lcd.print("y/n + Enter", 1, 0)
            
            choice = input("是否需要去皮操作？(y/n): ").lower().strip()
            if choice == 'y':
                self.perform_tare()
            
            # 开始测量循环
            self.run_measurement_loop()
            
        except Exception as e:
            error_msg = f"程序运行错误: {e}"
            print(error_msg)
            if self.lcd:
                self.lcd.clear()
                self.lcd.print("System Error!", 0, 0)
                self.lcd.print(str(e)[:16], 1, 0)
        finally:
            # 清理资源
            if self.scale:
                self.scale.cleanup()
            if self.lcd:
                self.lcd.clear()
                self.lcd.print("System", 0, 0)
                self.lcd.print("Shutdown", 1, 0)
            print("系统已关闭")

def main():
    """主函数"""
    system = WeightLCDDisplay()
    system.run()

if __name__ == "__main__":
    main()
