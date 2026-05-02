# DX-Ball Clone - QML 版本

这是使用 Qt6 QML + qtpy 实现的打砖块游戏，用于对比 Arcade 版本的差异。

## 特性

- ✅ 使用 **qtpy** 抽象层，兼容 PyQt6/PySide6/PyQt5/PySide2
- ✅ **优先使用 PyQt6**（性能更好，许可证友好）
- ✅ 自动回退到其他可用的 Qt 绑定
- ✅ 完整的游戏功能（与 Arcade 版本相同）

## 安装依赖

```bash
cd qml_version

# 方案1：安装所有支持的绑定（推荐）
pip install -r requirements.txt

# 方案2：仅安装 PyQt6
pip install qtpy PyQt6

# 方案3：仅安装 PySide6
pip install qtpy PySide6
```

## 检测可用的 Qt 绑定

```bash
python qt_config.py
```

输出示例：
```
检测可用的 Qt 绑定...

可用的 Qt 绑定:
  - PyQt6 6.5.0
  - PySide6 6.5.0

✅ 使用 Qt 绑定: PyQt6 (版本 6.5.0)
```

## 运行游戏

```bash
# 使用默认绑定（PyQt6）
python main.py

# 强制使用特定绑定
QT_API=pyqt6 python main.py
QT_API=pyside6 python main.py
QT_API=pyqt5 python main.py
```

## 游戏操作

- **左箭头 / Left Arrow**: 向左移动挡板
- **右箭头 / Right Arrow**: 向右移动挡板
- **鼠标 / Mouse**: 移动鼠标控制挡板位置
- **空格键 / Space**: 开始游戏（发射球）
- **R 键 / R Key**: 重新开始游戏

## 项目结构

```
qml_version/
├── main.py           # 主入口（Python）
├── game_logic.py     # 游戏逻辑（Python 后端）
├── main.qml          # UI 界面（QML 前端）
├── constants.py      # 游戏常量配置
├── requirements.txt  # 依赖库
└── README.md         # 说明文档
```

## 架构说明

### Python 后端 (`game_logic.py`)
- **GameController**: 游戏主控制器
- **Ball**: 球对象（物理计算）
- **GameState**: 游戏状态管理
- 使用 `@QmlElement` 装饰器暴露给 QML

### QML 前端 (`main.qml`)
- 声明式 UI（矩形、文字、动画）
- 粒子系统（纯 QML 实现）
- 数据绑定（自动更新 UI）

## 与 Arcade 版本的对比

| 特性 | Arcade 版本 | QML 版本 |
|------|------------|----------|
| **语言** | 纯 Python | Python + QML |
| **代码行数** | ~300 行 | ~450 行 |
| **架构** | 单文件 | MVC 分离 |
| **渲染** | OpenGL (命令式) | QML Scene Graph (声明式) |
| **学习曲线** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **UI 灵活性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **游戏专用特性** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 技术亮点

1. **Qt Property 系统**: 自动 UI 更新
2. **Signal/Slot 机制**: Python ↔ QML 通信
3. **声明式 UI**: 易于设计和维护
4. **RHI 后端**: 自动优化（Metal/DX12/Vulkan）

## 注意事项

⚠️ 这个版本主要用于**学习和对比**，Arcade 版本更适合实际游戏开发！
