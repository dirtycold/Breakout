# -*- coding: utf-8 -*-
"""
游戏逻辑层（Python 后端）
Game Logic Layer (Python Backend)

使用 qtpy 抽象层，优先选择 PyQt6
"""
import math
import random

# 优先使用 PyQt6
# os.environ.setdefault('QT_API', 'pyqt6')

from qtpy.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Property,
    QTimer,
    Qt,
    Signal,
    Slot,
)

from ball_texture import RainbowBallMotion, create_rainbow_ball_data_url
from constants import *

# 导出颜色列表供 QML 使用
def getBrickColors():
    """获取砖块颜色列表（HEX 格式）/ Get Brick Colors (HEX format)"""
    return BRICK_COLORS_HEX


class BrickModel(QAbstractListModel):
    """砖块模型 / Brick Model"""

    BRICK_X_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    BRICK_Y_ROLE = BRICK_X_ROLE + 1
    BRICK_WIDTH_ROLE = BRICK_X_ROLE + 2
    BRICK_HEIGHT_ROLE = BRICK_X_ROLE + 3
    BRICK_COLOR_ROLE = BRICK_X_ROLE + 4
    DESTROYED_ROLE = BRICK_X_ROLE + 5

    ROLE_NAMES = {
        BRICK_X_ROLE: b"brickX",
        BRICK_Y_ROLE: b"brickY",
        BRICK_WIDTH_ROLE: b"brickWidth",
        BRICK_HEIGHT_ROLE: b"brickHeight",
        BRICK_COLOR_ROLE: b"brickColor",
        DESTROYED_ROLE: b"destroyed",
    }

    ROLE_KEYS = {
        BRICK_X_ROLE: "x",
        BRICK_Y_ROLE: "y",
        BRICK_WIDTH_ROLE: "width",
        BRICK_HEIGHT_ROLE: "height",
        BRICK_COLOR_ROLE: "color",
        DESTROYED_ROLE: "destroyed",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bricks = []
        self.reset_bricks()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._bricks)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._bricks):
            return None

        key = self.ROLE_KEYS.get(int(role))
        if key is None:
            return None

        return self._bricks[index.row()][key]

    def roleNames(self):
        return {
            role: QByteArray(name)
            for role, name in self.ROLE_NAMES.items()
        }

    def reset_bricks(self):
        """重置砖块布局 / Reset brick layout."""
        self.beginResetModel()
        self._bricks = []

        for row in range(BRICK_ROWS):
            for column in range(bricks_in_row(row)):
                self._bricks.append({
                    "x": qml_brick_x(row, column),
                    "y": qml_brick_y(row),
                    "width": BRICK_WIDTH,
                    "height": BRICK_HEIGHT,
                    "color": BRICK_COLORS_HEX[row % len(BRICK_COLORS_HEX)],
                    "destroyed": False,
                })

        self.endResetModel()

    def brick_at(self, row):
        return self._bricks[row]

    def destroy_brick(self, row):
        if not 0 <= row < len(self._bricks):
            return

        self._bricks[row]["destroyed"] = True
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, [self.DESTROYED_ROLE])

    def active_brick_rows(self):
        for row, brick in enumerate(self._bricks):
            if not brick["destroyed"]:
                yield row, brick


class ParticleModel(QAbstractListModel):
    """粒子模型 / Particle Model"""

    PARTICLE_X_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    PARTICLE_Y_ROLE = PARTICLE_X_ROLE + 1
    PARTICLE_COLOR_ROLE = PARTICLE_X_ROLE + 2
    PARTICLE_OPACITY_ROLE = PARTICLE_X_ROLE + 3

    ROLE_NAMES = {
        PARTICLE_X_ROLE: b"particleX",
        PARTICLE_Y_ROLE: b"particleY",
        PARTICLE_COLOR_ROLE: b"particleColor",
        PARTICLE_OPACITY_ROLE: b"particleOpacity",
    }

    ROLE_KEYS = {
        PARTICLE_X_ROLE: "x",
        PARTICLE_Y_ROLE: "y",
        PARTICLE_COLOR_ROLE: "color",
        PARTICLE_OPACITY_ROLE: "opacity",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._particles = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._particles)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._particles):
            return None

        key = self.ROLE_KEYS.get(int(role))
        if key is None:
            return None

        return self._particles[index.row()][key]

    def roleNames(self):
        return {
            role: QByteArray(name)
            for role, name in self.ROLE_NAMES.items()
        }

    def clear(self):
        if not self._particles:
            return

        self.beginResetModel()
        self._particles = []
        self.endResetModel()

    def is_empty(self):
        return not self._particles

    def create_explosion(self, x, y, color):
        """创建爆炸粒子 / Create explosion particles."""
        start_row = len(self._particles)
        end_row = start_row + PARTICLE_COUNT - 1
        self.beginInsertRows(QModelIndex(), start_row, end_row)

        for _ in range(PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_MIN_SPEED, PARTICLE_MAX_SPEED)
            self._particles.append({
                "x": x - PARTICLE_RADIUS,
                "y": y - PARTICLE_RADIUS,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "age": 0.0,
                "color": color,
                "opacity": 1.0,
            })

        self.endInsertRows()

    def update_particles(self, delta_time):
        """更新粒子位置和透明度 / Update particle position and opacity."""
        if not self._particles:
            return

        for row in range(len(self._particles) - 1, -1, -1):
            particle = self._particles[row]
            particle["age"] += delta_time

            if particle["age"] >= PARTICLE_LIFETIME:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._particles.pop(row)
                self.endRemoveRows()
                continue

            particle["x"] += particle["vx"] * delta_time
            particle["y"] += particle["vy"] * delta_time
            particle["vy"] += PARTICLE_GRAVITY * delta_time
            particle["opacity"] = max(0.0, 1.0 - particle["age"] / PARTICLE_LIFETIME)

        if self._particles:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._particles) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [
                self.PARTICLE_X_ROLE,
                self.PARTICLE_Y_ROLE,
                self.PARTICLE_OPACITY_ROLE,
            ])


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
        self._message = MESSAGE_START
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
    rotationChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._x = SCREEN_WIDTH / 2
        self._y = qml_ball_start_center_y()
        self._dx = 0
        self._dy = 0
        self._active = False
        self._motion = RainbowBallMotion()
        self._rotation = self._motion.rotation
        self._texture_source = create_rainbow_ball_data_url(BALL_RADIUS)

    @Property(float, notify=positionChanged)
    def x(self):
        return self._x

    @Property(float, notify=positionChanged)
    def y(self):
        return self._y

    @Property(float, notify=rotationChanged)
    def rotation(self):
        return self._rotation

    @Property(str, constant=True)
    def textureSource(self):
        return self._texture_source

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

        self.positionChanged.emit(self._x, self._y)

    def update_rotation(self, delta_time):
        """更新彩虹纹理旋转 / Update rainbow texture rotation."""
        self._rotation = self._motion.update(delta_time)
        self.rotationChanged.emit(self._rotation)

    @Slot(float, float, float, result=bool)
    def checkPaddleCollision(self, paddle_x, paddle_y, paddle_width):
        """检测与挡板碰撞 / Check Paddle Collision"""
        if not self._active:
            return False

        if (self._y + BALL_RADIUS >= paddle_y and
            self._y + BALL_RADIUS <= paddle_y + PADDLE_HEIGHT and
            self._x >= paddle_x and
            self._x <= paddle_x + paddle_width):

            # 计算反弹角度和旋转 / Calculate bounce angle and spin
            hit_pos = (self._x - paddle_x) / paddle_width  # 0.0 到 1.0
            relative_hit = max(-1.0, min(1.0, hit_pos * 2 - 1))
            angle = relative_hit * PADDLE_BOUNCE_MAX_ANGLE
            angle_rad = math.radians(angle)

            speed = math.sqrt(self._dx**2 + self._dy**2)
            self._dx = speed * math.sin(angle_rad)
            self._dy = -abs(speed * math.cos(angle_rad))  # 向上为负
            self._motion.set_spin_from_paddle_hit(relative_hit)
            self._y = paddle_y - BALL_RADIUS
            self.positionChanged.emit(self._x, self._y)

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
        self._y = qml_ball_start_center_y()
        self._dx = 0
        self._dy = 0
        self._active = False
        self._motion.reset()
        self._rotation = self._motion.rotation
        self.positionChanged.emit(self._x, self._y)
        self.rotationChanged.emit(self._rotation)

    @Slot(float, float)
    def followPaddle(self, paddle_x, paddle_width):
        """球跟随挡板移动（游戏未开始时）/ Ball follows paddle"""
        if not self._active:
            self._x = paddle_x + paddle_width / 2
            self._y = qml_ball_start_center_y()
            self.positionChanged.emit(self._x, self._y)


class GameController(QObject):
    """游戏主控制器 / Main Game Controller"""

    paddleXChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = GameState(self)
        self._ball = Ball(self)
        self._brick_model = BrickModel(self)
        self._particle_model = ParticleModel(self)
        self._paddle_x = (SCREEN_WIDTH - PADDLE_WIDTH) / 2
        self._paddle_y = qml_paddle_y()
        self._paddle_width = PADDLE_WIDTH
        self._paddle_move_left = False
        self._paddle_move_right = False

        self._state.brickCount = total_brick_count()

        # 游戏计时器 / Game Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.setInterval(FRAME_INTERVAL_MS)  # ~60 FPS
        self.timer.start()

    @Property(QObject, constant=True)
    def state(self):
        """游戏状态对象"""
        return self._state

    @Property(QObject, constant=True)
    def ball(self):
        """球对象"""
        return self._ball

    @Property(QObject, constant=True)
    def brickModel(self):
        """砖块模型"""
        return self._brick_model

    @Property(float, notify=paddleXChanged)
    def paddleX(self):
        """挡板左上角 X / Paddle left x."""
        return self._paddle_x

    @Property(QObject, constant=True)
    def particleModel(self):
        """粒子模型"""
        return self._particle_model

    @Slot()
    def startGame(self):
        """开始游戏 / Start Game"""
        if self._state.gameStatus == GameStatus.NOT_STARTED:
            self._ball.launch()
            if not self.timer.isActive():
                self.timer.start()
            self._state.message = ""
            self._state.gameStatus = GameStatus.PLAYING

    @Slot()
    def resetGame(self):
        """重置游戏 / Reset Game"""
        self._set_paddle_x((SCREEN_WIDTH - self._paddle_width) / 2, force=True)
        self._paddle_move_left = False
        self._paddle_move_right = False
        self._ball.reset()
        self._brick_model.reset_bricks()
        self._particle_model.clear()
        self._state.score = 0
        self._state.gameStatus = GameStatus.NOT_STARTED
        self._state.message = MESSAGE_START
        
        # 重置砖块计数
        self._state.brickCount = total_brick_count()

    @Slot(float, float, float)
    def updatePaddle(self, paddle_x, paddle_y, paddle_width):
        """更新挡板位置 / Update paddle position."""
        self._paddle_y = paddle_y
        self._paddle_width = paddle_width
        self._set_paddle_x(paddle_x)

    @Slot(float)
    def setPaddleX(self, paddle_x):
        """设置挡板左上角 X / Set paddle left x."""
        self._set_paddle_x(paddle_x)

    @Slot(bool)
    def setPaddleMovingLeft(self, moving):
        """设置挡板是否向左移动 / Set whether paddle moves left."""
        self._paddle_move_left = moving

    @Slot(bool)
    def setPaddleMovingRight(self, moving):
        """设置挡板是否向右移动 / Set whether paddle moves right."""
        self._paddle_move_right = moving

    def _set_paddle_x(self, paddle_x, force=False):
        """更新挡板位置并同步等待发射的小球 / Update paddle and waiting ball."""
        clamped_x = max(0, min(SCREEN_WIDTH - self._paddle_width, paddle_x))
        if force or clamped_x != self._paddle_x:
            self._paddle_x = clamped_x
            self.paddleXChanged.emit(self._paddle_x)

            if self._state.gameStatus == GameStatus.NOT_STARTED:
                self._ball.followPaddle(self._paddle_x, self._paddle_width)

            return True

        return False

    def _update_paddle(self, delta_time):
        """按当前方向状态更新挡板 / Update paddle from current direction state."""
        next_x = self._paddle_x

        if self._paddle_move_left:
            next_x -= PADDLE_SPEED * delta_time
        if self._paddle_move_right:
            next_x += PADDLE_SPEED * delta_time

        if next_x != self._paddle_x:
            self._set_paddle_x(next_x)

    def _check_brick_collisions(self):
        """检测所有砖块碰撞 / Check all brick collisions."""
        if self._state.gameStatus != GameStatus.PLAYING:
            return False

        for row, brick in self._brick_model.active_brick_rows():
            if self._check_single_brick_collision(brick):
                self._brick_model.destroy_brick(row)
                self._state.score += SCORE_PER_BRICK
                self._state.brickCount -= 1

                self._particle_model.create_explosion(
                    brick["x"] + brick["width"] / 2,
                    brick["y"] + brick["height"] / 2,
                    brick["color"]
                )

                if self._state.brickCount <= 0:
                    self._state.gameStatus = GameStatus.VICTORY
                    self._state.message = MESSAGE_VICTORY

                return True

        return False

    def _check_single_brick_collision(self, brick):
        """检测单个砖块并处理反弹 / Check one brick and bounce the ball."""
        ball_x = self._ball.x
        ball_y = self._ball.y
        brick_x = brick["x"]
        brick_y = brick["y"]
        brick_width = brick["width"]
        brick_height = brick["height"]

        closest_x = max(brick_x, min(ball_x, brick_x + brick_width))
        closest_y = max(brick_y, min(ball_y, brick_y + brick_height))
        distance = math.sqrt((ball_x - closest_x)**2 + (ball_y - closest_y)**2)

        if distance >= BALL_RADIUS:
            return False

        brick_center_x = brick_x + brick_width / 2
        brick_center_y = brick_y + brick_height / 2
        dx = ball_x - brick_center_x
        dy = ball_y - brick_center_y
        overlap_x = brick_width / 2 + BALL_RADIUS - abs(dx)
        overlap_y = brick_height / 2 + BALL_RADIUS - abs(dy)

        if overlap_x < overlap_y:
            self._ball._dx = -self._ball._dx
            if dx > 0:
                self._ball._x = brick_center_x + brick_width / 2 + BALL_RADIUS
            else:
                self._ball._x = brick_center_x - brick_width / 2 - BALL_RADIUS
        else:
            self._ball._dy = -self._ball._dy
            if dy > 0:
                self._ball._y = brick_center_y + brick_height / 2 + BALL_RADIUS
            else:
                self._ball._y = brick_center_y - brick_height / 2 - BALL_RADIUS

        self._ball.positionChanged.emit(self._ball.x, self._ball.y)
        return True

    def _update(self):
        """游戏主循环 / Main Game Loop"""
        self._ball.update_rotation(FIXED_DELTA_TIME)
        self._update_paddle(FIXED_DELTA_TIME)

        if self._state.gameStatus == GameStatus.PLAYING:
            self._ball.update(FIXED_DELTA_TIME)  # 约 60 FPS
            self._ball.checkPaddleCollision(
                self._paddle_x,
                self._paddle_y,
                self._paddle_width
            )
            self._check_brick_collisions()

            # 检测掉落 / Check if Ball Fell
            if self._ball.isOutOfBounds():
                self._state.gameStatus = GameStatus.GAME_OVER
                self._state.message = MESSAGE_GAME_OVER

        self._particle_model.update_particles(FIXED_DELTA_TIME)
