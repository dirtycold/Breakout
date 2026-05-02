# DX-Ball Clone - 打砖块游戏

简单的打砖块游戏，使用 Python Arcade 开发，适合小朋友学习。

## 安装依赖 / Installation

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install arcade pillow
```

## 运行游戏 / Run the Game

```bash
python main.py
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
- 🌈 彩虹渐变球（HSV色彩空间动画效果）
- ✨ 抗锯齿圆形球体（使用PIL超采样技术）
- 💥 砖块爆炸粒子效果（重力、淡出动画）
- 🎲 智能球反弹（击中挡板不同位置产生不同角度）
- 🖱️ 键盘 + 鼠标双重控制
- 🈳 中文 + 英文双语界面
- 📊 分数统计系统
- 🎯 空格键延迟发射机制

🚀 **未来计划**:
- Power-ups（多球、挡板变大/变小、减速、激光等）
- 精美的 sprite 图片替代彩色矩形
- 音效和背景音乐
- 生命值系统（多次机会）
- 关卡系统（多个难度等级）
- 最高分记录存档

## 项目结构 / Project Structure

```
Breakout/
├── main.py           # 主游戏文件（包含 RainbowBall 和 BreakoutGame 类）
├── constants.py      # 游戏常量配置（屏幕、颜色、物理参数等）
├── requirements.txt  # Python 依赖库列表
├── README.md         # 项目说明文档
└── PROGRESS.md       # 开发进度记录
```

## 代码说明 / Code Overview

### 主要类 / Main Classes

- **`RainbowBall`**: 彩虹渐变球类
  - 使用 PIL 创建抗锯齿圆形纹理
  - HSV 色彩空间实现彩虹渐变动画
  - 继承自 `arcade.Sprite`

- **`BreakoutGame`**: 主游戏窗口类
  - 继承自 `arcade.Window`
  - 管理游戏状态、对象和逻辑

### 核心方法 / Core Methods

- `setup()`: 初始化/重置游戏（创建挡板、球、砖块）
- `on_draw()`: 绘制游戏画面（每帧调用）
- `on_update(delta_time)`: 更新游戏逻辑（物理、碰撞检测）
- `create_explosion()`: 创建爆炸粒子效果
- `update_particles()`: 更新粒子动画（位置、透明度、重力）
- `on_key_press()` / `on_key_release()`: 键盘事件处理
- `on_mouse_motion()`: 鼠标移动事件处理

### 技术亮点 / Technical Highlights

1. **抗锯齿渲染**: 使用 PIL 的 4x 超采样技术渲染平滑圆形
2. **色彩动画**: HSV 色彩空间转 RGB，实现流畅彩虹效果
3. **物理碰撞**: 基于重叠量判断碰撞方向，避免球体卡住
4. **粒子系统**: 自定义粒子效果（速度、重力、淡出）
5. **角度控制**: 击中挡板不同位置产生 ±60° 反弹角度
6. **双重控制**: 同时支持键盘和鼠标操作

## 学习要点 / Learning Points

1. **面向对象编程**: 使用类组织游戏代码，继承 `arcade.Sprite` 和 `arcade.Window`
2. **游戏循环**: 理解 `on_update()` 和 `on_draw()` 的分离职责
3. **碰撞检测**:
   - 简单碰撞：`arcade.check_for_collision()`
   - 列表碰撞：`arcade.check_for_collision_with_list()`
   - 精确碰撞方向判断（重叠量计算）
4. **向量运算**: 使用三角函数（`math.sin`, `math.cos`）计算球的速度分量
5. **视觉效果**:
   - HSV/RGB 色彩空间转换（`colorsys.hsv_to_rgb`）
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

### 视觉效果
- `BRICK_COLORS`: 砖块颜色列表（RGB 元组）
- `COLOR_BACKGROUND`: 背景颜色
- `RAINBOW_SPEED`: 彩虹渐变速度
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
  - `colorsys`: 色彩空间转换（Python 标准库）

## 许可证 / License

本项目仅用于学习目的。
