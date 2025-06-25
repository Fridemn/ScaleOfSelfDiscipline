"""
HX711称重传感器 + LCD显示屏 主程序
简洁版本，调用hx711和lcd_display模块
集成重量监控和音乐播放功能
"""

import time
import threading
import json
import os
from datetime import datetime
from hx711 import HX711
from lcd_display import LCD1602_I2C, format_weight

# 导入蜂鸣器模块
try:
    from raspberry_pi_badapple_beep import BadAppleBuzzer
    BUZZER_AVAILABLE = True
except ImportError:
    BUZZER_AVAILABLE = False
    print("警告: 无法导入蜂鸣器模块，音乐功能将被禁用")

class WeightMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.music_playing = False
        self.buzzer = None
        self.music_thread = None
        
    def load_config(self):
        """加载配置文件"""
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
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return default_config
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return default_config
    
    def start_music(self):
        """启动音乐播放"""
        if not BUZZER_AVAILABLE or not self.config.get("enable_music", True):
            print("音乐功能未启用或不可用")
            return
        
        if self.music_playing:
            return
        
        try:
            print("正在初始化蜂鸣器...")
            # 使用配置文件中的引脚号（BCM编号）
            buzzer_pin = self.config.get("buzzer_pin", 18)
            self.buzzer = BadAppleBuzzer(beep_pin=buzzer_pin)
            
            if not self.buzzer.gpio_initialized:
                print("蜂鸣器GPIO初始化失败，无法播放音乐")
                return
                
            self.music_playing = True
            
            def play_music():
                try:
                    print("开始播放Bad Apple音乐...")
                    self.buzzer.play_melody()
                except Exception as e:
                    print(f"音乐播放出错: {e}")
                finally:
                    self.music_playing = False
                    print("音乐播放结束")
            
            self.music_thread = threading.Thread(target=play_music, daemon=True)
            self.music_thread.start()
            print("音乐线程已启动")
            
        except Exception as e:
            print(f"启动音乐失败: {e}")
            self.music_playing = False
            if self.buzzer:
                try:
                    self.buzzer.cleanup()
                except:
                    pass
                self.buzzer = None
    
    def stop_music(self):
        """停止音乐播放"""
        if self.music_playing and self.buzzer:
            print("正在停止音乐播放...")
            self.buzzer.stop()
            self.music_playing = False
            
            # 等待音乐线程结束
            if self.music_thread and self.music_thread.is_alive():
                self.music_thread.join(timeout=1.0)
            
            # 清理蜂鸣器
            if self.buzzer:
                try:
                    self.buzzer.cleanup()
                except:
                    pass
                self.buzzer = None
            print("音乐播放已停止")

def main():
    """主程序"""
    print("=" * 50)
    print("    HX711 + LCD1602 称重显示系统")
    print("    带重量监控和音乐提醒功能")
    print("=" * 50)
    
    # 初始化重量监控器
    monitor = WeightMonitor()
    
    # 显示配置信息
    print(f"标准重量: {monitor.config['standard_weight']}g")
    print(f"误差范围: ±{monitor.config['weight_tolerance']}g")
    print(f"检测时间: {monitor.config['check_timeout']}秒")
    print(f"音乐功能: {'启用' if monitor.config['enable_music'] else '禁用'}")
    print(f"蜂鸣器引脚: GPIO{monitor.config['buzzer_pin']} (BCM)")
    
    # 初始化硬件
    try:
        print("\n正在初始化硬件...")
        lcd = LCD1602_I2C()
        scale = HX711()
        
        lcd.clear()
        lcd.print("System Ready", 0, 0)
        lcd.print("Weight Monitor", 1, 0)
        time.sleep(2)
        
    except Exception as e:
        print(f"硬件初始化失败: {e}")
        return
    
    # 变量初始化
    max_weight = 0
    unit = "g"
    stable_count = 0
    last_weight = 0
    check_completed = False
    start_time = time.time()
    
    try:
        # 去皮操作
        lcd.clear()
        lcd.print("Taring...", 0, 0)
        lcd.print("Remove items", 1, 0)
        
        for i in range(3, 0, -1):
            lcd.print(f"Wait {i}s", 1, 10)
            time.sleep(1)
        
        scale.tare(times=10)
        
        lcd.clear()
        lcd.print("Tare Complete!", 0, 0)
        time.sleep(1)
        
        # 显示重量检测倒计时
        lcd.clear()
        lcd.print("Weight Check", 0, 0)
        lcd.print("Starting...", 1, 0)
        time.sleep(1)
        
        print(f"\n开始重量检测... (目标: {monitor.config['standard_weight']}±{monitor.config['weight_tolerance']}g)")
        print("按 Ctrl+C 停止")
        
        # 重置开始时间
        start_time = time.time()
        
        # 主测量循环
        while True:
            # 获取重量
            weight = scale.get_stable_weight(times=5)
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # 检查稳定性
            is_stable = abs(weight - last_weight) <= 1.0
            if is_stable:
                stable_count += 1
            else:
                stable_count = 0
            last_weight = weight
            
            # 更新最大值
            if weight > max_weight:
                max_weight = weight
            
            # 重量检测逻辑
            if not check_completed and elapsed_time <= monitor.config['check_timeout']:
                # 检测期间
                remaining_time = monitor.config['check_timeout'] - elapsed_time
                target_weight = monitor.config['standard_weight']
                tolerance = monitor.config['weight_tolerance']
                
                # 检查是否达到目标重量
                if abs(weight - target_weight) <= tolerance:
                    check_completed = True
                    monitor.stop_music()  # 确保音乐停止
                    lcd.clear()
                    lcd.print("Weight OK!", 0, 0)
                    lcd.print(f"{weight:.1f}g Detected", 1, 0)
                    time.sleep(2)
                    print(f"\n✓ 重量检测通过: {weight:.1f}g")
                else:
                    # 显示倒计时和当前重量
                    lcd.clear()
                    lcd.print(f"Check:{remaining_time:.0f}s", 0, 0)
                    lcd.print(f"Need {target_weight:.0f}g Got{weight:.0f}g", 1, 0)
            
            elif not check_completed and elapsed_time > monitor.config['check_timeout']:
                # 检测超时，未达到目标重量
                check_completed = True
                print(f"\n✗ 重量检测失败: 超时未达到{monitor.config['standard_weight']}g")
                
                if monitor.config['enable_music']:
                    lcd.clear()
                    lcd.print("Weight Failed!", 0, 0)
                    lcd.print("Playing Music...", 1, 0)
                    monitor.start_music()
                    time.sleep(2)
            
            # 正常显示模式
            if check_completed or elapsed_time > monitor.config['check_timeout']:
                weight_str = format_weight(weight, unit)
                stability_indicator = "●" if stable_count >= 3 else "○"
                current_time_str = time.strftime("%H:%M")
                
                # 第一行：重量 + 稳定性指示
                line1 = f"{weight_str:>11s} {stability_indicator}"
                # 第二行：最大值 + 时间 + 音乐状态
                max_str = format_weight(max_weight, unit)
                music_indicator = "♪" if monitor.music_playing else " "
                line2 = f"Max:{max_str:>6s}{music_indicator}{current_time_str}"
                
                lcd.clear()
                lcd.print(line1, 0, 0)
                lcd.print(line2, 1, 0)
            
            # 控制台输出
            stability_text = "稳定" if stable_count >= 3 else "变化"
            music_status = " [音乐播放中]" if monitor.music_playing else ""
            print(f"重量: {weight:8.2f}g ({stability_text}){music_status}", end='\r')
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n\n测量已停止")
        monitor.stop_music()
        lcd.clear()
        lcd.print("Measurement", 0, 0)
        lcd.print("Stopped", 1, 0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        monitor.stop_music()
        lcd.clear()
        lcd.print("Error!", 0, 0)
        lcd.print(str(e)[:16], 1, 0)
    finally:
        monitor.stop_music()
        # 先停止音乐，再清理称重传感器
        time.sleep(0.5)  # 给音乐停止一点时间
        scale.cleanup()
        print("程序已退出")

if __name__ == "__main__":
    main()
