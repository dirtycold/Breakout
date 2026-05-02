# DX-Ball Clone - 打砖块游戏

简单的打砖块游戏，使用 Python Arcade 开发，适合小朋友学习。

## 安装依赖 / Installation

```bash
pip install arcade
```

## 运行游戏 / Run the Game

```bash
cd breakout_game
python main.py
```

## 游戏操作 / Controls

- **左箭头 / Left Arrow**: 向左移动挡板
- **右箭头 / Right Arrow**: 向右移动挡板
- **R 键 / R Key**: 重新开始游戏

## 游戏特性 / Features

✅ **第一阶段 (已完成)**:
- 球、挡板、砖块基础玩法
- 球的物理反弹（击中挡板不同位置产生不同角度）
- 闪烁的砖块效果
- 砖块爆炸粒子效果
- 分数系统

🚀 **第二阶段 (计划中)**:
- Power-ups（多球、挡板变大/变小、减速、激光等）
- 精美的 sprite 图片替代彩色矩形
- 音效和背景音乐
- 生命值系统
- 最高分记录

## 项目结构 / Project Structure

```
breakout_game/
├── main.py           # 主游戏文件
├── constants.py      # 游戏常量配置
└── README.md         # 说明文档
```

## 代码说明 / Code Overview

- `BreakoutGame`: 主游戏类，继承自 `arcade.Window`
- `setup()`: 初始化游戏对象（挡板、球、砖块）
- `on_draw()`: 绘制游戏画面
- `update()`: 更新游戏逻辑（每帧调用）
- `create_explosion()`: 创建爆炸粒子效果
- `ParticleEmitter`: 简单的粒子系统类

## 学习要点 / Learning Points

1. **面向对象编程**: 使用类组织游戏代码
2. **游戏循环**: `update()` 和 `on_draw()` 方法
3. **碰撞检测**: `arcade.check_for_collision()`
4. **向量运算**: 使用三角函数计算球的速度
5. **视觉效果**: 颜色插值、粒子系统

## 自定义配置 / Customization

在 `constants.py` 中可以修改：
- 屏幕尺寸
- 游戏速度
- 颜色方案
- 砖块数量和布局
