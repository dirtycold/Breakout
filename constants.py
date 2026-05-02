"""
游戏常量配置
Game Constants Configuration
"""

# 屏幕设置 / Screen Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "DX-Ball Clone - 打砖块游戏"

# 颜色定义 / Color Definitions
COLOR_BACKGROUND = (20, 20, 40)
COLOR_PADDLE = (100, 200, 255)
COLOR_BALL = (255, 255, 255)

# 砖块颜色 / Brick Colors
BRICK_COLORS = [
    (255, 100, 100),  # 红色 Red
    (255, 165, 100),  # 橙色 Orange
    (255, 255, 100),  # 黄色 Yellow
    (100, 255, 100),  # 绿色 Green
    (100, 200, 255),  # 蓝色 Blue
    (200, 100, 255),  # 紫色 Purple
]

# 挡板设置 / Paddle Settings
PADDLE_WIDTH = 120
PADDLE_HEIGHT = 15
PADDLE_SPEED = 500  # 像素/秒 pixels/second
PADDLE_Y_POSITION = 50  # 距离底部的高度

# 球设置 / Ball Settings
BALL_RADIUS = 8
BALL_SPEED = 300  # 像素/秒 pixels/second
BALL_START_ANGLE = 60  # 初始发射角度（度）

# 砖块设置 / Brick Settings
BRICK_WIDTH = 48  # 约为70的2/3
BRICK_HEIGHT = 18
BRICK_MARGIN = 5
BRICK_ROWS = 6
BRICK_COLUMNS = 10
BRICK_TOP_MARGIN = 100  # 距离顶部的距离
BRICK_LEFT_MARGIN = 30  # 距离左侧的距离

# 视觉效果 / Visual Effects
PARTICLE_COUNT = 20  # 爆炸粒子数量
PARTICLE_LIFETIME = 0.8  # 粒子存活时间（秒）
RAINBOW_SPEED = 2.0  # 彩虹渐变速度
