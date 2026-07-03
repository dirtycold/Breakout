"""
游戏常量配置
Game Constants Configuration

此文件同时支持 Arcade 和 QML 版本
"""
from enum import IntEnum

# 游戏状态枚举 / Game Status Enum
class GameStatus(IntEnum):
    """游戏状态 / Game Status"""
    NOT_STARTED = 0  # 未开始
    PLAYING = 1      # 游戏中
    GAME_OVER = 2    # 游戏失败
    VICTORY = 3      # 胜利

# 屏幕设置 / Screen Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "DX-Ball Clone - 打砖块游戏"
SCREEN_TITLE_QML = "DX-Ball Clone (QML版) - 打砖块游戏"

# 文案设置 / Text Settings
SCORE_LABEL = "分数 Score"
MESSAGE_START_LINES = (
    "按空格键开始游戏",
    "Press SPACE to Start",
    "← → 移动挡板 / Move Paddle",
)
MESSAGE_GAME_OVER_LINES = (
    "游戏结束！按 R 重新开始",
    "Game Over! Press R to Restart",
)
MESSAGE_VICTORY_LINES = (
    "恭喜胜利！按 R 重新开始",
    "Victory! Press R to Restart",
)
MESSAGE_START = "\n".join(MESSAGE_START_LINES)
MESSAGE_GAME_OVER = "\n".join(MESSAGE_GAME_OVER_LINES)
MESSAGE_VICTORY = "\n".join(MESSAGE_VICTORY_LINES)

# 计时设置 / Timing Settings
FRAME_INTERVAL_MS = 16
FIXED_DELTA_TIME = FRAME_INTERVAL_MS / 1000

# 颜色定义 / Color Definitions
COLOR_BACKGROUND = (26, 26, 46)  # #1A1A2E
COLOR_PADDLE = (52, 152, 219)  # #3498DB
COLOR_BALL = (255, 255, 255)

# 砖块颜色 / Brick Colors (Arcade RGB 格式)
BRICK_COLORS = [
    (255, 107, 107),  # 红色 Red #FF6B6B
    (255, 217, 61),   # 黄色 Yellow #FFD93D
    (108, 203, 119),  # 绿色 Green #6BCB77
    (77, 150, 255),   # 蓝色 Blue #4D96FF
    (157, 78, 221),   # 紫色 Purple #9D4EDD
]

# 砖块颜色 (QML 十六进制格式)
BRICK_COLORS_HEX = [
    "#FF6B6B",  # 红色 Red
    "#FFD93D",  # 黄色 Yellow
    "#6BCB77",  # 绿色 Green
    "#4D96FF",  # 蓝色 Blue
    "#9D4EDD",  # 紫色 Purple
]
COLOR_BACKGROUND_HEX = "#1A1A2E"
COLOR_PADDLE_HEX = "#3498DB"

# 挡板设置 / Paddle Settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 500  # 像素/秒 pixels/second
PADDLE_Y_POSITION = 50  # 挡板中心距离底部的高度
PADDLE_CORNER_RADIUS = 10
PADDLE_BOUNCE_MAX_ANGLE = 60

# 球设置 / Ball Settings
BALL_RADIUS = 10
BALL_DIAMETER = BALL_RADIUS * 2
BALL_SPEED = 300  # 像素/秒 pixels/second
BALL_START_ANGLE = 60  # 初始发射角度（度）
BALL_PADDLE_GAP = 2

# 砖块设置 / Brick Settings
BRICK_WIDTH = 55
BRICK_HEIGHT = 25
BRICK_MARGIN = 4
BRICK_ROWS = 5
BRICK_BASE_COUNT = 5
BRICK_ROW_INCREMENT = 2
BRICK_COLUMNS = 10  # 不再使用，改为菱形布局
BRICK_TOP_MARGIN = 80  # 距离顶部的距离
BRICK_LEFT_MARGIN = 30  # 距离左侧的距离
BRICK_CORNER_RADIUS = 6
SCORE_PER_BRICK = 10

# 视觉效果 / Visual Effects
PARTICLE_COUNT = 15  # 爆炸粒子数量
PARTICLE_RADIUS = 3
PARTICLE_MIN_SPEED = 50
PARTICLE_MAX_SPEED = 150
PARTICLE_GRAVITY = 500
PARTICLE_LIFETIME = 1.0  # 粒子存活时间（秒）
RAINBOW_SPEED = 0.5  # 彩虹渐变速度


def bricks_in_row(row):
    """返回指定行的砖块数 / Return brick count for a row."""
    return BRICK_BASE_COUNT + row * BRICK_ROW_INCREMENT


def total_brick_count():
    """返回当前布局的总砖块数 / Return total brick count."""
    return sum(bricks_in_row(row) for row in range(BRICK_ROWS))


def brick_row_width(row):
    """返回指定行的总宽度 / Return total row width."""
    count = bricks_in_row(row)
    return count * BRICK_WIDTH + (count - 1) * BRICK_MARGIN


def brick_row_left_x(row, screen_width=SCREEN_WIDTH):
    """返回指定行左侧起点 / Return left edge for a centered row."""
    return (screen_width - brick_row_width(row)) / 2


def arcade_brick_center_x(row, column, screen_width=SCREEN_WIDTH):
    """Arcade 坐标系下砖块中心 x / Brick center x in Arcade coordinates."""
    return brick_row_left_x(row, screen_width) + (BRICK_WIDTH + BRICK_MARGIN) * column + BRICK_WIDTH / 2


def arcade_brick_center_y(row):
    """Arcade 坐标系下砖块中心 y / Brick center y in Arcade coordinates."""
    return SCREEN_HEIGHT - BRICK_TOP_MARGIN - (BRICK_HEIGHT + BRICK_MARGIN) * row


def qml_brick_x(row, column, screen_width=SCREEN_WIDTH):
    """QML 坐标系下砖块左上角 x / Brick x in QML coordinates."""
    return brick_row_left_x(row, screen_width) + (BRICK_WIDTH + BRICK_MARGIN) * column


def qml_brick_y(row):
    """QML 坐标系下砖块左上角 y / Brick y in QML coordinates."""
    return SCREEN_HEIGHT - arcade_brick_center_y(row) - BRICK_HEIGHT / 2


def arcade_ball_start_center_y():
    """Arcade 坐标系下球的初始中心 y / Ball start center y in Arcade coordinates."""
    return PADDLE_Y_POSITION + PADDLE_HEIGHT / 2 + BALL_RADIUS + BALL_PADDLE_GAP


def qml_ball_start_center_y():
    """QML 坐标系下球的初始中心 y / Ball start center y in QML coordinates."""
    return SCREEN_HEIGHT - arcade_ball_start_center_y()


def qml_paddle_y():
    """QML 坐标系下挡板左上角 y / Paddle y in QML coordinates."""
    return SCREEN_HEIGHT - (PADDLE_Y_POSITION + PADDLE_HEIGHT / 2)
