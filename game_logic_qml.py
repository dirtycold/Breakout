# -*- coding: utf-8 -*-
"""
游戏逻辑层（Python 后端）
Game Logic Layer (Python Backend)

使用 qtpy 抽象层，优先选择 PyQt6
"""
import math
import colorsys
import os

# 优先使用 PyQt6
# os.environ.setdefault('QT_API', 'pyqt6')

from qtpy.QtCore import QObject, Signal, Slot, Property, QTimer
from qtpy.QtQml import qmlRegisterType

from constants import *

# 导出颜色列表供 QML 使用
def getBrickColors():
    """获取砖块颜色列表（HEX 格式）/ Get Brick Colors (HEX format)"""
    return BRICK_COLORS_HEX


class GameState(QObject):
    """游戏状态管理 / Game State Management"""

    scoreChanged = Signal(int)
    gameStatusChanged = Signal(int)
    messageChanged = Signal(str)
    brickCountChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self._game_status = GameStatus.NOT_STARTED
        self._message = "按空格键开始 / Press SPACE to start"
        self._brick_count = 0

    @Property(int, notify=scoreChanged)
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        if self._score != value:
            self._score = value
            self.scoreChanged.emit(value)

    @Property(int, notify=gameStatusChanged)
    def gameStatus(self):
        return self._game_status

    @gameStatus.setter
    def gameStatus(self, value):
        if self._game_status != value:
            self._game_status = value
            self.gameStatusChanged.emit(value)

    @Property(int, notify=brickCountChanged)
    def brickCount(self):
        return self._brick_count

    @brickCount.setter
    def brickCount(self, value):
        if self._brick_count != value:
            self._brick_count = value
            self.brickCountChanged.emit(value)

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        if self._message != value:
            self._message = value
            self.messageChanged.emit(value)


class Ball(QObject):
    """球对象 / Ball Object"""

    positionChanged = Signal(float, float)
    colorChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._x = SCREEN_WIDTH / 2
        self._y = SCREEN_HEIGHT - 70 - BALL_RADIUS - 2  # 挡板上方（y=518）
        self._dx = 0
        self._dy = 0
        self._active = False
        self._hue = 0.0

    @Property(float, notify=positionChanged)
    def x(self):
        return self._x

    @Property(float, notify=positionChanged)
    def y(self):
        return self._y

    @Slot()
    def launch(self):
        """发射球 / Launch Ball"""
        angle_rad = math.radians(BALL_START_ANGLE)
        self._dx = BALL_SPEED * math.cos(angle_rad)
        self._dy = -BALL_SPEED * math.sin(angle_rad)  # 向上为负
        self._active = True

    @Slot(float)
    def update(self, delta_time):
        """更新球的位置 / Update Ball Position"""
        if not self._active:
            return

        # 更新位置（乘以 delta_time 控制速度）
        self._x += self._dx * delta_time
        self._y += self._dy * delta_time

        # 边界碰撞 / Boundary Collision
        if self._x - BALL_RADIUS <= 0 or self._x + BALL_RADIUS >= SCREEN_WIDTH:
            self._dx = -self._dx
            self._x = max(BALL_RADIUS, min(SCREEN_WIDTH - BALL_RADIUS, self._x))

        if self._y - BALL_RADIUS <= 0:  # 顶部
            self._dy = -self._dy
            self._y = BALL_RADIUS

        # 更新彩虹色 / Update Rainbow Color
        self._hue = (self._hue + RAINBOW_SPEED * delta_time) % 1.0
        rgb = colorsys.hsv_to_rgb(self._hue, 1.0, 1.0)
        color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        self.colorChanged.emit(color)

        self.positionChanged.emit(self._x, self._y)

    @Slot(float, float, float, result=bool)
    def checkPaddleCollision(self, paddle_x, paddle_y, paddle_width):
        """检测与挡板碰撞 / Check Paddle Collision"""
        if not self._active:
            return False

        if (self._y + BALL_RADIUS >= paddle_y and
            self._y + BALL_RADIUS <= paddle_y + PADDLE_HEIGHT and
            self._x >= paddle_x and
            self._x <= paddle_x + paddle_width):

            # 计算反弹角度 / Calculate Bounce Angle
            hit_pos = (self._x - paddle_x) / paddle_width  # 0.0 到 1.0
            angle = -60 + (hit_pos * 120)  # -60° 到 +60°
            angle_rad = math.radians(angle)

            speed = math.sqrt(self._dx**2 + self._dy**2)
            self._dx = speed * math.sin(angle_rad)
            self._dy = -abs(speed * math.cos(angle_rad))  # 向上为负

            return True
        return False

    @Slot(result=bool)
    def isOutOfBounds(self):
        """检测是否掉出边界 / Check if Out of Bounds"""
        return self._y + BALL_RADIUS >= SCREEN_HEIGHT

    @Slot()
    def reset(self):
        """重置球 / Reset Ball"""
        self._x = SCREEN_WIDTH / 2
        self._y = SCREEN_HEIGHT - 70 - BALL_RADIUS - 2
        self._dx = 0
        self._dy = 0
        self._active = False
        self.positionChanged.emit(self._x, self._y)

    @Slot(float, float)
    def followPaddle(self, paddle_x, paddle_width):
        """球跟随挡板移动（游戏未开始时）/ Ball follows paddle"""
        if not self._active:
            self._x = paddle_x + paddle_width / 2
            self._y = SCREEN_HEIGHT - 70 - BALL_RADIUS - 2  # 挡板正上方
            self.positionChanged.emit(self._x, self._y)


class GameController(QObject):
    """游戏主控制器 / Main Game Controller"""

    requestCreateExplosion = Signal(float, float, str)  # x, y, color

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = GameState(self)
        self._ball = Ball(self)

        # 计算总砖块数（菱形布局）
        total_bricks = sum(5 + row * 2 for row in range(BRICK_ROWS))
        self._state.brickCount = total_bricks

        # 游戏计时器 / Game Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.setInterval(16)  # ~60 FPS

    @Property(QObject, constant=True)
    def state(self):
        """游戏状态对象"""
        return self._state

    @Property(QObject, constant=True)
    def ball(self):
        """球对象"""
        return self._ball

    @Slot()
    def startGame(self):
        """开始游戏 / Start Game"""
        if self._state.gameStatus == GameStatus.NOT_STARTED:
            self._ball.launch()
            self.timer.start()
            self._state.message = ""
            self._state.gameStatus = GameStatus.PLAYING

    @Slot()
    def resetGame(self):
        """重置游戏 / Reset Game"""
        self.timer.stop()
        self._ball.reset()
        self._state.score = 0
        self._state.gameStatus = GameStatus.NOT_STARTED
        self._state.message = "按空格键开始 / Press SPACE to start"
        
        # 重置砖块计数
        total_bricks = sum(5 + row * 2 for row in range(BRICK_ROWS))
        self._state.brickCount = total_bricks

    @Slot(float, float, float, result=bool)
    def checkPaddleCollision(self, paddle_x, paddle_y, paddle_width):
        """检测挡板碰撞 / Check Paddle Collision"""
        return self._ball.checkPaddleCollision(paddle_x, paddle_y, paddle_width)

    @Slot(float, float, float, float, str, result=bool)
    def checkBrickCollision(self, brick_x, brick_y, brick_width, brick_height, brick_color):
        """检测砖块碰撞 / Check Brick Collision"""
        ball_x = self._ball.x
        ball_y = self._ball.y

        # AABB 碰撞检测
        closest_x = max(brick_x, min(ball_x, brick_x + brick_width))
        closest_y = max(brick_y, min(ball_y, brick_y + brick_height))

        distance = math.sqrt((ball_x - closest_x)**2 + (ball_y - closest_y)**2)

        if distance < BALL_RADIUS:
            # 计算碰撞方向 / Calculate Collision Direction
            overlap_left = (ball_x + BALL_RADIUS) - brick_x
            overlap_right = (brick_x + brick_width) - (ball_x - BALL_RADIUS)
            overlap_top = (ball_y + BALL_RADIUS) - brick_y
            overlap_bottom = (brick_y + brick_height) - (ball_y - BALL_RADIUS)

            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

            if min_overlap in (overlap_left, overlap_right):
                self._ball._dx = -self._ball._dx
            else:
                self._ball._dy = -self._ball._dy

            # 增加分数 / Increase Score
            self._state.score += 10
            
            # 减少砖块计数 / Decrease brick count
            self._state.brickCount -= 1
            
            # 检测胜利 / Check Victory
            if self._state.brickCount <= 0:
                self.timer.stop()
                self._state.gameStatus = GameStatus.VICTORY
                self._state.message = "恭喜胜利! / Victory!\n按 R 重新开始 / Press R to restart"

            # 创建爆炸效果 / Create Explosion Effect
            self.requestCreateExplosion.emit(
                brick_x + brick_width / 2,
                brick_y + brick_height / 2,
                brick_color
            )

            return True
        return False

    def _update(self):
        """游戏主循环 / Main Game Loop"""
        self._ball.update(0.016)  # 约 60 FPS

        # 检测掉落 / Check if Ball Fell
        if self._ball.isOutOfBounds():
            self.timer.stop()
            self._state.gameStatus = GameStatus.GAME_OVER
            self._state.message = "游戏结束! / Game Over!\n按 R 重新开始 / Press R to restart"
