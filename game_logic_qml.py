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
from fireball_effect import inside_fireball_impact_area
from paddle_texture import create_paddle_sprite_sheet_data_url
from reward_visual import (
    choose_reward_type,
    create_reward_data_url,
    create_reward_motion,
)

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

    def active_rows_in_fireball_path(self, source_row, direction_x, direction_y):
        """返回撞击砖块运动方向一侧的 2x2 局部砖块 / Return the directional local 2x2 area."""
        if not 0 <= source_row < len(self._bricks):
            return []

        if math.hypot(direction_x, direction_y) <= 1e-6:
            return [source_row]

        source = self._bricks[source_row]
        source_center_x = source["x"] + source["width"] / 2
        source_center_y = source["y"] + source["height"] / 2
        candidates = []

        for row, brick in enumerate(self._bricks):
            if row == source_row or brick["destroyed"]:
                continue

            brick_center_x = brick["x"] + brick["width"] / 2
            brick_center_y = brick["y"] + brick["height"] / 2
            offset_x = brick_center_x - source_center_x
            offset_y = brick_center_y - source_center_y
            if inside_fireball_impact_area(
                offset_x,
                offset_y,
                direction_x,
                direction_y,
            ):
                candidates.append((offset_x * offset_x + offset_y * offset_y, row))

        candidates.sort(key=lambda item: item[0])
        return [
            source_row,
            *[row for _, row in candidates[:3]],
        ]


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
                "lifetime": PARTICLE_LIFETIME,
                "gravity": PARTICLE_GRAVITY,
                "color": color,
                "opacity": 1.0,
            })

        self.endInsertRows()

    def create_fireball_trail(self, x, y):
        """创建火球尾焰粒子 / Create fireball trail particles."""
        start_row = len(self._particles)
        end_row = start_row + FIREBALL_TRAIL_PARTICLE_COUNT - 1
        self.beginInsertRows(QModelIndex(), start_row, end_row)

        for _ in range(FIREBALL_TRAIL_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(FIREBALL_TRAIL_MIN_SPEED, FIREBALL_TRAIL_MAX_SPEED)
            self._particles.append({
                "x": x - FIREBALL_TRAIL_PARTICLE_RADIUS + random.uniform(-BALL_RADIUS / 2, BALL_RADIUS / 2),
                "y": y - FIREBALL_TRAIL_PARTICLE_RADIUS + random.uniform(-BALL_RADIUS / 2, BALL_RADIUS / 2),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "age": 0.0,
                "lifetime": FIREBALL_TRAIL_PARTICLE_LIFETIME,
                "gravity": FIREBALL_TRAIL_GRAVITY,
                "color": random.choice(FIREBALL_TRAIL_COLORS_HEX),
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
            lifetime = particle.get("lifetime", PARTICLE_LIFETIME)

            if particle["age"] >= lifetime:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._particles.pop(row)
                self.endRemoveRows()
                continue

            particle["x"] += particle["vx"] * delta_time
            particle["y"] += particle["vy"] * delta_time
            particle["vy"] += particle.get("gravity", PARTICLE_GRAVITY) * delta_time
            particle["opacity"] = max(0.0, 1.0 - particle["age"] / lifetime)

        if self._particles:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._particles) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [
                self.PARTICLE_X_ROLE,
                self.PARTICLE_Y_ROLE,
                self.PARTICLE_OPACITY_ROLE,
            ])


class RewardModel(QAbstractListModel):
    """奖励物件模型 / Reward object model."""

    REWARD_X_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    REWARD_Y_ROLE = REWARD_X_ROLE + 1
    REWARD_SIZE_ROLE = REWARD_X_ROLE + 2
    REWARD_TEXTURE_ROLE = REWARD_X_ROLE + 3
    REWARD_ROTATION_ROLE = REWARD_X_ROLE + 4

    ROLE_NAMES = {
        REWARD_X_ROLE: b"rewardX",
        REWARD_Y_ROLE: b"rewardY",
        REWARD_SIZE_ROLE: b"rewardSize",
        REWARD_TEXTURE_ROLE: b"rewardTexture",
        REWARD_ROTATION_ROLE: b"rewardRotation",
    }

    ROLE_KEYS = {
        REWARD_X_ROLE: "x",
        REWARD_Y_ROLE: "y",
        REWARD_SIZE_ROLE: "size",
        REWARD_TEXTURE_ROLE: "texture",
        REWARD_ROTATION_ROLE: "rotation",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rewards = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._rewards)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rewards):
            return None

        key = self.ROLE_KEYS.get(int(role))
        if key is None:
            return None

        return self._rewards[index.row()][key]

    def roleNames(self):
        return {
            role: QByteArray(name)
            for role, name in self.ROLE_NAMES.items()
        }

    def clear(self):
        if not self._rewards:
            return

        self.beginResetModel()
        self._rewards = []
        self.endResetModel()

    def create_reward(self, reward_type, center_x, center_y, source_dx=0):
        """创建指定类型的奖励 / Create a reward of the selected type."""
        motion = create_reward_motion(source_dx)
        row = len(self._rewards)
        self.beginInsertRows(QModelIndex(), row, row)
        self._rewards.append({
            "type": reward_type,
            "x": center_x - REWARD_RADIUS,
            "y": center_y - REWARD_RADIUS,
            "vx": motion.vx,
            "vy": -motion.upward_speed,
            "gravity": motion.gravity,
            "rotation": motion.angle,
            "angularVelocity": motion.angular_velocity,
            "size": REWARD_SIZE,
            "texture": create_reward_data_url(reward_type),
        })
        self.endInsertRows()

    def create_fireball_reward(self, center_x, center_y, source_dx=0):
        """Compatibility wrapper for creating a fireball reward."""
        self.create_reward(REWARD_TYPE_FIREBALL, center_x, center_y, source_dx)

    def update_rewards(self, delta_time, paddle_x, paddle_y, paddle_width):
        """更新奖励位置，并返回接取的奖励类型 / Update rewards and return collected types."""
        collected_types = []
        if not self._rewards:
            return collected_types

        for row in range(len(self._rewards) - 1, -1, -1):
            reward = self._rewards[row]
            reward["x"] += reward["vx"] * delta_time
            reward["y"] += reward["vy"] * delta_time
            reward["vy"] += reward["gravity"] * delta_time
            reward["rotation"] = (
                reward["rotation"] + reward["angularVelocity"] * delta_time
            ) % 360

            if reward["x"] <= 0:
                reward["x"] = 0
                reward["vx"] = abs(reward["vx"])
            elif reward["x"] + reward["size"] >= SCREEN_WIDTH:
                reward["x"] = SCREEN_WIDTH - reward["size"]
                reward["vx"] = -abs(reward["vx"])

            if self._collides_with_paddle(reward, paddle_x, paddle_y, paddle_width):
                collected_types.append(reward["type"])
                self._remove_reward(row)
            elif reward["y"] > paddle_y + PADDLE_HEIGHT:
                self._remove_reward(row)

        if self._rewards:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._rewards) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [
                self.REWARD_X_ROLE,
                self.REWARD_Y_ROLE,
                self.REWARD_ROTATION_ROLE,
            ])

        return collected_types

    def _collides_with_paddle(self, reward, paddle_x, paddle_y, paddle_width):
        reward_right = reward["x"] + reward["size"]
        reward_bottom = reward["y"] + reward["size"]
        return (
            reward_right >= paddle_x and
            reward["x"] <= paddle_x + paddle_width and
            reward_bottom >= paddle_y and
            reward["y"] <= paddle_y + PADDLE_HEIGHT
        )

    def _remove_reward(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self._rewards.pop(row)
        self.endRemoveRows()


class LaserModel(QAbstractListModel):
    """激光子弹模型 / Laser bullet model."""

    BULLET_X_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    BULLET_Y_ROLE = BULLET_X_ROLE + 1
    BULLET_WIDTH_ROLE = BULLET_X_ROLE + 2
    BULLET_HEIGHT_ROLE = BULLET_X_ROLE + 3

    ROLE_NAMES = {
        BULLET_X_ROLE: b"bulletX",
        BULLET_Y_ROLE: b"bulletY",
        BULLET_WIDTH_ROLE: b"bulletWidth",
        BULLET_HEIGHT_ROLE: b"bulletHeight",
    }
    ROLE_KEYS = {
        BULLET_X_ROLE: "x",
        BULLET_Y_ROLE: "y",
        BULLET_WIDTH_ROLE: "width",
        BULLET_HEIGHT_ROLE: "height",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bullets = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._bullets)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._bullets):
            return None
        key = self.ROLE_KEYS.get(int(role))
        return self._bullets[index.row()].get(key) if key else None

    def roleNames(self):
        return {role: QByteArray(name) for role, name in self.ROLE_NAMES.items()}

    def clear(self):
        if not self._bullets:
            return
        self.beginResetModel()
        self._bullets = []
        self.endResetModel()

    def fire(self, paddle_x, paddle_y, paddle_width):
        """从挡板两侧各发射一枚子弹 / Fire one bullet from each paddle gun."""
        centers = (
            paddle_x + LASER_GUN_SIDE_INSET + LASER_GUN_WIDTH / 2,
            paddle_x + paddle_width - LASER_GUN_SIDE_INSET - LASER_GUN_WIDTH / 2,
        )
        start_row = len(self._bullets)
        self.beginInsertRows(QModelIndex(), start_row, start_row + 1)
        for center_x in centers:
            self._bullets.append({
                "x": center_x - LASER_BULLET_WIDTH / 2,
                "y": paddle_y - LASER_BULLET_HEIGHT,
                "width": LASER_BULLET_WIDTH,
                "height": LASER_BULLET_HEIGHT,
            })
        self.endInsertRows()

    def update_bullets(self, delta_time):
        for bullet in self._bullets:
            bullet["y"] -= LASER_BULLET_SPEED * delta_time

        if self._bullets:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._bullets) - 1, 0),
                [self.BULLET_Y_ROLE],
            )

    def remove_bullet(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self._bullets.pop(row)
        self.endRemoveRows()


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
        self._fireball_active = False
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
        self._fireball_active = False
        self._motion.reset()
        self._rotation = self._motion.rotation
        self.positionChanged.emit(self._x, self._y)
        self.rotationChanged.emit(self._rotation)

    def activate_fireball(self):
        """激活火球效果 / Activate fireball effect."""
        self._fireball_active = True

    def deactivate_fireball(self):
        """清除火球效果 / Clear fireball effect."""
        self._fireball_active = False

    @property
    def fireball_active(self):
        return self._fireball_active

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
    paddleWidthChanged = Signal(float)
    laserActiveChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = GameState(self)
        self._ball = Ball(self)
        self._brick_model = BrickModel(self)
        self._particle_model = ParticleModel(self)
        self._reward_model = RewardModel(self)
        self._laser_model = LaserModel(self)
        self._paddle_x = (SCREEN_WIDTH - PADDLE_WIDTH) / 2
        self._paddle_y = qml_paddle_y()
        self._paddle_width = PADDLE_WIDTH
        self._paddle_move_left = False
        self._paddle_move_right = False
        self._laser_active = False

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

    @Property(float, notify=paddleWidthChanged)
    def paddleWidth(self):
        """当前挡板宽度 / Current paddle width."""
        return self._paddle_width

    @Property(str, notify=paddleWidthChanged)
    def paddleTextureSource(self):
        """当前宽度对应的固定牙齿挡板图集 / Width-specific paddle atlas."""
        return create_paddle_sprite_sheet_data_url(
            self._paddle_width,
            PADDLE_HEIGHT,
            PADDLE_CORNER_RADIUS,
            PADDLE_GRADIENT_FRAME_COUNT,
        )

    @Property(QObject, constant=True)
    def particleModel(self):
        """粒子模型"""
        return self._particle_model

    @Property(QObject, constant=True)
    def rewardModel(self):
        """奖励物件模型"""
        return self._reward_model

    @Property(QObject, constant=True)
    def laserModel(self):
        return self._laser_model

    @Property(bool, notify=laserActiveChanged)
    def laserActive(self):
        return self._laser_active

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
    def handleSpace(self):
        """空格键统一处理开始、暂停、继续和重开 / Handle the full SPACE state machine."""
        status = self._state.gameStatus
        if status == GameStatus.NOT_STARTED:
            self.startGame()
        elif status == GameStatus.PLAYING:
            self._paddle_move_left = False
            self._paddle_move_right = False
            self._state.message = MESSAGE_PAUSED
            self._state.gameStatus = GameStatus.PAUSED
        elif status == GameStatus.PAUSED:
            self._state.message = ""
            self._state.gameStatus = GameStatus.PLAYING
        elif status in (GameStatus.GAME_OVER, GameStatus.VICTORY):
            self.resetGame()
            self.startGame()

    @Slot()
    def resetGame(self):
        """重置游戏 / Reset Game"""
        self._set_paddle_width(PADDLE_WIDTH)
        self._set_paddle_x((SCREEN_WIDTH - PADDLE_WIDTH) / 2, force=True)
        self._paddle_move_left = False
        self._paddle_move_right = False
        self._ball.reset()
        self._brick_model.reset_bricks()
        self._particle_model.clear()
        self._reward_model.clear()
        self._laser_model.clear()
        self._set_laser_active(False)
        self._state.score = 0
        self._state.gameStatus = GameStatus.NOT_STARTED
        self._state.message = MESSAGE_START
        
        # 重置砖块计数
        self._state.brickCount = total_brick_count()

    @Slot(float, float, float)
    def updatePaddle(self, paddle_x, paddle_y, paddle_width):
        """更新挡板位置 / Update paddle position."""
        self._paddle_y = paddle_y
        self._set_paddle_width(paddle_width)
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

    def _set_paddle_width(self, paddle_width):
        """调整挡板宽度并保持中心位置 / Resize the paddle around its center."""
        new_width = max(PADDLE_MIN_WIDTH, min(PADDLE_MAX_WIDTH, paddle_width))
        if new_width == self._paddle_width:
            return False

        center_x = self._paddle_x + self._paddle_width / 2
        self._paddle_width = new_width
        self.paddleWidthChanged.emit(self._paddle_width)
        self._set_paddle_x(center_x - self._paddle_width / 2, force=True)
        return True

    def _apply_reward(self, reward_type):
        """应用接取的奖励 / Apply a collected reward."""
        if reward_type == REWARD_TYPE_FIREBALL:
            self._ball.activate_fireball()
        elif reward_type == REWARD_TYPE_EXTEND_PADDLE:
            self._set_paddle_width(self._paddle_width + PADDLE_REWARD_SIZE_STEP)
        elif reward_type == REWARD_TYPE_SHRINK_PADDLE:
            self._set_paddle_width(self._paddle_width - PADDLE_REWARD_SIZE_STEP)
        elif reward_type == REWARD_TYPE_RESET:
            self._reset_active_rewards()
        elif reward_type == REWARD_TYPE_LASER:
            self._set_laser_active(True)
        elif reward_type == REWARD_TYPE_SKULL:
            self._state.gameStatus = GameStatus.GAME_OVER
            self._state.message = MESSAGE_GAME_OVER
            self._set_laser_active(False)

    def _set_laser_active(self, active):
        if self._laser_active == active:
            return
        self._laser_active = active
        self.laserActiveChanged.emit(active)
        if not active:
            self._laser_model.clear()

    def _reset_active_rewards(self):
        """清除所有已接取并持续生效的奖励 / Reset all active collected rewards."""
        self._ball.deactivate_fireball()
        self._set_laser_active(False)
        self._set_paddle_width(PADDLE_WIDTH)

    @Slot()
    def fireLaser(self):
        if self._laser_active and self._state.gameStatus == GameStatus.PLAYING:
            self._laser_model.fire(self._paddle_x, self._paddle_y, self._paddle_width)

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
            incoming_dx = self._ball._dx
            incoming_dy = self._ball._dy

            if self._check_single_brick_collision(brick):
                self._destroy_brick_group(row, incoming_dx, incoming_dy)
                return True

        return False

    def _update_lasers(self, delta_time):
        """推进子弹并消除首个命中的砖块 / Advance bullets and destroy first hits."""
        self._laser_model.update_bullets(delta_time)
        for bullet_row in range(len(self._laser_model._bullets) - 1, -1, -1):
            bullet = self._laser_model._bullets[bullet_row]
            hit_row = None
            for brick_row, brick in self._brick_model.active_brick_rows():
                if (
                    bullet["x"] + bullet["width"] >= brick["x"]
                    and bullet["x"] <= brick["x"] + brick["width"]
                    and bullet["y"] + bullet["height"] >= brick["y"]
                    and bullet["y"] <= brick["y"] + brick["height"]
                ):
                    hit_row = brick_row
                    break

            if hit_row is not None:
                self._destroy_laser_brick(hit_row)
                self._laser_model.remove_bullet(bullet_row)
            elif bullet["y"] + bullet["height"] < 0:
                self._laser_model.remove_bullet(bullet_row)

    def _destroy_laser_brick(self, row):
        brick = self._brick_model.brick_at(row)
        if brick["destroyed"]:
            return
        center_x = brick["x"] + brick["width"] / 2
        center_y = brick["y"] + brick["height"] / 2
        self._brick_model.destroy_brick(row)
        self._state.score += SCORE_PER_BRICK
        self._state.brickCount -= 1
        self._particle_model.create_explosion(center_x, center_y, brick["color"])
        reward_type = choose_reward_type()
        if reward_type is not None:
            self._reward_model.create_reward(reward_type, center_x, center_y, 0)
        if self._state.brickCount <= 0:
            self._state.gameStatus = GameStatus.VICTORY
            self._state.message = MESSAGE_VICTORY

    def _destroy_brick_group(self, hit_row, direction_x=0, direction_y=0):
        """销毁命中砖块，火球状态下沿运动方向额外销毁砖块 / Destroy fireball path."""
        if self._ball.fireball_active:
            rows_to_destroy = self._brick_model.active_rows_in_fireball_path(hit_row, direction_x, direction_y)
        else:
            rows_to_destroy = [hit_row]

        for row in rows_to_destroy:
            brick = self._brick_model.brick_at(row)
            if brick["destroyed"]:
                continue

            center_x = brick["x"] + brick["width"] / 2
            center_y = brick["y"] + brick["height"] / 2
            self._brick_model.destroy_brick(row)
            self._state.score += SCORE_PER_BRICK
            self._state.brickCount -= 1

            self._particle_model.create_explosion(center_x, center_y, brick["color"])
            reward_type = choose_reward_type()
            if reward_type is not None:
                self._reward_model.create_reward(reward_type, center_x, center_y, direction_x)

        if self._state.brickCount <= 0:
            self._state.gameStatus = GameStatus.VICTORY
            self._state.message = MESSAGE_VICTORY

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
        if self._state.gameStatus == GameStatus.PAUSED:
            return

        self._ball.update_rotation(FIXED_DELTA_TIME)
        self._update_paddle(FIXED_DELTA_TIME)

        if self._state.gameStatus == GameStatus.PLAYING:
            for reward_type in self._reward_model.update_rewards(
                FIXED_DELTA_TIME,
                self._paddle_x,
                self._paddle_y,
                self._paddle_width,
            ):
                self._apply_reward(reward_type)
                if self._state.gameStatus != GameStatus.PLAYING:
                    break

            if self._state.gameStatus != GameStatus.PLAYING:
                self._particle_model.update_particles(FIXED_DELTA_TIME)
                return

            self._update_lasers(FIXED_DELTA_TIME)

            self._ball.update(FIXED_DELTA_TIME)  # 约 60 FPS
            self._ball.checkPaddleCollision(
                self._paddle_x,
                self._paddle_y,
                self._paddle_width
            )
            self._check_brick_collisions()

            if self._ball.fireball_active:
                self._particle_model.create_fireball_trail(self._ball.x, self._ball.y)

            # 检测掉落 / Check if Ball Fell
            if self._ball.isOutOfBounds():
                self._state.gameStatus = GameStatus.GAME_OVER
                self._state.message = MESSAGE_GAME_OVER

        self._particle_model.update_particles(FIXED_DELTA_TIME)
