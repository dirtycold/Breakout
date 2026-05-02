"""
游戏常量配置
Game Constants Configuration
"""

# 屏幕设置 / Screen Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "DX-Ball Clone - 打砖块游戏"

# 颜色定义 / Color Definitions
COLOR_BACKGROUND = (26, 26, 46)  # #1A1A2E
COLOR_PADDLE = (52, 152, 219)  # #3498DB
COLOR_BALL = (255, 255, 255)

# 砖块颜色 / Brick Colors
BRICK_COLORS = [
    (255, 107, 107),  # 红色 Red #FF6B6B
    (255, 217, 61),   # 黄色 Yellow #FFD93D
    (108, 203, 119),  # 绿色 Green #6BCB77
    (77, 150, 255),   # 蓝色 Blue #4D96FF
    (157, 78, 221),   # 紫色 Purple #9D4EDD
]

# 挡板设置 / Paddle Settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 500  # 像素/秒 pixels/second
PADDLE_Y_POSITION = 50  # 距离底部的高度

# 球设置 / Ball Settings
BALL_RADIUS = 10
BALL_SPEED = 300  # 像素/秒 pixels/second
BALL_START_ANGLE = 60  # 初始发射角度（度）

# 砖块设置 / Brick Settings
BRICK_WIDTH = 55
BRICK_HEIGHT = 25
BRICK_MARGIN = 4
BRICK_ROWS = 5
BRICK_COLUMNS = 10  # 不再使用，改为菱形布局
BRICK_TOP_MARGIN = 80  # 距离顶部的距离
BRICK_LEFT_MARGIN = 30  # 距离左侧的距离

# 视觉效果 / Visual Effects
PARTICLE_COUNT = 15  # 爆炸粒子数量
PARTICLE_LIFETIME = 1.0  # 粒子存活时间（秒）
RAINBOW_SPEED = 0.5  # 彩虹渐变速度
