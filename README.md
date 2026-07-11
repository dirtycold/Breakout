# DX-Ball Clone - 打砖块游戏

简单的打砖块游戏，提供 **Arcade** 和 **QML** 两个版本实现，适合学习对比。

## 版本说明 / Versions

### 🎮 Arcade 版本（推荐）
- 纯 Python 实现
- 使用 Arcade 游戏引擎
- 代码简洁，适合学习

### 🖼️ QML 版本
- Python (逻辑) + QML (UI)
- 使用 Qt6，支持 PyQt6/PySide6
- MVC 架构，声明式 UI

## 安装依赖 / Installation

### Arcade 版本
```bash
pip install -r requirements.txt
```

### QML 版本
```bash
pip install -r requirements_qml.txt
```

或手动安装：
```bash
pip install qtpy PyQt6 pillow
```
> QML 版本也会通过 Pillow 生成共享彩虹球纹理；使用 `requirements_qml.txt` 安装会自动包含它。

## 运行游戏 / Run the Game

### Arcade 版本
```bash
python main_arcade.py
```

### QML 版本
```bash
python main_qml.py
```

## 游戏操作 / Controls

- **左箭头 / Left Arrow**: 向左移动挡板
- **右箭头 / Right Arrow**: 向右移动挡板
- **鼠标 / Mouse**: 移动鼠标控制挡板位置
- **空格键 / Space**: 开始游戏（发射球）
- **R 键 / R Key**: 重新开始游戏

## 游戏特性 / Features

✅ **已实现功能**:
- 🎮 球、挡板、砖块基础玩法
- 💎 菱形砖块布局（视觉更美观）
- 🎯 改进的物理碰撞系统（精确的左右、上下反弹）
- 🌈 彩虹条纹球（共享纹理 + 挡板命中位置驱动旋转）
- ✨ 抗锯齿圆形球体（使用PIL超采样技术）
- 💥 砖块爆炸粒子效果（重力、淡出动画）
- 🎁 奖励系统基础框架（自由落体奖励物件 + 火球奖励）
- 🎲 智能球反弹（击中挡板不同位置产生不同角度）
- 🖱️ 键盘 + 鼠标双重控制
- 🈳 中文 + 英文双语界面
- 📊 分数统计系统
- 🎯 空格键延迟发射机制

🚀 **未来计划**:
- 扩展奖励效果（穿越球、消金砖、减速、直接过关、加速、砖块降低、多重球等）
- 精美的 sprite 图片替代彩色矩形
- 音效和背景音乐
- 生命值系统（多次机会）
- 关卡系统（多个难度等级）
- 最高分记录存档

## 项目结构 / Project Structure

```
Breakout/
├── main_arcade.py       # Arcade 版本主程序
├── main_qml.py          # QML 版本主程序
├── game_logic_qml.py    # QML 游戏逻辑层（Python）
├── main.qml             # QML UI 界面
├── constants.py         # 共享常量配置
├── ball_texture.py      # 共享彩虹球纹理与旋转动画
├── paddle_texture.py    # 共享彩虹尖牙挡板纹理与图集
├── qt_config.py         # Qt 绑定配置（qtpy）
├── requirements.txt     # Arcade 依赖
├── requirements_qml.txt # QML 依赖
├── README.md            # 项目说明文档
└── PROGRESS.md          # 开发进度记录
```

> 💡 **提示**: 两个版本共享 `constants.py`，实现完全一致的游戏体验

## 代码说明 / Code Overview

### 主要类 / Main Classes

- **`RainbowBall`**: 彩虹条纹球类
  - 使用 PIL 创建抗锯齿彩虹条纹纹理
  - 根据上次挡板命中位置设置旋转方向和速度
  - 继承自 `arcade.Sprite`

- **`BreakoutGame`**: 主游戏窗口类
  - 继承自 `arcade.Window`
  - 管理游戏状态、对象和逻辑

- **`RewardModel` / `RewardSprite`**: 奖励物件
  - 砖块被小球破坏时按概率生成奖励
  - 奖励生成后先向上运动，再受重力下落
  - 被挡板接住后应用效果，落到挡板下方后销毁

### 核心方法 / Core Methods

- `setup()`: 初始化/重置游戏（创建挡板、球、砖块）
- `on_draw()`: 绘制游戏画面（每帧调用）
- `on_update(delta_time)`: 更新游戏逻辑（物理、碰撞检测）
- `create_explosion()`: 创建爆炸粒子效果
- `spawn_reward()` / `RewardModel.create_fireball_reward()`: 创建奖励物件
- `update_particles()`: 更新粒子动画（位置、透明度、重力）
- `on_key_press()` / `on_key_release()`: 键盘事件处理
- `on_mouse_motion()`: 鼠标移动事件处理

### 技术亮点 / Technical Highlights

1. **抗锯齿渲染**: 使用 PIL 的 4x 超采样技术渲染平滑圆形和条纹边缘
2. **纹理动画**: 共享彩虹条纹纹理，旋转方向和速度由上次挡板命中位置决定
3. **物理碰撞**: 基于重叠量判断碰撞方向，避免球体卡住
4. **粒子系统**: 自定义粒子效果（速度、重力、淡出）
5. **角度控制**: 击中挡板不同位置产生 ±60° 反弹角度
6. **奖励物理**: 奖励物件使用初始上抛速度 + 重力加速度实现自由落体
7. **双重控制**: 同时支持键盘和鼠标操作

## 奖励系统 / Reward System

当前奖励系统已经具备完整生命周期：

1. 小球破坏砖块时按概率触发奖励掉落。
2. 奖励物件从砖块中心生成；每个实例会随机获得水平速度、上抛速度、重力与旋转速度，因此拥有不同的运动轨迹。
3. 奖励与挡板碰撞时被接取并应用效果。
4. 奖励碰到左右墙会反弹；落到挡板下方后销毁，不再产生效果。
5. 奖励以更醒目的方块贴图显示；图标均由 Pillow 在内存中绘制，不依赖外部图片文件。
6. 当前总掉落概率为 `50%`；普通奖励权重为 `1`，骷髅权重为 `0.5`，因此消极奖励的概率是任一其他奖励的一半。

当前启用的奖励：

- **火球 / Fireball（正向，绿色提示）**：接取后小球带有火焰粒子尾迹；小球命中砖块时，只会破坏首个命中砖块及运动方向一侧局部 `2x2` 范围内的砖块。
- **挡板变长 / Extend Paddle（中性，灰底蓝色向外三角）**：挡板宽度增加 `30px`，可以连续叠加，最大为半个屏幕宽度（当前 `400px`）。
- **挡板变短 / Shrink Paddle（中性，灰底红色向内三角）**：挡板宽度减少 `30px`，可以连续叠加，最小为小球直径（当前 `20px`）。
- **奖励重置 / Reset Rewards（中性，灰色提示）**：清除火球和激光状态，清空激光子弹，并将挡板恢复为默认宽度。
- **激光枪 / Laser（正向，绿色提示）**：在挡板两侧安装枪管；游戏中按鼠标左键发射双激光，命中砖块后直接消除并计分。
- **骷髅 / Skull（消极，红色提示）**：接取后立即失败。

挡板尺寸变化时会按新宽度重新生成并缓存动画图集；白色三角牙齿保持固定宽度和高度，只增减牙齿数量，不随挡板拉伸或压缩。

奖励分类规划：

- **正向奖励**：火球、激光枪；穿越球、消金砖、减速、直接过关待实现。
- **反向奖励**：骷髅；加速、砖块降低待实现。
- **中性奖励**：挡板变长、挡板变短、奖励重置；多重球待实现。

## 学习要点 / Learning Points

1. **面向对象编程**: 使用类组织游戏代码，继承 `arcade.Sprite` 和 `arcade.Window`
2. **游戏循环**: 理解 `on_update()` 和 `on_draw()` 的分离职责
3. **碰撞检测**:
   - 简单碰撞：`arcade.check_for_collision()`
   - 列表碰撞：`arcade.check_for_collision_with_list()`
   - 精确碰撞方向判断（重叠量计算）
4. **向量运算**: 使用三角函数（`math.sin`, `math.cos`）计算球的速度分量
5. **视觉效果**:
   - 程序化彩虹条纹纹理
   - 基于挡板命中位置的旋转控制
   - 粒子系统（位置、速度、透明度动画）
   - 抗锯齿渲染（PIL 超采样）
6. **图像处理**: 使用 PIL (Pillow) 创建纹理
7. **事件驱动编程**: 处理键盘、鼠标事件
8. **游戏状态管理**: 开始前、游戏中、游戏结束状态

## 自定义配置 / Customization

在 `constants.py` 中可以轻松修改游戏参数：

### 屏幕设置
- `SCREEN_WIDTH` / `SCREEN_HEIGHT`: 窗口尺寸
- `SCREEN_TITLE`: 窗口标题

### 物理参数
- `PADDLE_SPEED`: 挡板移动速度
- `BALL_SPEED`: 球的初始速度
- `BALL_START_ANGLE`: 球的发射角度（度）
- `REWARD_TRIGGER_PROBABILITY`: 砖块触发任意奖励的总概率（当前为 `0.5`）
- `PADDLE_REWARD_SIZE_STEP` / `PADDLE_MIN/MAX_WIDTH`: 挡板尺寸奖励的步长和边界
- `REWARD_MIN/MAX_SPEED_X/Y` / `REWARD_MIN/MAX_GRAVITY`: 奖励物件随机轨迹范围
- `FIREBALL_IMPACT_COLUMNS` / `FIREBALL_IMPACT_ROWS`: 火球撞击的局部砖块范围（当前为 `2x2`）

### 视觉效果
- `BRICK_COLORS`: 砖块颜色列表（RGB 元组）
- `COLOR_BACKGROUND`: 背景颜色
- `BALL_ROTATION_MAX_SPEED`: 挡板边缘命中时的最大旋转速度
- `PARTICLE_COUNT`: 爆炸粒子数量
- `PARTICLE_LIFETIME`: 粒子存活时间（秒）

### 游戏布局
- `BRICK_ROWS`: 砖块行数（影响菱形大小）
- `BRICK_WIDTH` / `BRICK_HEIGHT`: 砖块尺寸
- `BRICK_MARGIN`: 砖块间距
- `PADDLE_WIDTH` / `PADDLE_HEIGHT`: 挡板尺寸
- `BALL_RADIUS`: 球的半径

## 开发环境 / Development Environment

- **Python**: 3.8+
- **依赖库**:
  - `arcade`: 游戏框架
  - `pillow`: 图像处理（用于创建抗锯齿纹理）

## 许可证 / License

本项目仅用于学习目的。
