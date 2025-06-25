"""
简化LED测试程序
只测试LED功能，不涉及其他硬件
用于排除GPIO冲突问题
"""

import time
import sys
import os

# 检查权限
if os.geteuid() != 0:
    print("请使用sudo权限运行此脚本: sudo python simple_led_test.py")
    sys.exit(1)

# 导入GPIO
try:
    import RPi.GPIO as GPIO
    print("✓ GPIO模块导入成功")
except ImportError:
    print("✗ 无法导入GPIO模块")
    sys.exit(1)

def test_led_only():
    """纯LED测试，不涉及任何其他硬件"""
    led_pin = 19
    
    try:
        print("=" * 50)
        print("简化LED测试 - 只测试LED功能")
        print("=" * 50)
        
        # 完全清理之前的GPIO设置
        GPIO.cleanup()
        print("GPIO已清理")
        
        # 设置GPIO模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        print("GPIO模式设置为BCM")
        
        # 设置LED引脚
        GPIO.setup(led_pin, GPIO.OUT)
        print(f"GPIO{led_pin}设置为输出模式")
        
        # 确保LED初始状态为关闭
        GPIO.output(led_pin, GPIO.LOW)
        initial_state = GPIO.input(led_pin)
        print(f"LED初始状态: {'HIGH' if initial_state else 'LOW'}")
        
        # 测试1: 基本开关测试
        print("\n测试1: 基本开关测试")
        print("点亮LED 3秒...")
        GPIO.output(led_pin, GPIO.HIGH)
        state_on = GPIO.input(led_pin)
        print(f"设置HIGH后状态: {'HIGH' if state_on else 'LOW'}")
        
        if state_on:
            print("✓ GPIO设置HIGH成功")
        else:
            print("✗ GPIO设置HIGH失败")
        
        time.sleep(3)
        
        print("关闭LED...")
        GPIO.output(led_pin, GPIO.LOW)
        state_off = GPIO.input(led_pin)
        print(f"设置LOW后状态: {'HIGH' if state_off else 'LOW'}")
        
        if not state_off:
            print("✓ GPIO设置LOW成功")
        else:
            print("✗ GPIO设置LOW失败")
        
        time.sleep(1)
        
        # 测试2: 快速闪烁测试
        print("\n测试2: 快速闪烁测试 (10次)")
        for i in range(10):
            print(f"闪烁 {i+1}/10", end=" ")
            GPIO.output(led_pin, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(led_pin, GPIO.LOW)
            time.sleep(0.2)
            print("完成")
        
        # 测试3: 长时间点亮测试
        print("\n测试3: 长时间点亮测试 (5秒)")
        GPIO.output(led_pin, GPIO.HIGH)
        for i in range(5):
            print(f"剩余 {5-i} 秒...")
            time.sleep(1)
        GPIO.output(led_pin, GPIO.LOW)
        
        # 测试4: 交互式测试
        print("\n测试4: 交互式测试")
        print("您可以手动控制LED")
        
        while True:
            cmd = input("输入命令 (on/off/quit): ").strip().lower()
            
            if cmd == 'on':
                GPIO.output(led_pin, GPIO.HIGH)
                state = GPIO.input(led_pin)
                print(f"LED点亮 - 状态: {'HIGH' if state else 'LOW'}")
                
            elif cmd == 'off':
                GPIO.output(led_pin, GPIO.LOW)
                state = GPIO.input(led_pin)
                print(f"LED关闭 - 状态: {'HIGH' if state else 'LOW'}")
                
            elif cmd == 'quit':
                break
                
            else:
                print("无效命令，请输入: on/off/quit")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试出错: {e}")
    
    finally:
        # 确保LED关闭并清理GPIO
        try:
            GPIO.output(led_pin, GPIO.LOW)
            GPIO.cleanup()
            print("GPIO已清理，LED已关闭")
        except:
            pass

def check_gpio_conflicts():
    """检查可能的GPIO冲突"""
    print("\n" + "=" * 50)
    print("GPIO冲突检查")
    print("=" * 50)
    
    # 常用的GPIO引脚和可能的用途
    gpio_usage = {
        18: "蜂鸣器 (BCM)",
        19: "LED (BCM)",
        2: "I2C SDA (LCD)",
        3: "I2C SCL (LCD)",
        5: "HX711 DT",
        6: "HX711 SCK"
    }
    
    print("当前项目GPIO使用情况:")
    for pin, usage in gpio_usage.items():
        print(f"  GPIO{pin}: {usage}")
    
    print("\n可能的冲突:")
    print("1. 如果多个模块同时使用GPIO，可能导致冲突")
    print("2. HX711模块可能已经初始化了GPIO模式")
    print("3. 某些模块可能没有正确清理GPIO")
    
    print("\n建议:")
    print("1. 单独测试每个硬件模块")
    print("2. 确保模块正确清理GPIO资源")
    print("3. 检查硬件连接是否正确")

def main():
    print("简化LED测试程序")
    print("此程序只测试LED，不涉及其他硬件")
    
    # 检查GPIO冲突
    check_gpio_conflicts()
    
    # 确认开始测试
    response = input("\n是否开始LED测试? (y/n): ").strip().lower()
    if response not in ['y', 'yes', '是']:
        print("测试取消")
        return
    
    # 开始测试
    test_led_only()

if __name__ == "__main__":
    main()
