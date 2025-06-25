#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派Bad Apple蜂鸣器播放程序


硬件连接:
- 蜂鸣器正极 -> 3.3V
- 蜂鸣器负极 -> 三极管(S9012)发射极
- 三极管基极 -> 1K电阻 -> GPIO18 (BCM) = 物理引脚12
- 三极管集电极 -> GND

"""

import RPi.GPIO as GPIO
import time
import signal
import sys

# GPIO设置 - 使用BOARD模式与HX711保持一致
BEEP_PIN_BCM = 18  # BCM编号
BEEP_PIN_BOARD = 12  # 对应的物理引脚号

# 音符频率定义
NOTE_B0 = 31
NOTE_C1 = 33
NOTE_CS1 = 35
NOTE_D1 = 37
NOTE_DS1 = 39
NOTE_E1 = 41
NOTE_F1 = 44
NOTE_FS1 = 46
NOTE_G1 = 49
NOTE_GS1 = 52
NOTE_A1 = 55
NOTE_AS1 = 58
NOTE_B1 = 62
NOTE_C2 = 65
NOTE_CS2 = 69
NOTE_D2 = 73
NOTE_DS2 = 78
NOTE_E2 = 82
NOTE_F2 = 87
NOTE_FS2 = 93
NOTE_G2 = 98
NOTE_GS2 = 104
NOTE_A2 = 110
NOTE_AS2 = 117
NOTE_B2 = 123
NOTE_C3 = 131
NOTE_CS3 = 139
NOTE_D3 = 147
NOTE_DS3 = 156
NOTE_E3 = 165
NOTE_F3 = 175
NOTE_FS3 = 185
NOTE_G3 = 196
NOTE_GS3 = 208
NOTE_A3 = 220
NOTE_AS3 = 233
NOTE_B3 = 247
NOTE_C4 = 262
NOTE_CS4 = 277
NOTE_D4 = 294
NOTE_DS4 = 311
NOTE_E4 = 330
NOTE_F4 = 349
NOTE_FS4 = 370
NOTE_G4 = 392
NOTE_GS4 = 415
NOTE_A4 = 440
NOTE_AS4 = 466
NOTE_B4 = 494
NOTE_C5 = 523
NOTE_CS5 = 554
NOTE_D5 = 587
NOTE_DS5 = 622
NOTE_E5 = 659
NOTE_F5 = 698
NOTE_FS5 = 740
NOTE_G5 = 784
NOTE_GS5 = 831
NOTE_A5 = 880
NOTE_AS5 = 932
NOTE_B5 = 988
NOTE_C6 = 1047
NOTE_CS6 = 1109
NOTE_D6 = 1175
NOTE_DS6 = 1245
NOTE_E6 = 1319
NOTE_F6 = 1397
NOTE_FS6 = 1480
NOTE_G6 = 1568
NOTE_GS6 = 1661
NOTE_A6 = 1760
NOTE_AS6 = 1865
NOTE_B6 = 1976
NOTE_C7 = 2093
NOTE_CS7 = 2217
NOTE_D7 = 2349
NOTE_DS7 = 2489
NOTE_E7 = 2637
NOTE_F7 = 2794
NOTE_FS7 = 2960
NOTE_G7 = 3136
NOTE_GS7 = 3322
NOTE_A7 = 3520
NOTE_AS7 = 3729
NOTE_B7 = 3951
NOTE_C8 = 4186
NOTE_CS8 = 4435
NOTE_D8 = 4699
NOTE_DS8 = 4978

class BadAppleBuzzer:
    def __init__(self, beep_pin=18):
        # 将BCM引脚号转换为BOARD引脚号
        self.beep_pin_bcm = beep_pin
        if beep_pin == 18:
            self.beep_pin = 12  # GPIO18对应物理引脚12
        else:
            # 简单的BCM到BOARD转换（仅支持常用引脚）
            bcm_to_board = {
                2: 3, 3: 5, 4: 7, 17: 11, 27: 13, 22: 15,
                10: 19, 9: 21, 11: 23, 5: 29, 6: 31,
                13: 33, 19: 35, 26: 37, 14: 8, 15: 10,
                18: 12, 23: 16, 24: 18, 25: 22, 8: 24,
                7: 26, 12: 32, 16: 36, 20: 38, 21: 40
            }
            self.beep_pin = bcm_to_board.get(beep_pin, 12)
        
        self.stop_playing = False  # 添加停止标志
        self.gpio_initialized = False
        self.setup_gpio()
        signal.signal(signal.SIGINT, self.cleanup_and_exit)
        
    def setup_gpio(self):
        """初始化GPIO设置"""
        try:
            # 检查GPIO模式是否已设置
            try:
                # 尝试获取当前模式
                current_mode = GPIO.getmode()
                if current_mode is None:
                    # 如果没有设置模式，使用BOARD模式
                    GPIO.setmode(GPIO.BOARD)
                elif current_mode != GPIO.BOARD:
                    print(f"警告: GPIO已设置为模式 {current_mode}，将使用现有模式")
                    # 如果是BCM模式，使用BCM引脚号
                    if current_mode == GPIO.BCM:
                        self.beep_pin = self.beep_pin_bcm
            except:
                # 如果获取模式失败，尝试设置BOARD模式
                GPIO.setmode(GPIO.BOARD)
            
            # 设置引脚
            GPIO.setup(self.beep_pin, GPIO.OUT)
            GPIO.output(self.beep_pin, GPIO.LOW)
            self.gpio_initialized = True
            print(f"GPIO初始化完成，蜂鸣器引脚: {self.beep_pin} (BCM: {self.beep_pin_bcm})")
            
        except Exception as e:
            print(f"GPIO初始化失败: {e}")
            # 尝试清理并重新初始化
            try:
                GPIO.cleanup()
                time.sleep(0.1)
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.beep_pin, GPIO.OUT)
                GPIO.output(self.beep_pin, GPIO.LOW)
                self.gpio_initialized = True
                print("GPIO重新初始化成功")
            except Exception as e2:
                print(f"GPIO重新初始化也失败: {e2}")
                self.gpio_initialized = False
                raise
        
    def tone(self, frequency, duration):
        """
        产生指定频率和时长的音调
        :param frequency: 频率(Hz)，0表示静音
        :param duration: 持续时间(毫秒)
        """
        if not self.gpio_initialized:
            return
            
        if frequency == 0:
            # 静音
            time.sleep(duration / 1000.0)
            return
            
        # 计算半周期时间
        period = 1.0 / frequency
        half_period = period / 2.0
        
        # 计算需要的周期数
        cycles = int((duration / 1000.0) * frequency)
        
        try:
            for _ in range(cycles):
                if self.stop_playing:
                    break
                GPIO.output(self.beep_pin, GPIO.HIGH)
                time.sleep(half_period)
                GPIO.output(self.beep_pin, GPIO.LOW)
                time.sleep(half_period)
        except Exception as e:
            print(f"蜂鸣器输出错误: {e}")
    
    def play_melody(self):
        """播放Bad Apple完整旋律"""
        print("开始播放Bad Apple旋律...")
        print("按Ctrl+C停止播放")
        
        bpm = 137
        # 12000 = 60 * 1000 * 4 * 0.8 / 16 quarter note = one beat
        ndms = 12000
        
        # Bad Apple旋律数据 - 完整版本
        melody = [
            # # Intro
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
             NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2, NOTE_DS2,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
             NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, NOTE_DS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_GS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_GS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_DS3, NOTE_FS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, NOTE_DS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_GS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_GS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_DS3, NOTE_FS3,
            
            # Verse 1 - 16
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_F4, NOTE_DS4, NOTE_D4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_F4, NOTE_DS4, NOTE_D4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4,
            
            # Verse 17 - 32
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_F5,
            NOTE_FS5, NOTE_F5, NOTE_DS5, NOTE_CS5, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            
            # Verse 33 - 48
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_F5,
            NOTE_FS5, NOTE_F5, NOTE_DS5, NOTE_CS5, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, 0,
            
            # Interlude
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, NOTE_DS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_GS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_GS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_DS3, NOTE_FS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, NOTE_DS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_GS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3,
            NOTE_DS3, 0, NOTE_DS3, NOTE_CS3, NOTE_DS3, NOTE_GS3, NOTE_FS3, NOTE_GS3, NOTE_FS3, NOTE_DS3, NOTE_FS3,
            
            # Verse(2) 1 - 16 (重复第一段)
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_F4, NOTE_DS4, NOTE_D4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_F4, NOTE_DS4, NOTE_D4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_CS5,
            NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_GS4, NOTE_FS4, NOTE_F4,
            NOTE_DS4, NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_FS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4,
            
            # Verse(2) 17 - 32 (重复)
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_CS4, NOTE_DS4,
            NOTE_F4, NOTE_FS4, NOTE_GS4, NOTE_AS4, NOTE_DS4, NOTE_AS4, NOTE_CS5,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_CS5, NOTE_DS5, NOTE_AS4, NOTE_GS4, NOTE_AS4, NOTE_DS5, NOTE_F5,
            NOTE_FS5, NOTE_F5, NOTE_DS5, NOTE_CS5, NOTE_AS4, NOTE_GS4, NOTE_AS4,
            NOTE_GS4, NOTE_FS4, NOTE_F4, NOTE_CS4, NOTE_DS4, NOTE_B4, NOTE_D5,
            
            # Verse(2) 33 - 48 转调到G大调
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_A4, NOTE_G4, NOTE_FS4, NOTE_D4, NOTE_E4, NOTE_D4, NOTE_E4,
            NOTE_FS4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_E4, NOTE_B4, NOTE_D5,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_A4, NOTE_G4, NOTE_FS4, NOTE_D4, NOTE_E4, NOTE_D4, NOTE_E4,
            NOTE_FS4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_E4, NOTE_B4, NOTE_D5,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_A4, NOTE_G4, NOTE_FS4, NOTE_D4, NOTE_E4, NOTE_D4, NOTE_E4,
            NOTE_FS4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_E4, NOTE_B4, NOTE_D5,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_D5, NOTE_E5, NOTE_B4, NOTE_A4, NOTE_B4, NOTE_E5, NOTE_FS5,
            NOTE_G5, NOTE_FS5, NOTE_E5, NOTE_D5, NOTE_B4, NOTE_A4, NOTE_B4,
            NOTE_A4, NOTE_G4, NOTE_FS4, NOTE_D4, NOTE_E4, 0,
            
            # Outro
            NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4,
            NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4,
            NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4,
            NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, NOTE_E4, 0,
            0
        ]
        
        # 音符时长数据：单位为1/16音符，时间 = 数字 * (1/16)
        note_durations = [
            # # Intro
            4, 4, 4, 1, 1, 1, 1,
            4, 4, 4, 2, 2,
            4, 4, 4, 1, 1, 1, 1,
            4, 4, 4, 2, 2,
            4, 4, 4, 1, 1, 1, 1,
            4, 4, 4, 2, 2,
            4, 4, 4, 1, 1, 1, 1,
            4, 4, 4, 2, 2,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            
            # Verse 1 - 16
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 4, 4,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 4, 4,
            
            # Verse 17 - 32
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            
            # Verse 33 - 48
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 4,
            
            # Interlude
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            4, 1, 1, 1, 1, 4, 1, 1, 1, 1,
            4, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1,
            
            # Verse(2) 1 - 16
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 4, 4,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 2, 2, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            4, 4, 4, 4,
            
            # Verse(2) 17 - 32
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            
            # Verse(2) 33 - 48
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 2, 2,
            2, 2, 2, 2, 4, 4,
            
            # Outro
            3, 3, 2, 3, 3, 2,
            3, 3, 2, 3, 3, 2,
            3, 3, 2, 3, 3, 2,
            3, 3, 2, 3, 3, 2,
            16
        ]
        
        total_notes = len(melody)
        print(f"总共 {total_notes} 个音符")
        
        start_time = time.time()
        
        for i in range(total_notes):
            if self.stop_playing:  # 检查停止标志
                print("\n音乐播放被停止")
                break
                
            try:
                # 计算音符持续时间
                note_duration = ndms * note_durations[i] / bpm
                
                # 播放音符
                self.tone(melody[i], note_duration)
                
                # 音符间的停顿
                pause_between_notes = note_duration / 4
                time.sleep(pause_between_notes / 1000.0)
                
                # 显示进度
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    progress = (i + 1) / total_notes * 100
                    print(f"播放进度: {progress:.1f}% ({i+1}/{total_notes}) - 已播放 {elapsed:.1f}秒")
                    
            except KeyboardInterrupt:
                print("\n播放被用户中断")
                break
            except Exception as e:
                print(f"播放音符 {i} 时出错: {e}")
                continue
        
        if not self.stop_playing:
            print("Bad Apple旋律播放完成！")
    
    def stop(self):
        """停止播放"""
        self.stop_playing = True
    
    def cleanup_and_exit(self, signum, frame):
        """清理GPIO并退出"""
        print("\n\n正在清理GPIO...")
        self.cleanup()
        print("GPIO清理完成，程序退出")
        sys.exit(0)
    
    def cleanup(self):
        """手动清理GPIO"""
        self.stop_playing = True
        if self.gpio_initialized:
            try:
                GPIO.output(self.beep_pin, GPIO.LOW)
                # 注意：不要调用GPIO.cleanup()，因为HX711可能还在使用GPIO
                print("蜂鸣器GPIO已清理")
            except:
                pass

def main():
    """主函数"""
    try:
        # 创建蜂鸣器对象
        buzzer = BadAppleBuzzer(beep_pin=18)
        
        # 播放旋律
        buzzer.play_melody()
        
    except Exception as e:
        print(f"程序运行出错: {e}")
    
    finally:
        # 清理GPIO
        try:
            GPIO.cleanup()
            print("程序结束，GPIO已清理")
        except:
            pass

if __name__ == "__main__":
    main()
