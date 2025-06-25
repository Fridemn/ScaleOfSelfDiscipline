"""
LED测试脚本
用于测试GPIO19引脚的LED控制功能
"""

import time
import sys

# 导入GPIO模块
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("✓ GPIO模块导入成功")
except ImportError:
    GPIO_AVAILABLE = False
    print("✗ 无法导入GPIO模块")
    sys.exit(1)

class LEDTester:
    def __init__(self, led_pin=19):
        self.led_pin = led_pin
        self.gpio_initialized = False
        self.setup_gpio()
    
    def setup_gpio(self):
        """初始化GPIO"""
        try:
            # 清理之前的GPIO设置
            GPIO.cleanup()
            
            # 设置GPIO模式
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 设置LED引脚为输出模式
            GPIO.setup(self.led_pin, GPIO.OUT)
            
            # 初始化LED为关闭状态
            GPIO.output(self.led_pin, GPIO.LOW)
            
            self.gpio_initialized = True
            print(f"✓ GPIO初始化成功，LED引脚: GPIO{self.led_pin}")
            
        except Exception as e:
            print(f"✗ GPIO初始化失败: {e}")
            self.gpio_initialized = False
    
    def test_led_basic(self):
        """基本LED测试 - 点亮/熄灭"""
        if not self.gpio_initialized:
            print("GPIO未初始化，无法测试")
            return False
        
        print("\n=== 基本LED测试 ===")
        try:
            # 点亮LED
            print("点亮LED...")
            GPIO.output(self.led_pin, GPIO.HIGH)
            time.sleep(2)
            
            # 熄灭LED
            print("熄灭LED...")
            GPIO.output(self.led_pin, GPIO.LOW)
            time.sleep(1)
            
            print("✓ 基本LED测试完成")
            return True
            
        except Exception as e:
            print(f"✗ 基本LED测试失败: {e}")
            return False
    
    def test_led_blink(self, count=5, interval=0.5):
        """LED闪烁测试"""
        if not self.gpio_initialized:
            print("GPIO未初始化，无法测试")
            return False
        
        print(f"\n=== LED闪烁测试 (闪烁{count}次) ===")
        try:
            for i in range(count):
                print(f"闪烁 {i+1}/{count}")
                
                # 点亮
                GPIO.output(self.led_pin, GPIO.HIGH)
                time.sleep(interval)
                
                # 熄灭
                GPIO.output(self.led_pin, GPIO.LOW)
                time.sleep(interval)
            
            print("✓ LED闪烁测试完成")
            return True
            
        except Exception as e:
            print(f"✗ LED闪烁测试失败: {e}")
            return False
    
    def test_led_fade(self):
        """LED PWM渐变测试（如果支持）"""
        if not self.gpio_initialized:
            print("GPIO未初始化，无法测试")
            return False
        
        print("\n=== LED PWM渐变测试 ===")
        try:
            # 创建PWM对象
            pwm = GPIO.PWM(self.led_pin, 1000)  # 1000Hz频率
            pwm.start(0)  # 从0%开始
            
            # 渐亮
            print("LED渐亮...")
            for duty_cycle in range(0, 101, 5):
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.1)
            
            # 渐暗
            print("LED渐暗...")
            for duty_cycle in range(100, -1, -5):
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.1)
            
            # 停止PWM
            pwm.stop()
            
            print("✓ LED PWM渐变测试完成")
            return True
            
        except Exception as e:
            print(f"✗ LED PWM渐变测试失败: {e}")
            return False
    
    def test_led_long_on(self, duration=5):
        """LED长时间点亮测试"""
        if not self.gpio_initialized:
            print("GPIO未初始化，无法测试")
            return False
        
        print(f"\n=== LED长时间点亮测试 ({duration}秒) ===")
        try:
            print(f"LED将点亮{duration}秒...")
            GPIO.output(self.led_pin, GPIO.HIGH)
            
            for i in range(duration):
                print(f"剩余时间: {duration-i}秒", end='\r')
                time.sleep(1)
            
            GPIO.output(self.led_pin, GPIO.LOW)
            print("\n✓ LED长时间点亮测试完成")
            return True
            
        except Exception as e:
            print(f"\n✗ LED长时间点亮测试失败: {e}")
            return False
    
    def interactive_test(self):
        """交互式测试"""
        if not self.gpio_initialized:
            print("GPIO未初始化，无法测试")
            return
        
        print("\n=== 交互式LED测试 ===")
        print("输入命令控制LED:")
        print("  on  - 点亮LED")
        print("  off - 熄灭LED")
        print("  quit - 退出测试")
        
        try:
            while True:
                command = input("\n请输入命令: ").strip().lower()
                
                if command == 'on':
                    GPIO.output(self.led_pin, GPIO.HIGH)
                    print("💡 LED已点亮")
                elif command == 'off':
                    GPIO.output(self.led_pin, GPIO.LOW)
                    print("💡 LED已熄灭")
                elif command == 'quit':
                    GPIO.output(self.led_pin, GPIO.LOW)
                    print("退出交互式测试")
                    break
                else:
                    print("无效命令，请输入 on/off/quit")
                    
        except KeyboardInterrupt:
            print("\n用户中断，退出交互式测试")
        except Exception as e:
            print(f"交互式测试出错: {e}")
    
    def check_gpio_status(self):
        """检查GPIO引脚状态"""
        print(f"\n=== GPIO{self.led_pin}引脚状态检查 ===")
        
        if not self.gpio_initialized:
            print("GPIO未初始化")
            return
        
        try:
            # 检查引脚功能
            function = GPIO.gpio_function(self.led_pin)
            print(f"引脚功能: {function}")
            
            # 检查引脚状态
            state = GPIO.input(self.led_pin)
            print(f"当前状态: {'HIGH' if state else 'LOW'}")
            
        except Exception as e:
            print(f"状态检查失败: {e}")
    
    def cleanup(self):
        """清理GPIO资源"""
        if self.gpio_initialized:
            try:
                GPIO.output(self.led_pin, GPIO.LOW)  # 确保LED关闭
                GPIO.cleanup()
                print("GPIO资源已清理")
            except Exception as e:
                print(f"GPIO清理失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("    LED测试程序")
    print("    测试GPIO19引脚LED控制")
    print("=" * 50)
    
    # 检查是否以root权限运行
    import os
    if os.geteuid() != 0:
        print("警告: 建议以root权限运行此脚本 (sudo python test_led.py)")
    
    # 创建LED测试器
    led_tester = LEDTester(led_pin=19)
    
    if not led_tester.gpio_initialized:
        print("LED测试器初始化失败，程序退出")
        return
    
    try:
        while True:
            print("\n" + "=" * 30)
            print("LED测试菜单:")
            print("1. 基本测试 (点亮2秒)")
            print("2. 闪烁测试 (闪烁5次)")
            print("3. PWM渐变测试")
            print("4. 长时间点亮 (5秒)")
            print("5. 交互式测试")
            print("6. 检查GPIO状态")
            print("7. 硬件连接指南")
            print("0. 退出")
            
            choice = input("\n请选择测试项目 (0-7): ").strip()
            
            if choice == '1':
                led_tester.test_led_basic()
            elif choice == '2':
                led_tester.test_led_blink()
            elif choice == '3':
                led_tester.test_led_fade()
            elif choice == '4':
                led_tester.test_led_long_on()
            elif choice == '5':
                led_tester.interactive_test()
            elif choice == '6':
                led_tester.check_gpio_status()
            elif choice == '7':
                print_hardware_guide()
            elif choice == '0':
                break
            else:
                print("无效选择，请重新输入")
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
    finally:
        led_tester.cleanup()
        print("LED测试程序已退出")

def print_hardware_guide():
    """打印硬件连接指南"""
    print("\n" + "=" * 40)
    print("    LED硬件连接指南")
    print("=" * 40)
    print("1. LED连接方式:")
    print("   GPIO19 (引脚35) --- 电阻(220Ω-1kΩ) --- LED长脚(+)")
    print("   GND (引脚39)    ------------------- LED短脚(-)")
    print()
    print("2. 引脚位置 (40针GPIO):")
    print("   GPIO19 位于第35针 (左侧倒数第3个)")
    print("   GND    位于第39针 (左侧倒数第1个)")
    print()
    print("3. LED极性:")
    print("   长脚为正极(阳极)，连接GPIO19")
    print("   短脚为负极(阴极)，连接GND")
    print()
    print("4. 电阻作用:")
    print("   限制电流，保护GPIO和LED")
    print("   推荐使用220Ω-1kΩ电阻")
    print()
    print("5. 故障排除:")
    print("   - 检查接线是否牢固")
    print("   - 确认LED极性正确")
    print("   - 测试LED是否损坏")
    print("   - 检查电阻是否连接")
    print("=" * 40)

if __name__ == "__main__":
    main()
