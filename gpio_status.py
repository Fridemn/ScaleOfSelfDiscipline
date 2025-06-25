"""
GPIO状态检查工具
检查当前GPIO的使用情况和状态
"""

import os
import sys

def check_gpio_status():
    """检查GPIO状态"""
    print("=" * 50)
    print("GPIO状态检查")
    print("=" * 50)
    
    # 检查权限
    if os.geteuid() != 0:
        print("警告: 需要sudo权限才能访问GPIO")
        print("请使用: sudo python gpio_status.py")
    
    try:
        import RPi.GPIO as GPIO
        print("✓ GPIO模块可用")
        
        # 检查GPIO模式
        try:
            mode = GPIO.getmode()
            if mode == GPIO.BCM:
                print("GPIO模式: BCM")
            elif mode == GPIO.BOARD:
                print("GPIO模式: BOARD")
            elif mode is None:
                print("GPIO模式: 未设置")
            else:
                print(f"GPIO模式: {mode}")
        except Exception as e:
            print(f"无法获取GPIO模式: {e}")
        
        # 检查特定引脚状态
        pins_to_check = [18, 19, 2, 3, 5, 6]
        print(f"\n检查引脚状态 (BCM编号):")
        
        for pin in pins_to_check:
            try:
                # 这里可能会出错，因为引脚可能未设置
                function = GPIO.gpio_function(pin)
                print(f"  GPIO{pin}: {function}")
            except Exception as e:
                print(f"  GPIO{pin}: 无法读取 ({e})")
    
    except ImportError:
        print("✗ GPIO模块不可用")
    
    # 检查系统GPIO状态
    print(f"\n系统GPIO状态:")
    try:
        # 读取 /sys/class/gpio/export 状态
        if os.path.exists("/sys/class/gpio"):
            exported_gpios = []
            for item in os.listdir("/sys/class/gpio"):
                if item.startswith("gpio"):
                    exported_gpios.append(item)
            
            if exported_gpios:
                print(f"已导出的GPIO: {', '.join(exported_gpios)}")
            else:
                print("没有已导出的GPIO")
        else:
            print("/sys/class/gpio 不存在")
    except Exception as e:
        print(f"无法读取系统GPIO状态: {e}")

def check_processes():
    """检查可能使用GPIO的进程"""
    print(f"\n检查GPIO相关进程:")
    
    import subprocess
    try:
        # 查找可能使用GPIO的进程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        gpio_processes = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['gpio', 'rpigpio', 'pigpio', 'wiringpi']):
                gpio_processes.append(line)
        
        if gpio_processes:
            print("发现GPIO相关进程:")
            for proc in gpio_processes:
                print(f"  {proc}")
        else:
            print("没有发现GPIO相关进程")
            
    except Exception as e:
        print(f"无法检查进程: {e}")

def main():
    check_gpio_status()
    check_processes()
    
    print(f"\n建议:")
    print("1. 如果有其他进程使用GPIO，先停止它们")
    print("2. 运行 'sudo python simple_led_test.py' 进行纯LED测试")
    print("3. 确保硬件连接正确")

if __name__ == "__main__":
    main()
