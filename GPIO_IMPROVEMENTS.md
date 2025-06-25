# GPIO统一管理改进说明

## 问题描述

原始代码中各个模块（HX711、蜂鸣器、LED等）都独立初始化GPIO，导致以下问题：
1. GPIO模式冲突（有些使用BCM，有些使用BOARD）
2. 引脚分配冲突（多个模块可能使用同一引脚）
3. GPIO清理冲突（一个模块清理GPIO会影响其他模块）
4. 初始化顺序依赖问题

## 解决方案

创建了一个统一的GPIO管理器 (`gpio_manager.py`)，具有以下特性：

### 1. 单例模式管理
- 确保整个程序只有一个GPIO管理器实例
- 避免多个管理器之间的冲突

### 2. 统一的GPIO模式
- 强制使用一致的GPIO模式（BOARD模式）
- 提供BCM和BOARD引脚号的自动转换

### 3. 引脚分配管理
- 记录每个引脚的使用者
- 防止引脚冲突
- 提供引脚使用状态查询

### 4. 安全的资源管理
- 模块化的引脚释放
- 避免全局GPIO清理造成的冲突
- 支持优雅的资源清理

## 修改的文件

### 1. `gpio_manager.py` (新增)
统一的GPIO管理器，提供：
- GPIO初始化管理
- 引脚分配和释放
- 引脚状态查询
- 引脚转换功能
- 模拟GPIO支持

### 2. `main.py` (修改)
- 使用GPIO管理器进行LED控制
- 改进的初始化流程
- 更好的错误处理和诊断

### 3. `hx711.py` (修改)
- 使用GPIO管理器或直接GPIO控制
- 兼容现有的初始化流程
- 改进的资源清理

### 4. `beep.py` (修改)
- 使用GPIO管理器进行蜂鸣器控制
- 保持向后兼容性
- 统一的GPIO输出接口

### 5. `test_gpio_manager.py` (新增)
GPIO管理器的测试脚本，验证：
- GPIO初始化
- 引脚分配和释放
- 输出功能
- 引脚转换

## 使用方法

### 基本用法

```python
from gpio_manager import init_gpio, allocate_pin, release_pin, output, input_pin, GPIO

# 1. 初始化GPIO系统（整个程序只需调用一次）
init_gpio(GPIO.BOARD)

# 2. 分配引脚
if allocate_pin(12, "my_module", GPIO.OUT):
    print("引脚分配成功")

# 3. 使用引脚
output(12, GPIO.HIGH)
state = input_pin(12)

# 4. 释放引脚
release_pin(12, "my_module")
```

### 高级功能

```python
from gpio_manager import gpio_manager

# 查看GPIO状态
status = gpio_manager.get_status()
print(status)

# 查找可用引脚
available_pins = gpio_manager.find_available_pins(count=3)
print(f"可用引脚: {available_pins}")

# 引脚转换
board_pin = gpio_manager.convert_pin(18, GPIO.BCM, GPIO.BOARD)
print(f"BCM 18 对应 BOARD {board_pin}")
```

## 改进效果

### 1. 解决LED启动问题
- 统一的GPIO初始化顺序
- 避免引脚冲突
- 更好的错误诊断

### 2. 提高系统稳定性
- 减少GPIO相关的错误
- 更好的资源管理
- 避免模块间的相互干扰

### 3. 增强可维护性
- 集中的GPIO管理
- 清晰的引脚使用情况
- 统一的接口

### 4. 保持兼容性
- 现有模块仍可独立工作
- 渐进式迁移支持
- 向后兼容的接口

## 测试方法

运行GPIO管理器测试：
```bash
python test_gpio_manager.py
```

运行主程序：
```bash
python main.py
```

## 注意事项

1. **引脚配置**: 确保配置文件中的LED引脚号正确
2. **硬件连接**: 检查所有硬件连接是否正确
3. **权限问题**: 在树莓派上可能需要sudo权限
4. **模拟模式**: 在没有GPIO的环境中会自动使用模拟模式

## 故障排除

### LED不工作
1. 检查GPIO管理器状态：运行 `test_gpio_manager.py`
2. 查看引脚分配情况：检查是否有引脚冲突
3. 验证硬件连接：使用万用表测试电路
4. 检查配置文件：确认LED引脚配置正确

### 初始化失败
1. 确保按正确顺序初始化（先GPIO管理器，再其他模块）
2. 检查是否有权限问题
3. 查看错误日志获取详细信息

这个改进方案通过统一的GPIO管理解决了原有的引脚冲突和初始化问题，使系统更加稳定可靠。
