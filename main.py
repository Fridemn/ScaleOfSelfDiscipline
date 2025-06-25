"""
HX711称重传感器 + LCD显示屏 主程序
简洁版本，调用hx711和lcd_display模块
集成重量监控、音乐播放和人脸检测功能
"""

import time
import threading
import json
import os
from datetime import datetime
from hx711 import HX711
from lcd_display import LCD1602_I2C, format_weight

# 导入GPIO统一管理器
from gpio_manager import gpio_manager, init_gpio, allocate_pin, release_pin, output, input_pin, GPIO_AVAILABLE, GPIO

# 导入蜂鸣器模块
try:
    from beep import BadAppleBuzzer
    BUZZER_AVAILABLE = True
except ImportError:
    BUZZER_AVAILABLE = False
    print("警告: 无法导入蜂鸣器模块，音乐功能将被禁用")

# 导入摄像头模块
try:
    from camera import USBCamera
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    print("警告: 无法导入摄像头模块，人脸检测功能将被禁用")

class WeightMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.music_playing = False
        self.buzzer = None
        self.music_thread = None
        self.camera = None
        self.face_detection_active = False
        self.face_detection_thread = None
        self.beep_queue = []  # 改为LED队列
        self.beep_lock = threading.Lock()  # 改为LED锁
        self.buzzer_method = None
        self.led_pin = 19  # LED引脚号（BCM编号）
        self.led_initialized = False
        self.gpio_manager_initialized = False  # GPIO管理器初始化状态
        # 不在初始化时就设置LED，等待其他硬件初始化完成后再设置
        
    def load_config(self):
        """加载配置文件"""
        config_file = "hx711_calibration.json"
        default_config = {
            "standard_weight": 200.0,
            "weight_tolerance": 10.0,
            "check_timeout": 10.0,
            "enable_music": True,
            "enable_face_detection": True,
            "buzzer_pin": 18,
            "camera_index": 0,
            "led_pin": 19  # 添加LED引脚配置
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
    
    def led_alert(self, duration=2):
        """LED警报 - 点亮指定时间"""
        if not GPIO_AVAILABLE or not self.led_initialized:
            print(f"LED警报: 点亮{duration}秒 (模拟)")
            return
        
        # 检查是否在主线程中
        if threading.current_thread() != threading.main_thread():
            # 如果不在主线程，将请求添加到队列
            with self.beep_lock:
                self.beep_queue.append(duration)
            print(f"LED警报请求已加入队列: 点亮{duration}秒")
            return
        
        # 在主线程中直接执行
        self._execute_led_sync(duration)
    
    def _execute_led_sync(self, duration):
        """在主线程中同步执行LED操作"""
        try:
            if not self.led_initialized:
                print("LED未初始化")
                return
            
            print(f"LED警报: 点亮{duration}秒")
            
            # 使用GPIO管理器进行输出
            current_state = input_pin(self.led_pin)
            print(f"LED当前状态: {'HIGH' if current_state else 'LOW'}")
            
            # 点亮LED
            if output(self.led_pin, GPIO.HIGH):
                print("💡 LED已点亮")
                
                # 验证LED是否真的点亮了
                new_state = input_pin(self.led_pin)
                print(f"LED设置后状态: {'HIGH' if new_state else 'LOW'}")
                if not new_state:
                    print("警告: LED可能没有正确点亮")
                
                # 保持点亮指定时间
                print(f"保持点亮{duration}秒...")
                time.sleep(duration)
                
                # 关闭LED
                if output(self.led_pin, GPIO.LOW):
                    print("💡 LED已关闭")
                    
                    # 验证LED是否真的关闭了
                    final_state = input_pin(self.led_pin)
                    print(f"LED关闭后状态: {'HIGH' if final_state else 'LOW'}")
            else:
                print("LED输出失败，使用模拟模式")
                self._simulate_led_alert(duration)
            
        except Exception as e:
            print(f"LED警报失败: {e}")
            self._simulate_led_alert(duration)
    
    def _simulate_led_alert(self, duration):
        """模拟LED警报"""
        print(f"💡 模拟LED警报: 闪烁{duration}次")
        for i in range(int(duration)):
            print(f"💡 闪烁 {i+1}/{int(duration)}")
            time.sleep(0.5)
    
    def process_beep_queue(self):
        """处理LED队列（在主线程中调用）"""
        with self.beep_lock:
            while self.beep_queue:
                duration = self.beep_queue.pop(0)
                # 直接在主线程中执行LED操作
                self._execute_led_sync(duration)
    
    def _test_buzzer_methods(self, buzzer):
        """测试蜂鸣器可用的方法"""
        if self.buzzer_method:
            return self.buzzer_method
            
        test_methods = [
            ('beep', lambda b, duration: b.beep(duration)),
            ('buzz', lambda b, duration: b.buzz(duration)),
            ('play_beep', lambda b, duration: b.play_beep(duration)),
            ('simple_beep', lambda b, duration: b.simple_beep(duration)),
            ('play_tone', lambda b, duration: b.play_tone(1000, duration)),
            ('tone', lambda b, duration: b.tone(1000, duration))
        ]
        
        for method_name, method_func in test_methods:
            if hasattr(buzzer, method_name):
                try:
                    # 测试调用
                    method_func(buzzer, 0.1)
                    self.buzzer_method = (method_name, method_func)
                    print(f"找到可用的蜂鸣器方法: {method_name}")
                    return self.buzzer_method
                except Exception as e:
                    print(f"方法 {method_name} 测试失败: {e}")
                    continue
        
        # 如果都不行，返回None
        methods = [method for method in dir(buzzer) if not method.startswith('_') and callable(getattr(buzzer, method))]
        print(f"无法找到可用的蜂鸣器方法。可用方法: {methods}")
        return None
    
    def _execute_beep_sync(self, count):
        """在主线程中同步执行蜂鸣器操作"""
        try:
            buzzer_pin = self.config.get("buzzer_pin", 18)
            temp_buzzer = BadAppleBuzzer(beep_pin=buzzer_pin)
            
            if not temp_buzzer.gpio_initialized:
                print("蜂鸣器GPIO初始化失败")
                return
            
            print(f"蜂鸣器警报: 响{count}声")
            
            # 测试并获取可用的蜂鸣器方法
            buzzer_method = self._test_buzzer_methods(temp_buzzer)
            
            if buzzer_method:
                method_name, method_func = buzzer_method
                for i in range(count):
                    try:
                        method_func(temp_buzzer, 0.2)
                        if i < count - 1:
                            time.sleep(0.3)
                    except Exception as e:
                        print(f"蜂鸣器响声失败: {e}")
                        print(f"BEEP {i+1}/{count} (模拟)")
                        if i < count - 1:
                            time.sleep(0.3)
            else:
                # 完全模拟
                print("使用完全模拟的蜂鸣器警报")
                for i in range(count):
                    print(f"🔊 BEEP {i+1}!")
                    if i < count - 1:
                        time.sleep(0.3)
            
            temp_buzzer.cleanup()
            
        except Exception as e:
            print(f"蜂鸣器警报失败: {e}")
            # 完全模拟的备用方案
            print(f"使用模拟蜂鸣器警报: 响{count}声")
            for i in range(count):
                print(f"🔊 BEEP {i+1}!")
                if i < count - 1:
                    time.sleep(0.3)

    def init_camera(self):
        """初始化摄像头"""
        if not CAMERA_AVAILABLE or not self.config.get("enable_face_detection", True):
            print("摄像头功能未启用或不可用")
            return False
        
        try:
            camera_index = self.config.get("camera_index", 0)
            self.camera = USBCamera(camera_index=camera_index)
            
            # 检查摄像头是否真正可用
            if not self.camera.camera_available:
                print("摄像头初始化失败，硬件不可用")
                self.camera = None
                return False
                
            print(f"摄像头已初始化，索引: {camera_index}")
            return True
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            self.camera = None
            return False
    
    def start_face_detection(self):
        """启动人脸检测"""
        if not self.camera or not self.camera.camera_available or self.face_detection_active:
            if not self.camera:
                print("摄像头未初始化，无法启动人脸检测")
            elif not self.camera.camera_available:
                print("摄像头不可用，无法启动人脸检测")
            return
        
        # 检查人脸检测器是否可用
        if self.camera.face_detection_method is None:
            print("人脸检测器不可用，无法启动人脸检测")
            print("提示: OpenCV人脸检测功能初始化失败")
            return
        
        print(f"启动人脸检测，使用方法: {self.camera.face_detection_method}")
        print(f"LED状态: {'已初始化' if self.led_initialized else '未初始化'}")
        self.face_detection_active = True
        
        def face_detection_worker():
            print("人脸检测线程已启动")
            frame_count = 0
            detection_interval = 30  # 增加检测间隔，减少误触发
            consecutive_failures = 0
            max_failures = 10
            last_face_detection = 0  # 上次检测到人脸的时间
            cooldown_period = 5  # 冷却期5秒，避免频繁触发
            
            try:
                while self.face_detection_active:
                    try:
                        ret, frame = self.camera.cap.read()
                        if not ret or frame is None:
                            consecutive_failures += 1
                            if consecutive_failures >= max_failures:
                                print("连续读取摄像头失败过多，退出人脸检测")
                                break
                            if consecutive_failures <= 3:
                                print(f"无法读取摄像头画面 (失败次数: {consecutive_failures})")
                            time.sleep(1)
                            continue
                        
                        consecutive_failures = 0
                        
                        # 每隔几帧进行一次人脸检测
                        if frame_count % detection_interval == 0:
                            faces = self.camera.detect_faces(frame)
                            
                            if len(faces) > 0:
                                current_time = time.time()
                                # 检查冷却期
                                if current_time - last_face_detection > cooldown_period:
                                    print(f"检测到人脸! 触发LED警报 (检测到{len(faces)}个人脸)")
                                    last_face_detection = current_time
                                    # 将LED请求添加到队列
                                    self.led_alert(3)  # LED点亮3秒
                                else:
                                    print(f"检测到人脸但在冷却期内，跳过触发")
                        
                        frame_count += 1
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"人脸检测帧处理出错: {e}")
                        time.sleep(1)
                        continue
                    
            except Exception as e:
                print(f"人脸检测出错: {e}")
            finally:
                self.face_detection_active = False
                print("人脸检测线程已退出")
        
        self.face_detection_thread = threading.Thread(target=face_detection_worker, daemon=True)
        self.face_detection_thread.start()
    
    def stop_face_detection(self):
        """停止人脸检测"""
        if self.face_detection_active:
            print("正在停止人脸检测...")
            self.face_detection_active = False
            
            if self.face_detection_thread and self.face_detection_thread.is_alive():
                self.face_detection_thread.join(timeout=2.0)
            
            print("人脸检测已停止")
    
    def cleanup_camera(self):
        """清理摄像头资源"""
        self.stop_face_detection()
        if self.camera:
            try:
                self.camera.cleanup()
            except:
                pass
            self.camera = None
    
    def cleanup_led(self):
        """清理LED资源 - 使用GPIO管理器"""
        if self.led_initialized and GPIO_AVAILABLE:
            try:
                # 确保LED关闭
                output(self.led_pin, GPIO.LOW)
                print("LED已关闭")
                
                # 释放LED引脚
                release_pin(self.led_pin, "WeightMonitor")
                self.led_initialized = False
                
                print("LED资源已清理")
            except Exception as e:
                print(f"LED资源清理失败: {e}")

    def setup_led(self):
        """初始化LED GPIO - 使用GPIO管理器"""
        if not GPIO_AVAILABLE:
            print("GPIO模块不可用，LED功能将被禁用")
            return
        
        if not self.gpio_manager_initialized:
            print("GPIO管理器未初始化，无法设置LED")
            return
        
        # 获取配置的LED引脚
        config_led_pin = self.config.get("led_pin", 19)
        
        # 转换引脚号（从BCM转换为BOARD模式）
        board_pin = gpio_manager.convert_pin(config_led_pin, GPIO.BCM, GPIO.BOARD)
        if board_pin is None:
            print(f"无效的LED引脚配置: GPIO{config_led_pin} (BCM)")
            return
        
        print(f"开始初始化LED，配置引脚: GPIO{config_led_pin} (BCM) -> 引脚{board_pin} (BOARD)")
        
        try:
            # 使用GPIO管理器分配引脚
            if allocate_pin(board_pin, "WeightMonitor", GPIO.OUT):
                self.led_pin = board_pin  # 使用BOARD引脚号
                self.led_initialized = True
                
                # 确保LED初始状态为关闭
                output(self.led_pin, GPIO.LOW)
                
                print(f"✓ LED成功初始化在引脚{board_pin} (对应BCM GPIO{config_led_pin})")
                
                # 进行LED测试
                self._test_led_functionality()
                return
            else:
                print(f"LED引脚{board_pin}分配失败，尝试自动寻找可用引脚...")
                self._auto_find_led_pin()
        
        except Exception as e:
            print(f"LED初始化失败: {e}")
            self.led_initialized = False
    
    def _auto_find_led_pin(self):
        """自动寻找可用的LED引脚"""
        print("正在自动寻找可用的LED引脚...")
        
        # 避开已知被占用的引脚（HX711使用11,13，蜂鸣器使用12）
        exclude_pins = [11, 12, 13]  # BOARD引脚号
        
        # 寻找可用引脚
        available_pins = gpio_manager.find_available_pins(count=1, exclude_pins=exclude_pins)
        
        if available_pins:
            pin = available_pins[0]
            print(f"找到可用引脚: {pin}")
            
            if allocate_pin(pin, "WeightMonitor", GPIO.OUT):
                self.led_pin = pin
                self.led_initialized = True
                output(self.led_pin, GPIO.LOW)
                
                # 更新配置文件
                bcm_pin = gpio_manager.convert_pin(pin, GPIO.BOARD, GPIO.BCM)
                if bcm_pin:
                    self.config["led_pin"] = bcm_pin
                    self._save_config()
                    print(f"✓ LED成功初始化在自动分配的引脚{pin} (对应BCM GPIO{bcm_pin})")
                    print(f"配置已更新")
                    
                    # 进行LED测试
                    self._test_led_functionality()
                    return
        
        print("✗ 无法找到可用的LED引脚")
        self._diagnose_hardware_issue()
    
    def _test_led_functionality(self):
        """测试LED功能"""
        print("正在测试LED功能...")
        try:
            # 快速闪烁测试
            for i in range(3):
                output(self.led_pin, GPIO.HIGH)
                time.sleep(0.2)
                output(self.led_pin, GPIO.LOW)
                time.sleep(0.2)
            print("✓ LED功能测试通过")
        except Exception as e:
            print(f"LED功能测试失败: {e}")
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open("hx711_calibration.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    def _diagnose_hardware_issue(self):
        """诊断硬件问题"""
        print("\n" + "=" * 50)
        print("LED硬件问题诊断")
        print("=" * 50)
        
        # 显示GPIO管理器状态
        status = gpio_manager.get_status()
        print(f"GPIO管理器状态:")
        print(f"  - 已初始化: {status['initialized']}")
        print(f"  - GPIO模式: {status['mode']}")
        print(f"  - GPIO可用性: {status['gpio_available']}")
        print(f"  - 已分配引脚: {status['allocated_pins']}")
        
        print("\n可能的问题:")
        print("1. LED连接问题:")
        print("   - LED长脚(正极)是否连接到GPIO引脚?")
        print("   - LED短脚(负极)是否连接到GND?")
        print("   - 连接线是否松动?")
        
        print("\n2. 电阻问题:")
        print("   - 是否使用了限流电阻(220Ω-1kΩ)?")
        print("   - 电阻是否损坏?")
        
        print("\n3. LED问题:")
        print("   - LED是否损坏?")
        print("   - LED极性是否正确?")
        
        print("\n4. 引脚冲突:")
        print("   - 检查引脚是否被其他设备占用")
        print("   - HX711使用引脚11,13 (BOARD)")
        print("   - 蜂鸣器使用引脚12 (BOARD)")
        
        print("\n建议的解决方案:")
        print("1. 使用万用表测试GPIO引脚电压")
        print("2. 更换LED和电阻")
        print("3. 检查所有连接线")
        print("4. 尝试连接到不同的GPIO引脚")
        print("=" * 50)
    
    def _execute_led_sync(self, duration):
        """在主线程中同步执行LED操作 - 使用GPIO管理器的简化版本"""
        if not self.led_initialized:
            print(f"LED警报: 点亮{duration}秒 (模拟 - LED未初始化)")
            return
        
        try:
            print(f"💡 LED警报: 闪烁{duration}次 (引脚{self.led_pin})")
            
            # 执行更明显的闪烁模式
            flash_count = max(3, int(duration))  # 至少闪烁3次
            
            for i in range(flash_count):
                if output(self.led_pin, GPIO.HIGH):
                    time.sleep(0.5)  # 点亮0.5秒
                    output(self.led_pin, GPIO.LOW)
                    if i < flash_count - 1:  # 最后一次不需要间隔
                        time.sleep(0.5)  # 熄灭0.5秒
                else:
                    print(f"LED输出失败，第{i+1}次闪烁")
                    time.sleep(0.5)
            
            print("💡 LED闪烁完成")
            
        except Exception as e:
            print(f"LED操作失败: {e}")
            self._simulate_led_alert(duration)

    def init_gpio_system(self):
        """统一初始化GPIO系统"""
        if self.gpio_manager_initialized:
            return True
        
        print("正在初始化GPIO统一管理系统...")
        
        # 初始化GPIO管理器 - 使用BOARD模式与HX711保持一致
        if not init_gpio(GPIO.BOARD):
            print("GPIO管理器初始化失败")
            return False
        
        self.gpio_manager_initialized = True
        print("GPIO统一管理系统初始化成功")
        
        # 显示GPIO状态
        status = gpio_manager.get_status()
        print(f"GPIO模式: {status['mode']}")
        print(f"GPIO可用性: {status['gpio_available']}")
        
        return True

def main():
    """主程序"""
    print("=" * 50)
    print("    HX711 + LCD1602 称重显示系统")
    print("    带重量监控、音乐提醒和人脸检测LED警报功能")
    print("=" * 50)
    
    # 初始化重量监控器
    monitor = WeightMonitor()
    
    # 显示配置信息
    print(f"标准重量: {monitor.config['standard_weight']}g")
    print(f"误差范围: ±{monitor.config['weight_tolerance']}g")
    print(f"检测时间: {monitor.config['check_timeout']}秒")
    print(f"音乐功能: {'启用' if monitor.config['enable_music'] else '禁用'}")
    print(f"人脸检测: {'启用' if monitor.config['enable_face_detection'] else '禁用'}")
    print(f"蜂鸣器引脚: GPIO{monitor.config['buzzer_pin']} (BCM)")
    print(f"LED引脚: GPIO{monitor.config.get('led_pin', 19)} (BCM)")
    print(f"摄像头索引: {monitor.config['camera_index']}")
    
    # 初始化硬件
    try:
        print("\n正在初始化硬件...")
        
        # 1. 首先初始化GPIO统一管理系统
        if not monitor.init_gpio_system():
            print("GPIO系统初始化失败，程序退出")
            return
        
        # 2. 初始化其他硬件（它们会使用GPIO管理器）
        lcd = LCD1602_I2C()
        scale = HX711()
        
        # 3. 等待其他硬件稳定后再初始化LED
        print("等待硬件稳定...")
        time.sleep(1)
        
        # 4. 初始化LED
        print("正在初始化LED...")
        monitor.setup_led()
        
        # 如果LED初始化失败，提供更多选项
        if not monitor.led_initialized:
            print("\nLED初始化失败！")
            print("选项:")
            print("1. 继续运行程序（不使用LED功能）")
            print("2. 查看GPIO状态诊断")
            print("3. 退出程序")
            
            choice = input("请选择 (1/2/3): ").strip()
            
            if choice == "2":
                # 显示GPIO状态诊断
                print("\nGPIO状态诊断:")
                status = gpio_manager.get_status()
                print(f"GPIO管理器状态: {status}")
                
                # 检查可用引脚
                available_pins = gpio_manager.find_available_pins(count=5)
                print(f"可用引脚: {available_pins}")
                
                choice = input("是否继续运行程序？(y/n): ")
                if choice.lower() not in ['y', 'yes']:
                    return
            elif choice == "3":
                print("程序退出")
                return
            # choice == "1" 继续运行
        
        # 5. 初始化摄像头
        camera_initialized = monitor.init_camera()
        
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
        # 启动人脸检测
        if camera_initialized:
            monitor.start_face_detection()
        
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
            # 处理LED队列（在主线程中）- 放在循环开始处理
            monitor.process_beep_queue()
            
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
                # 第二行：最大值 + 时间 + 音乐状态 + 人脸检测状态
                max_str = format_weight(max_weight, unit)
                music_indicator = "♪" if monitor.music_playing else " "
                face_indicator = "👁" if monitor.face_detection_active else " "
                line2 = f"Max:{max_str:>5s}{music_indicator}{face_indicator}{current_time_str}"
                
                lcd.clear()
                lcd.print(line1, 0, 0)
                lcd.print(line2, 1, 0)
            
            # 控制台输出
            stability_text = "稳定" if stable_count >= 3 else "变化"
            music_status = " [音乐播放中]" if monitor.music_playing else ""
            face_status = " [人脸检测中]" if monitor.face_detection_active else ""
            print(f"重量: {weight:8.2f}g ({stability_text}){music_status}{face_status}", end='\r')
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n\n测量已停止")
        monitor.stop_music()
        monitor.cleanup_camera()
        monitor.cleanup_led()
        lcd.clear()
        lcd.print("Measurement", 0, 0)
        lcd.print("Stopped", 1, 0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        monitor.stop_music()
        monitor.cleanup_camera()
        monitor.cleanup_led()
        lcd.clear()
        lcd.print("Error!", 0, 0)
        lcd.print(str(e)[:16], 1, 0)
    finally:
        print("正在清理资源...")
        monitor.stop_music()
        monitor.cleanup_camera()
        monitor.cleanup_led()
        
        # 清理HX711
        try:
            scale.cleanup()
        except:
            pass
        
        # 最后清理GPIO管理器（可选）
        # gpio_manager.cleanup_all()  # 如果需要完全重置GPIO
        
        time.sleep(0.5)  # 给清理一点时间
        print("程序已退出")


if __name__ == "__main__":
    main()
