"""
1602 I2C LCD显示屏驱动模块
"""

import smbus
import time

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

def format_weight(weight, unit="g"):
    """格式化重量显示"""
    if unit == "kg":
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
