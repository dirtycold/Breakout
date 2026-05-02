# -*- coding: utf-8 -*-
"""
游戏常量配置
Game Constants Configuration (QML版)
"""

# 屏幕设置 / Screen Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "DX-Ball Clone (QML版) - 打砖块游戏"

# 挡板设置 / Paddle Settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 8

# 球设置 / Ball Settings
BALL_RADIUS = 10
BALL_SPEED = 5
BALL_START_ANGLE = 60  # 度

# 砖块设置 / Brick Settings
BRICK_WIDTH = 55
BRICK_HEIGHT = 25
BRICK_MARGIN = 4
BRICK_ROWS = 5

# 颜色定义 (十六进制字符串，用于 QML)
BRICK_COLORS = [
    "#FF6B6B",  # 红色 Red
    "#FFD93D",  # 黄色 Yellow
    "#6BCB77",  # 绿色 Green
    "#4D96FF",  # 蓝色 Blue
    "#9D4EDD",  # 紫色 Purple
]
COLOR_BACKGROUND = "#1A1A2E"
COLOR_PADDLE = "#3498DB"

# 粒子效果 / Particle Effects
PARTICLE_COUNT = 15
PARTICLE_LIFETIME = 1.0  # 秒
PARTICLE_GRAVITY = 500

# 彩虹效果 / Rainbow Effect
RAINBOW_SPEED = 0.5
