#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO管理器测试脚本
验证统一GPIO管理功能
"""

import time
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gpio_manager import gpio_manager, init_gpio, allocate_pin, release_pin, output, input_pin, GPIO_AVAILABLE, GPIO

def test_gpio_manager():
    """测试GPIO管理器功能"""
    print("=" * 50)
    print("GPIO管理器功能测试")
    print("=" * 50)
    
    # 1. 测试GPIO初始化
    print("\n1. 测试GPIO初始化...")
    if init_gpio(GPIO.BOARD):
        print("✓ GPIO初始化成功")
    else:
        print("✗ GPIO初始化失败")
        return False
    
    # 2. 显示GPIO状态
    print("\n2. GPIO管理器状态:")
    status = gpio_manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # 3. 测试引脚分配
    print("\n3. 测试引脚分配...")
    test_pins = [11, 12, 13, 15, 16]  # BOARD引脚号
    allocated_pins = []
    
    for pin in test_pins:
        if allocate_pin(pin, "test_module", GPIO.OUT):
            print(f"✓ 引脚{pin}分配成功")
            allocated_pins.append(pin)
        else:
            print(f"✗ 引脚{pin}分配失败")
    
    # 4. 测试重复分配（应该失败）
    print("\n4. 测试重复分配...")
    if allocated_pins:
        pin = allocated_pins[0]
        if allocate_pin(pin, "another_module", GPIO.OUT):
            print(f"✗ 引脚{pin}重复分配成功（这不应该发生）")
        else:
            print(f"✓ 引脚{pin}重复分配被正确拒绝")
    
    # 5. 测试GPIO输出（如果有LED连接）
    print("\n5. 测试GPIO输出...")
    if allocated_pins:
        test_pin = allocated_pins[0]
        print(f"测试引脚{test_pin}的输出功能...")
        
        for i in range(3):
            print(f"  设置引脚{test_pin}为HIGH")
            output(test_pin, GPIO.HIGH)
            state = input_pin(test_pin)
            print(f"  读取状态: {'HIGH' if state else 'LOW'}")
            time.sleep(0.5)
            
            print(f"  设置引脚{test_pin}为LOW")
            output(test_pin, GPIO.LOW)
            state = input_pin(test_pin)
            print(f"  读取状态: {'HIGH' if state else 'LOW'}")
            time.sleep(0.5)
        
        print("✓ GPIO输出测试完成")
    
    # 6. 测试可用引脚查找
    print("\n6. 测试可用引脚查找...")
    available_pins = gpio_manager.find_available_pins(count=3)
    print(f"找到可用引脚: {available_pins}")
    
    # 7. 测试引脚释放
    print("\n7. 测试引脚释放...")
    for pin in allocated_pins:
        release_pin(pin, "test_module")
        print(f"✓ 引脚{pin}已释放")
    
    # 8. 最终状态检查
    print("\n8. 最终GPIO状态:")
    status = gpio_manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✓ GPIO管理器测试完成")
    return True

def test_pin_conversion():
    """测试引脚转换功能"""
    print("\n" + "=" * 50)
    print("引脚转换功能测试")
    print("=" * 50)
    
    # 测试一些常用的引脚转换
    test_conversions = [
        (17, GPIO.BCM, GPIO.BOARD),  # GPIO17 -> 引脚11
        (18, GPIO.BCM, GPIO.BOARD),  # GPIO18 -> 引脚12
        (19, GPIO.BCM, GPIO.BOARD),  # GPIO19 -> 引脚35
        (11, GPIO.BOARD, GPIO.BCM),  # 引脚11 -> GPIO17
        (12, GPIO.BOARD, GPIO.BCM),  # 引脚12 -> GPIO18
    ]
    
    for pin, from_mode, to_mode in test_conversions:
        converted = gpio_manager.convert_pin(pin, from_mode, to_mode)
        mode_names = {GPIO.BCM: "BCM", GPIO.BOARD: "BOARD"}
        from_name = mode_names.get(from_mode, str(from_mode))
        to_name = mode_names.get(to_mode, str(to_mode))
        print(f"{from_name} {pin} -> {to_name} {converted}")

def main():
    """主函数"""
    print("GPIO管理器测试程序")
    
    if not GPIO_AVAILABLE:
        print("警告: GPIO模块不可用，将进行模拟测试")
    
    try:
        # 测试基本功能
        if test_gpio_manager():
            print("\n所有测试通过！")
        else:
            print("\n测试失败！")
        
        # 测试引脚转换
        test_pin_conversion()
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
    finally:
        # 清理
        print("\n正在清理资源...")
        try:
            gpio_manager.cleanup_all()
        except:
            pass
        print("清理完成")

if __name__ == "__main__":
    main()
