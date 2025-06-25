# GPIO统一管理和智能重量监控改进

## 改进概述

本次改进主要解决了多个模块之间的GPIO冲突问题，并实现了智能的重量监控和音乐播放控制。

## 主要改进内容

### 1. GPIO统一管理器 (`gpio_manager.py`)

**功能特点:**
- 单例模式，确保全局唯一的GPIO管理器
- 统一的GPIO初始化和引脚分配机制
- 防止模块间引脚冲突
- 支持BCM和BOARD模式的引脚转换
- 自动查找可用引脚
- 模拟GPIO支持（用于开发测试）

**核心方法:**
- `init_gpio(mode)`: 初始化GPIO系统
- `allocate_pin(pin, module_name, pin_mode)`: 分配引脚给模块
- `release_pin(pin, module_name)`: 释放引脚
- `output(pin, value)`: 安全的GPIO输出
- `input(pin)`: 安全的GPIO输入
- `find_available_pins(count)`: 查找可用引脚

### 2. 智能重量监控 (`main.py`)

**改进的播放逻辑:**
- ✅ 不再只是开始10秒后播放音乐
- ✅ 持续监控重量状态
- ✅ 重量不足时自动播放音乐
- ✅ 重量达标时自动停止音乐
- ✅ 避免频繁切换的稳定性算法

**智能控制特点:**
- 状态稳定性检测（避免重量波动导致音乐频繁开关）
- 可配置的启动/停止延迟时间
- 详细的重量状态显示
- 实时的控制台和LCD反馈

### 3. 配置增强

**新增配置项:**
```json
{
    "weight_check_interval": 2.0,     // 重量检查间隔（秒）
    "music_start_delay": 3.0,         // 重量不足后音乐启动延迟（秒）
    "music_stop_delay": 1.0,          // 重量达标后音乐停止延迟（秒）
    "stable_threshold": 1.0,          // 重量稳定阈值（克）
    "smart_monitoring": true          // 启用智能监控模式
}
```

## 使用方法

### 基本使用

```python
# 1. 导入GPIO管理器
from gpio_manager import init_gpio, allocate_pin, output, GPIO

# 2. 初始化GPIO系统
init_gpio(GPIO.BOARD)

# 3. 分配引脚
if allocate_pin(15, "my_module", GPIO.OUT):
    # 4. 使用引脚
    output(15, GPIO.HIGH)
```

### 运行主程序

```bash
python main.py
```

新的显示界面将显示：
- 重量状态（达标/不足）
- 音乐播放状态
- 人脸检测状态
- 实时的重量数据

### 测试功能

```bash
python test_gpio_improvements.py
```

## 技术细节

### GPIO初始化流程

1. **统一初始化**: 主程序首先调用`monitor.init_gpio_system()`
2. **硬件模块**: HX711、蜂鸣器等模块通过GPIO管理器申请引脚
3. **LED控制**: LED模块最后初始化，自动寻找可用引脚
4. **冲突检测**: 如果引脚被占用，自动寻找替代引脚

### 智能音乐控制算法

```python
def smart_music_control(self, weight, target_weight, tolerance):
    # 1. 检查重量状态
    weight_is_sufficient = abs(weight - target_weight) <= tolerance
    
    # 2. 维护状态历史（稳定性检测）
    self.weight_status_history.append(weight_is_sufficient)
    
    # 3. 根据稳定状态和延迟配置控制音乐
    if weight_is_sufficient and status_stable:
        # 延迟停止音乐
    elif not weight_is_sufficient and status_stable:
        # 延迟启动音乐
```

## 硬件兼容性

### 支持的GPIO引脚 (BOARD模式)
- **安全引脚**: 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40
- **避开引脚**: I2C (3, 5), SPI (19, 21, 23, 24, 26), UART (8, 10)

### 引脚分配示例
- HX711: 引脚11(SCK), 引脚13(DT)
- 蜂鸣器: 引脚12 (BCM GPIO18)
- LED: 自动分配（如引脚35对应BCM GPIO19）

## 故障排除

### 常见问题

1. **LED初始化失败**
   - 检查硬件连接
   - 查看GPIO状态诊断信息
   - 尝试不同的引脚

2. **GPIO冲突**
   - GPIO管理器会自动检测并报告冲突
   - 检查配置文件中的引脚设置

3. **音乐播放异常**
   - 确保蜂鸣器硬件连接正确
   - 检查引脚配置是否正确

### 调试命令

```bash
# 运行测试脚本
python test_gpio_improvements.py

# 查看GPIO状态
python -c "from gpio_manager import gpio_manager; print(gpio_manager.get_status())"
```

## 开发测试

在没有树莓派硬件的环境中，系统会自动切换到模拟模式：
- GPIO操作会在控制台显示模拟输出
- 所有功能逻辑保持不变
- 便于开发和调试

## 未来改进计划

1. **Web界面**: 添加基于Web的监控界面
2. **数据记录**: 保存重量历史数据
3. **多设备支持**: 支持多个称重设备
4. **高级报警**: 添加邮件/短信通知功能

## 文件结构

```
├── main.py                      # 主程序（已改进）
├── gpio_manager.py              # GPIO统一管理器（新增）
├── hx711.py                     # HX711模块（已更新）
├── beep.py                      # 蜂鸣器模块（已更新）
├── test_gpio_improvements.py    # 功能测试脚本（新增）
├── lcd_display.py              # LCD显示模块
├── camera.py                   # 摄像头模块
└── hx711_calibration.json      # 配置文件（已扩展）
```

---

**改进完成日期**: 2025年6月25日  
**版本**: v2.0  
**作者**: AI Assistant
