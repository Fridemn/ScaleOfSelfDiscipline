#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO管理器功能测试脚本
测试GPIO统一管理、LED控制和音乐播放功能
"""

import time
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gpio_manager import gpio_manager, init_gpio, allocate_pin, release_pin, output, input_pin, GPIO, GPIO_AVAILABLE
    from main import WeightMonitor
    print("✓ 成功导入模块")
except ImportError as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

def test_gpio_manager():
    """测试GPIO管理器基本功能"""
    print("\n" + "=" * 50)
    print("测试GPIO管理器基本功能")
    print("=" * 50)
    
    # 测试初始化
    print("1. 测试GPIO初始化...")
    if init_gpio(GPIO.BOARD):
        print("✓ GPIO管理器初始化成功")
    else:
        print("✗ GPIO管理器初始化失败")
        return False
    
    # 显示状态
    status = gpio_manager.get_status()
    print(f"GPIO状态: {status}")
    
    # 测试引脚分配
    print("\n2. 测试引脚分配...")
    test_pin = 15  # BOARD引脚15
    if allocate_pin(test_pin, "test", GPIO.OUT):
        print(f"✓ 引脚{test_pin}分配成功")
        
        # 测试输出
        print("3. 测试GPIO输出...")
        if output(test_pin, GPIO.HIGH):
            print("✓ HIGH输出成功")
            time.sleep(0.5)
            
        if output(test_pin, GPIO.LOW):
            print("✓ LOW输出成功")
            time.sleep(0.5)
        
        # 释放引脚
        release_pin(test_pin, "test")
        print(f"✓ 引脚{test_pin}释放成功")
        
    else:
        print(f"✗ 引脚{test_pin}分配失败")
    
    return True

def test_weight_monitor():
    """测试重量监控器功能"""
    print("\n" + "=" * 50)
    print("测试重量监控器功能")
    print("=" * 50)
    
    try:
        monitor = WeightMonitor()
        print("✓ WeightMonitor创建成功")
        
        # 测试GPIO系统初始化
        print("1. 测试GPIO系统初始化...")
        if monitor.init_gpio_system():
            print("✓ GPIO系统初始化成功")
        else:
            print("✗ GPIO系统初始化失败")
            return False
        
        # 测试LED初始化
        print("2. 测试LED初始化...")
        monitor.setup_led()
        if monitor.led_initialized:
            print(f"✓ LED初始化成功 (引脚{monitor.led_pin})")
            
            # 测试LED功能
            print("3. 测试LED功能...")
            print("LED将闪烁3次...")
            monitor.led_alert(3)
            print("✓ LED测试完成")
        else:
            print("✗ LED初始化失败")
        
        # 测试智能音乐控制
        print("4. 测试智能音乐控制...")
        
        # 模拟重量不足
        print("模拟重量不足情况...")
        weight_sufficient = monitor.smart_music_control(150, 200, 10)
        print(f"重量状态: {'足够' if weight_sufficient else '不足'}")
        
        time.sleep(1)
        
        # 模拟重量达标
        print("模拟重量达标情况...")
        weight_sufficient = monitor.smart_music_control(200, 200, 10)
        print(f"重量状态: {'足够' if weight_sufficient else '不足'}")
        
        # 测试状态信息
        sufficient, status_text, icon = monitor.get_weight_status_info(180, 200, 10)
        print(f"状态信息: {status_text} {icon}")
        
        # 清理
        monitor.cleanup_led()
        print("✓ 资源清理完成")
        
        return True
        
    except Exception as e:
        print(f"✗ WeightMonitor测试失败: {e}")
        return False

def test_pin_availability():
    """测试可用引脚查找"""
    print("\n" + "=" * 50)
    print("测试可用引脚查找")
    print("=" * 50)
    
    if not gpio_manager.gpio_initialized:
        if not init_gpio(GPIO.BOARD):
            print("✗ GPIO未初始化")
            return False
    
    print("查找可用引脚...")
    available_pins = gpio_manager.find_available_pins(count=5)
    print(f"找到可用引脚: {available_pins}")
    
    if available_pins:
        print("✓ 成功找到可用引脚")
        
        # 测试第一个可用引脚
        test_pin = available_pins[0]
        print(f"测试引脚{test_pin}...")
        
        if gpio_manager.test_pin(test_pin):
            print(f"✓ 引脚{test_pin}测试通过")
        else:
            print(f"✗ 引脚{test_pin}测试失败")
    else:
        print("✗ 未找到可用引脚")
    
    return len(available_pins) > 0

def main():
    """主测试函数"""
    print("GPIO管理器和重量监控器功能测试")
    print("=" * 60)
    
    # 显示系统信息
    print(f"GPIO可用性: {GPIO_AVAILABLE}")
    if not GPIO_AVAILABLE:
        print("注意: 在模拟模式下运行")
    
    tests = [
        ("GPIO管理器基本功能", test_gpio_manager),
        ("可用引脚查找", test_pin_availability),
        ("重量监控器功能", test_weight_monitor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n正在运行: {test_name}")
        try:
            if test_func():
                print(f"✓ {test_name} - 通过")
                passed += 1
            else:
                print(f"✗ {test_name} - 失败")
        except Exception as e:
            print(f"✗ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！GPIO管理器工作正常。")
    else:
        print("⚠️  部分测试失败，请检查硬件连接或配置。")
    
    # 最终清理
    try:
        gpio_manager.cleanup_all()
        print("✓ 最终资源清理完成")
    except:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        try:
            gpio_manager.cleanup_all()
        except:
            pass
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        try:
            gpio_manager.cleanup_all()
        except:
            pass
