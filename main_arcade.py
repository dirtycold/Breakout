"""
DX-Ball 克隆游戏 - 主程序
DX-Ball Clone Game - Main Program

简单的打砖块游戏，适合小朋友学习
Simple brick-breaker game for kids to learn
"""

import ctypes
import math
import random
import sys
import types


def _force_missing_gstreamer_when_gi_is_incomplete():
    """Make pyglet treat an incomplete gi namespace as unavailable."""
    if not sys.platform.startswith("linux"):
        return

    try:
        import gi
    except ImportError:
        return

    if hasattr(gi, "require_version"):
        return

    missing_gi = types.ModuleType("gi")

    def require_version(*_args, **_kwargs):
        raise ImportError("PyGObject is unavailable")

    missing_gi.require_version = require_version
    sys.modules["gi"] = missing_gi


_force_missing_gstreamer_when_gi_is_incomplete()

import arcade


def _patch_pyglet_fontconfig_memory_faces():
    """Avoid a fontconfig crash when Pyglet queries memory-backed faces."""
    if not sys.platform.startswith("linux"):
        return

    try:
        import pyglet.font.fontconfig as pyglet_fontconfig
    except Exception:
        return

    style_from_face = pyglet_fontconfig.FontConfig.style_from_face
    if getattr(style_from_face, "_breakout_safe", False):
        return

    def safe_style_from_face(self, font_face):
        blank = ctypes.c_int()
        pattern = self._fontconfig.FcFreeTypeQueryFace(
            font_face,
            b":pyglet-memory:",
            0,
            ctypes.byref(blank),
        )
        if not pattern:
            return "normal", False, "normal"

        result = pyglet_fontconfig.FontConfigSearchResult(self._fontconfig, pattern)
        return result.weight, result.italic, result.stretch

    safe_style_from_face._breakout_safe = True
    pyglet_fontconfig.FontConfig.style_from_face = safe_style_from_face


_patch_pyglet_fontconfig_memory_faces()

from PIL import Image, ImageDraw
from ball_texture import RainbowBallMotion, create_rainbow_ball_image
from constants import *
from fireball_effect import inside_fireball_impact_area
from magnet_visual import create_magnet_effect_frames
from paddle_texture import create_paddle_image
from reward_visual import (
    choose_reward_type,
    create_reward_image,
    create_reward_motion,
)


class RainbowBall(arcade.Sprite):
    """彩虹条纹球类 / Rainbow Striped Ball Class"""

    def __init__(self, radius):
        super().__init__()
        self.radius = radius
        self.motion = RainbowBallMotion()
        self.fireball_active = False

        # 创建抗锯齿的圆形纹理
        self._create_rainbow_texture()

    def _create_rainbow_texture(self):
        """创建彩虹条纹纹理 / Create rainbow stripe texture."""
        self.texture = arcade.Texture(
            image=create_rainbow_ball_image(self.radius),
            name=f"rainbow_ball_{id(self)}"
        )

        # 设置碰撞框
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.angle = self.motion.rotation

    def update_animation(self, delta_time=FIXED_DELTA_TIME):
        """更新彩虹纹理旋转 / Update rainbow texture rotation."""
        self.angle = self.motion.update(delta_time)

    def activate_fireball(self):
        """激活火球效果 / Activate fireball effect."""
        self.fireball_active = True

    def deactivate_fireball(self):
        """清除火球效果 / Clear fireball effect."""
        self.fireball_active = False


class RewardSprite(arcade.Sprite):
    """自由落体奖励物件 / Free-falling reward object."""

    def __init__(self, reward_type, center_x, center_y, source_dx=0):
        super().__init__()
        self.texture = arcade.Texture(
            image=create_reward_image(reward_type),
            name=f"{reward_type}_reward_{id(self)}",
        )
        self.width = REWARD_SIZE
        self.height = REWARD_SIZE
        self.reward_type = reward_type
        self.center_x = center_x
        self.center_y = center_y
        motion = create_reward_motion(source_dx)
        self.change_x = motion.vx
        self.change_y = motion.upward_speed
        self.gravity = motion.gravity
        self.angle = motion.angle
        self.angular_velocity = motion.angular_velocity


class MagnetEffectSprite(arcade.Sprite):
    """Animated electric field displayed while the ball is attached."""

    _texture_frames = None

    def __init__(self):
        super().__init__()
        if self.__class__._texture_frames is None:
            self.__class__._texture_frames = [
                arcade.Texture(
                    image=image,
                    name=f"magnet_effect_{frame_index}",
                )
                for frame_index, image in enumerate(create_magnet_effect_frames())
            ]
        self._frame_index = 0
        self._elapsed = 0.0
        self.texture = self._texture_frames[0]
        self.width = MAGNET_EFFECT_WIDTH
        self.height = MAGNET_EFFECT_HEIGHT

    def update_animation(self, delta_time=FIXED_DELTA_TIME):
        self._elapsed += delta_time
        next_frame = int(
            self._elapsed / MAGNET_EFFECT_FRAME_DURATION
        ) % len(self._texture_frames)
        if next_frame != self._frame_index:
            self._frame_index = next_frame
            self.texture = self._texture_frames[next_frame]


class RoundedRectBrick(arcade.Sprite):
    """圆角矩形砖块类 / Rounded Rectangle Brick Class"""

    def __init__(self, width, height, color, radius=BRICK_CORNER_RADIUS):
        super().__init__()
        self.brick_width = width
        self.brick_height = height
        self.brick_color = color  # 保存原始颜色
        self.corner_radius = radius

        # 创建圆角矩形纹理
        self._create_rounded_rect_texture()

    def _create_rounded_rect_texture(self):
        """创建带圆角的矩形纹理 / Create rounded rectangle texture"""
        # 使用更大的尺寸进行超采样，然后缩小以获得更好的抗锯齿效果
        scale = 4  # 4x 超采样
        width = int(self.brick_width * scale)
        height = int(self.brick_height * scale)

        # 创建 PIL 图像
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制圆角矩形（使用缩放后的半径）
        draw.rounded_rectangle(
            [0, 0, width - 1, height - 1],
            radius=self.corner_radius * scale,
            fill=self.brick_color
        )

        # 缩小到实际尺寸（提供抗锯齿效果）
        image = image.resize((int(self.brick_width), int(self.brick_height)), Image.Resampling.LANCZOS)

        # 转换为 Arcade 纹理
        self.texture = arcade.Texture(image=image, name=f"brick_{id(self)}")

        # 设置碰撞框
        self.width = self.brick_width
        self.height = self.brick_height


class RoundedRectPaddle(arcade.Sprite):
    """圆角矩形挡板类 / Rounded Rectangle Paddle Class"""

    _texture_frame_cache = {}

    def __init__(self, width, height, color, radius=PADDLE_CORNER_RADIUS):
        super().__init__()
        self.paddle_width = width
        self.paddle_height = height
        self.paddle_color = color
        self.corner_radius = radius
        self.gradient_offset = 0
        self._frame_index = 0

        # 预渲染挡板动画帧，运行时只切换纹理 / Pre-render frames; swap textures at runtime.
        self._texture_frames = self._get_texture_frames()
        self.texture = self._texture_frames[self._frame_index]
        self.width = self.paddle_width
        self.height = self.paddle_height

    def _get_texture_frames(self):
        """返回缓存的挡板动画帧 / Return cached paddle animation frames."""
        cache_key = (
            self.paddle_width,
            self.paddle_height,
            self.paddle_color,
            self.corner_radius,
            PADDLE_FANG_COUNT,
            PADDLE_FANG_HEIGHT,
            PADDLE_FANG_SIDE_INSET,
            tuple(PADDLE_GRADIENT_COLORS),
            tuple(PADDLE_GRADIENT_STOPS),
            PADDLE_GRADIENT_FRAME_COUNT,
        )

        if cache_key not in self._texture_frame_cache:
            frames = []
            for frame_index in range(PADDLE_GRADIENT_FRAME_COUNT):
                gradient_offset = self.paddle_width * frame_index / PADDLE_GRADIENT_FRAME_COUNT
                frames.append(
                    arcade.Texture(
                        image=create_paddle_image(
                            self.paddle_width,
                            self.paddle_height,
                            self.corner_radius,
                            gradient_offset,
                        ),
                        name=f"paddle_{int(self.paddle_width)}x{int(self.paddle_height)}_{frame_index}"
                    )
                )
            self._texture_frame_cache[cache_key] = frames

        return self._texture_frame_cache[cache_key]

    def update_animation(self, delta_time=FIXED_DELTA_TIME):
        """更新挡板彩虹渐变偏移 / Update paddle rainbow gradient offset."""
        self.gradient_offset = (
            self.gradient_offset + PADDLE_GRADIENT_SCROLL_SPEED * delta_time
        ) % self.paddle_width
        next_frame_index = int(
            self.gradient_offset / self.paddle_width * len(self._texture_frames)
        ) % len(self._texture_frames)

        if next_frame_index != self._frame_index:
            self._frame_index = next_frame_index
            self.texture = self._texture_frames[self._frame_index]

    def set_paddle_width(self, width):
        """Swap to a width-specific atlas while keeping every fang unscaled."""
        if width == self.paddle_width:
            return

        self.paddle_width = width
        self._texture_frames = self._get_texture_frames()
        self._frame_index %= len(self._texture_frames)
        self.texture = self._texture_frames[self._frame_index]
        self.width = self.paddle_width
        self.height = self.paddle_height
        self.sync_hit_box_to_texture()


class BreakoutGame(arcade.Window):
    """主游戏窗口类 / Main Game Window Class"""

    def __init__(self):
        """初始化游戏 / Initialize the game"""
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # 设置背景色 / Set background color
        arcade.set_background_color(COLOR_BACKGROUND)

        # 游戏对象 / Game objects
        self.paddle = None
        self.paddle_list = None
        self.ball = None
        self.ball_list = None
        self.brick_list = None
        self.particle_list = None
        self.reward_list = None
        self.laser_bullet_list = None
        self.laser_gun_list = None
        self.magnet_effect_list = None
        self.magnet_effect = None
        self.laser_active = False
        self.magnet_active = False
        self.magnet_attached = False
        self.magnet_offset = 0.0
        self.magnet_speed = BALL_SPEED

        # 移动标志 / Movement flags
        self.left_pressed = False
        self.right_pressed = False
        self.space_pressed = False

        # 游戏状态 / Game state
        self.score = 0
        self.game_status = GameStatus.NOT_STARTED

    def setup(self):
        """设置游戏（开始或重置）/ Set up the game (start or reset)"""

        # 创建挡板 / Create paddle
        self.paddle_list = arcade.SpriteList()
        self.paddle = RoundedRectPaddle(PADDLE_WIDTH, PADDLE_HEIGHT, COLOR_PADDLE, radius=PADDLE_CORNER_RADIUS)
        self.paddle.center_x = SCREEN_WIDTH / 2
        self.paddle.center_y = PADDLE_Y_POSITION
        self.paddle_list.append(self.paddle)

        # 创建球 / Create ball
        self.ball_list = arcade.SpriteList()
        self.ball = RainbowBall(BALL_RADIUS)
        self.ball.center_x = SCREEN_WIDTH / 2
        self.ball.center_y = arcade_ball_start_center_y()
        self.ball_list.append(self.ball)

        # 设置球的初始速度为0（等待开始）/ Set initial ball velocity to 0 (waiting to start)
        self.ball.change_x = 0
        self.ball.change_y = 0

        # 创建砖块列表 / Create brick list
        self.brick_list = arcade.SpriteList()

        # 生成菱形砖块布局 / Generate diamond-shaped brick layout
        for row in range(BRICK_ROWS):
            # 计算这一行应该有多少砖块（菱形效果）
            row_brick_count = bricks_in_row(row)

            for column in range(row_brick_count):
                # 选择颜色（根据行数）/ Choose color based on row
                color = BRICK_COLORS[row % len(BRICK_COLORS)]

                # 创建圆角砖块 / Create rounded brick
                brick = RoundedRectBrick(BRICK_WIDTH, BRICK_HEIGHT, color, radius=BRICK_CORNER_RADIUS)

                # 设置位置（菱形布局）/ Set position (diamond layout)
                brick.center_x = arcade_brick_center_x(row, column)
                brick.center_y = arcade_brick_center_y(row)

                # 添加到列表 / Add to list
                self.brick_list.append(brick)

        # 重置粒子效果 / Reset particle effects
        self.particle_list = arcade.SpriteList()
        self.reward_list = arcade.SpriteList()
        self.laser_bullet_list = arcade.SpriteList()
        self.laser_gun_list = arcade.SpriteList()
        self.magnet_effect_list = arcade.SpriteList()
        self.magnet_effect = MagnetEffectSprite()
        self.magnet_effect_list.append(self.magnet_effect)
        for _ in range(2):
            self.laser_gun_list.append(arcade.SpriteSolidColor(
                LASER_GUN_WIDTH,
                LASER_GUN_HEIGHT,
                color=LASER_GUN_COLOR,
            ))
        self.laser_active = False
        self.magnet_active = False
        self.magnet_attached = False
        self.magnet_offset = 0.0
        self.magnet_speed = BALL_SPEED
        self.update_laser_guns()
        self.update_magnet_effect()

        # 重置游戏状态 / Reset game state
        self.score = 0
        self.game_status = GameStatus.NOT_STARTED
        self.left_pressed = False
        self.right_pressed = False

    def on_draw(self):
        """绘制游戏画面 / Draw the game screen"""
        self.clear()

        # 绘制砖块 / Draw bricks
        self.brick_list.draw()

        # 绘制挡板 / Draw paddle
        self.paddle_list.draw()
        if self.laser_active:
            self.laser_gun_list.draw()
        if self.magnet_attached:
            self.magnet_effect_list.draw()
        self.laser_bullet_list.draw()

        # 绘制奖励物件 / Draw rewards
        self.reward_list.draw()

        # 绘制球 / Draw ball
        self.ball_list.draw()

        # 绘制粒子效果 / Draw particle effects
        self.particle_list.draw()

        # 绘制分数 / Draw score
        arcade.draw_text(
            f"{SCORE_LABEL}: {self.score}",
            SCORE_MARGIN_X, SCREEN_HEIGHT - SCORE_MARGIN_TOP - SCORE_FONT_SIZE,
            arcade.color.WHITE,
            SCORE_FONT_SIZE,
            font_name=GAME_FONT_FAMILIES,
        )

        # 如果游戏未开始，显示开始提示 / Show start message if game hasn't started
        if self.game_status == GameStatus.NOT_STARTED:
            arcade.draw_text(
                MESSAGE_START_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_START_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_START_LINES[2],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                arcade.color.WHITE,
                MESSAGE_HINT_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )

        # 如果游戏结束，显示提示 / Show game over message
        if self.game_status == GameStatus.GAME_OVER:
            arcade.draw_text(
                MESSAGE_GAME_OVER_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_GAME_OVER_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )

        # 如果胜利，显示提示 / Show victory message
        if self.game_status == GameStatus.VICTORY:
            arcade.draw_text(
                MESSAGE_VICTORY_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_VICTORY_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center"
            )

        if self.game_status == GameStatus.PAUSED:
            arcade.draw_text(
                MESSAGE_PAUSED_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center",
            )
            arcade.draw_text(
                MESSAGE_PAUSED_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                font_name=GAME_FONT_FAMILIES,
                anchor_x="center",
            )

    def on_update(self, delta_time):
        """更新游戏逻辑 / Update game logic"""
        if self.game_status == GameStatus.PAUSED:
            return

        self.paddle.update_animation(delta_time)

        if self.game_status in (GameStatus.GAME_OVER, GameStatus.VICTORY):
            # 只更新动画和粒子效果 / Only update animation and particle effects
            self.ball.update_animation(delta_time)
            self.update_particles(delta_time)
            return

        # 如果游戏未开始，只允许移动挡板 / If game hasn't started, only allow paddle movement
        if self.game_status == GameStatus.NOT_STARTED:
            # 更新挡板位置 / Update paddle position
            if self.left_pressed:
                self.paddle.center_x -= PADDLE_SPEED * delta_time
            if self.right_pressed:
                self.paddle.center_x += PADDLE_SPEED * delta_time

            # 限制挡板在屏幕内 / Keep paddle on screen
            self.clamp_paddle_to_screen()

            # 球跟随挡板移动 / Ball follows paddle
            self.ball.center_x = self.paddle.center_x
            self.ball.update_animation(delta_time)
            return

        # 更新挡板位置 / Update paddle position
        if self.left_pressed:
            self.paddle.center_x -= PADDLE_SPEED * delta_time
        if self.right_pressed:
            self.paddle.center_x += PADDLE_SPEED * delta_time

        # 限制挡板在屏幕内 / Keep paddle on screen
        self.clamp_paddle_to_screen()
        self.update_attached_ball()

        self.update_rewards(delta_time)
        if self.game_status != GameStatus.PLAYING:
            self.update_particles(delta_time)
            return

        self.update_lasers(delta_time)

        if self.magnet_attached:
            self.update_attached_ball()
            self.magnet_effect.update_animation(delta_time)
            self.ball.update_animation(delta_time)
            self.update_particles(delta_time)
            return

        # 更新球的位置 / Update ball position
        self.ball.center_x += self.ball.change_x * delta_time
        self.ball.center_y += self.ball.change_y * delta_time

        # 球与左右墙壁碰撞 / Ball collision with left/right walls
        if self.ball.center_x < BALL_RADIUS:
            self.ball.center_x = BALL_RADIUS
            self.ball.change_x = abs(self.ball.change_x)
        elif self.ball.center_x > SCREEN_WIDTH - BALL_RADIUS:
            self.ball.center_x = SCREEN_WIDTH - BALL_RADIUS
            self.ball.change_x = -abs(self.ball.change_x)

        # 球与顶部碰撞 / Ball collision with top wall
        if self.ball.center_y > SCREEN_HEIGHT - BALL_RADIUS:
            self.ball.center_y = SCREEN_HEIGHT - BALL_RADIUS
            self.ball.change_y = -abs(self.ball.change_y)

        # 球掉落（游戏结束）/ Ball falls (game over)
        if self.ball.center_y - BALL_RADIUS <= 0:
            self.game_status = GameStatus.GAME_OVER
            return

        # 球与挡板碰撞 / Ball collision with paddle
        if arcade.check_for_collision(self.ball, self.paddle):
            if self.magnet_active and self.ball.change_y < 0:
                self.attach_ball_to_magnet()
            else:
                # 计算击中挡板的相对位置和旋转 / Calculate relative hit position and spin
                relative_hit = (self.ball.center_x - self.paddle.center_x) / (self.paddle.width / 2)
                relative_hit = max(-1, min(1, relative_hit))  # 限制在 -1 到 1 之间

                # 根据击中位置调整反弹角度 / Adjust bounce angle based on hit position
                angle = relative_hit * PADDLE_BOUNCE_MAX_ANGLE
                angle_rad = math.radians(angle)

                speed = math.sqrt(self.ball.change_x**2 + self.ball.change_y**2)
                self.ball.change_x = speed * math.sin(angle_rad)
                self.ball.change_y = abs(speed * math.cos(angle_rad))  # 确保向上
                self.ball.motion.set_spin_from_paddle_hit(relative_hit)

                # 确保球在挡板上方 / Ensure ball is above paddle
                self.ball.center_y = self.paddle.center_y + PADDLE_HEIGHT / 2 + BALL_RADIUS

        # 球与砖块碰撞 / Ball collision with bricks
        hit_bricks = arcade.check_for_collision_with_list(self.ball, self.brick_list)

        for brick in hit_bricks:
            incoming_dx = self.ball.change_x
            incoming_dy = self.ball.change_y

            # 计算球心与砖块中心的相对位置 / Calculate ball center relative to brick center
            dx = self.ball.center_x - brick.center_x
            dy = self.ball.center_y - brick.center_y

            # 计算砖块的半宽和半高 / Calculate brick half-width and half-height
            brick_half_width = BRICK_WIDTH / 2
            brick_half_height = BRICK_HEIGHT / 2

            # 判断碰撞是从哪个方向发生的 / Determine collision direction
            # 使用重叠量来判断 / Use overlap to determine
            overlap_x = brick_half_width + BALL_RADIUS - abs(dx)
            overlap_y = brick_half_height + BALL_RADIUS - abs(dy)

            # 如果X方向重叠更小，说明是左右碰撞 / If X overlap is smaller, it's a side collision
            if overlap_x < overlap_y:
                # 左右碰撞 / Side collision
                self.ball.change_x *= -1
                # 调整位置避免卡住 / Adjust position to avoid getting stuck
                if dx > 0:
                    self.ball.center_x = brick.center_x + brick_half_width + BALL_RADIUS
                else:
                    self.ball.center_x = brick.center_x - brick_half_width - BALL_RADIUS
            else:
                # 上下碰撞 / Top/bottom collision
                self.ball.change_y *= -1
                # 调整位置避免卡住 / Adjust position to avoid getting stuck
                if dy > 0:
                    self.ball.center_y = brick.center_y + brick_half_height + BALL_RADIUS
                else:
                    self.ball.center_y = brick.center_y - brick_half_height - BALL_RADIUS

            self.destroy_brick_group(brick, incoming_dx, incoming_dy)
            # 只处理第一个碰撞的砖块 / Only handle first collision
            break

        # 更新球的彩虹效果 / Update ball rainbow effect
        self.ball.update_animation(delta_time)

        if self.ball.fireball_active:
            self.create_fireball_trail(self.ball.center_x, self.ball.center_y)

        # 更新粒子效果 / Update particle effects
        self.update_particles(delta_time)

    def spawn_reward(self, x, y, source_dx=0):
        """按概率生成奖励 / Spawn a reward by configured probability."""
        reward_type = choose_reward_type()
        if reward_type is None:
            return

        reward = RewardSprite(reward_type, x, y, source_dx)
        self.reward_list.append(reward)

    def update_rewards(self, delta_time):
        """更新自由落体奖励并处理接取/销毁 / Update free-falling rewards."""
        rewards_to_remove = []
        paddle_bottom = self.paddle.center_y - PADDLE_HEIGHT / 2

        for reward in self.reward_list:
            reward.center_x += reward.change_x * delta_time
            reward.center_y += reward.change_y * delta_time
            reward.change_y -= reward.gravity * delta_time
            reward.angle = (reward.angle + reward.angular_velocity * delta_time) % 360

            if reward.center_x - REWARD_RADIUS <= 0:
                reward.center_x = REWARD_RADIUS
                reward.change_x = abs(reward.change_x)
            elif reward.center_x + REWARD_RADIUS >= SCREEN_WIDTH:
                reward.center_x = SCREEN_WIDTH - REWARD_RADIUS
                reward.change_x = -abs(reward.change_x)

            if arcade.check_for_collision(reward, self.paddle):
                self.score += SCORE_PER_REWARD
                self.apply_reward(reward.reward_type)
                rewards_to_remove.append(reward)
                if self.game_status != GameStatus.PLAYING:
                    break
            elif reward.center_y + REWARD_RADIUS < paddle_bottom:
                rewards_to_remove.append(reward)

        for reward in rewards_to_remove:
            reward.remove_from_sprite_lists()

    def apply_reward(self, reward_type):
        """接受奖励效果 / Apply a collected reward effect."""
        if reward_type == REWARD_TYPE_FIREBALL:
            self.ball.activate_fireball()
        elif reward_type == REWARD_TYPE_EXTEND_PADDLE:
            self.resize_paddle(self.paddle.width + PADDLE_REWARD_SIZE_STEP)
        elif reward_type == REWARD_TYPE_SHRINK_PADDLE:
            self.resize_paddle(self.paddle.width - PADDLE_REWARD_SIZE_STEP)
        elif reward_type == REWARD_TYPE_RESET:
            self.reset_active_rewards()
        elif reward_type == REWARD_TYPE_LASER:
            self.laser_active = True
            self.update_laser_guns()
        elif reward_type == REWARD_TYPE_MAGNET:
            self.set_magnet_active(True)
        elif reward_type == REWARD_TYPE_SKULL:
            self.game_status = GameStatus.GAME_OVER
            self.laser_active = False
            self.laser_bullet_list.clear()
            self.set_magnet_active(False)

    def reset_active_rewards(self):
        """清除所有持续奖励 / Clear all persistent collected rewards."""
        self.ball.deactivate_fireball()
        self.laser_active = False
        self.laser_bullet_list.clear()
        self.set_magnet_active(False)
        self.resize_paddle(PADDLE_WIDTH)

    def set_magnet_active(self, active):
        """Enable or clear the persistent magnetic paddle effect."""
        if not active:
            self.release_magnet_ball()
        self.magnet_active = active

    def attach_ball_to_magnet(self):
        """Capture the descending ball at its actual paddle contact point."""
        if self.magnet_attached:
            return False
        half_range = max(0.0, self.paddle.width / 2 - BALL_RADIUS)
        self.magnet_offset = max(
            -half_range,
            min(half_range, self.ball.center_x - self.paddle.center_x),
        )
        self.magnet_speed = max(
            BALL_SPEED,
            math.hypot(self.ball.change_x, self.ball.change_y),
        )
        self.ball.change_x = 0.0
        self.ball.change_y = 0.0
        self.magnet_attached = True
        self.update_attached_ball()
        return True

    def release_magnet_ball(self):
        """Release the captured ball upward using its contact-point angle."""
        if not getattr(self, "magnet_attached", False):
            return False
        half_width = max(BALL_RADIUS, self.paddle.width / 2)
        relative_hit = max(-1.0, min(1.0, self.magnet_offset / half_width))
        angle = math.radians(relative_hit * PADDLE_BOUNCE_MAX_ANGLE)
        self.ball.change_x = self.magnet_speed * math.sin(angle)
        self.ball.change_y = abs(self.magnet_speed * math.cos(angle))
        self.ball.motion.set_spin_from_paddle_hit(relative_hit)
        self.magnet_attached = False
        return True

    def update_attached_ball(self):
        """Keep the captured ball and its electric field aligned to the paddle."""
        if not getattr(self, "magnet_attached", False):
            return
        half_range = max(0.0, self.paddle.width / 2 - BALL_RADIUS)
        self.magnet_offset = max(-half_range, min(half_range, self.magnet_offset))
        self.ball.center_x = self.paddle.center_x + self.magnet_offset
        self.ball.center_y = (
            self.paddle.center_y
            + PADDLE_HEIGHT / 2
            + BALL_RADIUS
            + BALL_PADDLE_GAP
        )
        self.update_magnet_effect()

    def update_magnet_effect(self):
        if not getattr(self, "magnet_effect", None):
            return
        ball_x = getattr(self.ball, "center_x", self.paddle.center_x)
        self.magnet_effect.center_x = ball_x
        self.magnet_effect.center_y = (
            self.paddle.center_y
            + PADDLE_HEIGHT / 2
            + MAGNET_EFFECT_HEIGHT / 2
            - 5
        )

    def update_laser_guns(self):
        if not self.laser_gun_list:
            return
        centers = (
            self.paddle.center_x - self.paddle.width / 2 + LASER_GUN_SIDE_INSET + LASER_GUN_WIDTH / 2,
            self.paddle.center_x + self.paddle.width / 2 - LASER_GUN_SIDE_INSET - LASER_GUN_WIDTH / 2,
        )
        for gun, center_x in zip(self.laser_gun_list, centers):
            gun.center_x = center_x
            gun.center_y = self.paddle.center_y + PADDLE_HEIGHT / 2 + LASER_GUN_HEIGHT / 2 - 3

    def fire_lasers(self):
        if not self.laser_active or self.game_status != GameStatus.PLAYING:
            return
        self.update_laser_guns()
        for gun in self.laser_gun_list:
            bullet = arcade.SpriteSolidColor(
                LASER_BULLET_WIDTH,
                LASER_BULLET_HEIGHT,
                center_x=gun.center_x,
                center_y=gun.top + LASER_BULLET_HEIGHT / 2,
                color=LASER_BULLET_COLOR,
            )
            self.laser_bullet_list.append(bullet)

    def update_lasers(self, delta_time):
        self.update_laser_guns()
        bullets_to_remove = []
        for bullet in self.laser_bullet_list:
            bullet.center_y += LASER_BULLET_SPEED * delta_time
            hit_bricks = arcade.check_for_collision_with_list(bullet, self.brick_list)
            if hit_bricks:
                brick = min(hit_bricks, key=lambda candidate: candidate.center_y)
                brick_x, brick_y, brick_color = brick.center_x, brick.center_y, brick.brick_color
                brick.remove_from_sprite_lists()
                self.score += SCORE_PER_BRICK
                self.create_explosion(brick_x, brick_y, brick_color)
                self.spawn_reward(brick_x, brick_y, 0)
                bullets_to_remove.append(bullet)
            elif bullet.bottom > SCREEN_HEIGHT:
                bullets_to_remove.append(bullet)

        for bullet in bullets_to_remove:
            bullet.remove_from_sprite_lists()
        if len(self.brick_list) == 0:
            self.game_status = GameStatus.VICTORY

    def resize_paddle(self, width):
        """调整挡板宽度并保持中心位置 / Resize paddle around its center."""
        new_width = max(PADDLE_MIN_WIDTH, min(PADDLE_MAX_WIDTH, width))
        self.paddle.set_paddle_width(new_width)
        self.clamp_paddle_to_screen()
        self.update_laser_guns()
        self.update_attached_ball()

    def clamp_paddle_to_screen(self):
        """根据当前动态宽度限制挡板 / Clamp using the current dynamic width."""
        half_width = self.paddle.width / 2
        self.paddle.center_x = max(
            half_width,
            min(SCREEN_WIDTH - half_width, self.paddle.center_x),
        )

    def destroy_brick_group(self, hit_brick, direction_x=0, direction_y=0):
        """销毁命中砖块，火球状态下沿运动方向额外销毁砖块 / Destroy fireball path."""
        if self.ball.fireball_active:
            bricks_to_destroy = self.bricks_in_fireball_path(hit_brick, direction_x, direction_y)
        else:
            bricks_to_destroy = [hit_brick]

        for brick in bricks_to_destroy:
            if not brick.sprite_lists:
                continue

            brick_x = brick.center_x
            brick_y = brick.center_y
            brick_color = brick.brick_color
            brick.remove_from_sprite_lists()

            self.score += SCORE_PER_BRICK
            self.create_explosion(brick_x, brick_y, brick_color)
            self.spawn_reward(brick_x, brick_y, direction_x)

        if len(self.brick_list) == 0:
            self.game_status = GameStatus.VICTORY

    def bricks_in_fireball_path(self, source_brick, direction_x, direction_y):
        """返回撞击砖块运动方向一侧的 2x2 局部砖块 / Return the directional local 2x2 area."""
        if math.hypot(direction_x, direction_y) <= 1e-6:
            return [source_brick]

        candidates = []

        for brick in list(self.brick_list):
            if brick is source_brick:
                continue

            offset_x = brick.center_x - source_brick.center_x
            offset_y = brick.center_y - source_brick.center_y
            if inside_fireball_impact_area(
                offset_x,
                offset_y,
                direction_x,
                direction_y,
            ):
                candidates.append((offset_x * offset_x + offset_y * offset_y, brick))

        candidates.sort(key=lambda item: item[0])
        return [
            source_brick,
            *[brick for _, brick in candidates[:3]],
        ]

    def bricks_near(self, source_brick):
        """兼容测试：返回火球路径候选砖块 / Compatibility helper for path bricks."""
        return self.bricks_in_fireball_path(
            source_brick,
            self.ball.change_x,
            self.ball.change_y,
        )

    def create_explosion(self, x, y, color):
        """创建爆炸粒子效果 / Create explosion particle effect"""

        for _ in range(PARTICLE_COUNT):
            # 随机速度 / Random velocity
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_MIN_SPEED, PARTICLE_MAX_SPEED)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            # 创建粒子 / Create particle
            particle = arcade.SpriteCircle(PARTICLE_RADIUS, color)
            particle.center_x = x
            particle.center_y = y
            particle.change_x = velocity_x
            particle.change_y = velocity_y
            particle.alpha = 255
            particle.age = 0  # 跟踪粒子年龄

            # 添加到粒子列表 / Add to particle list
            self.particle_list.append(particle)

    def create_fireball_trail(self, x, y):
        """创建火球尾焰粒子 / Create fireball flame trail particles."""
        for _ in range(FIREBALL_TRAIL_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(FIREBALL_TRAIL_MIN_SPEED, FIREBALL_TRAIL_MAX_SPEED)
            color = random.choice(FIREBALL_TRAIL_COLORS)

            particle = arcade.SpriteCircle(FIREBALL_TRAIL_PARTICLE_RADIUS, color)
            particle.center_x = x + random.uniform(-BALL_RADIUS / 2, BALL_RADIUS / 2)
            particle.center_y = y + random.uniform(-BALL_RADIUS / 2, BALL_RADIUS / 2)
            particle.change_x = math.cos(angle) * speed
            particle.change_y = math.sin(angle) * speed
            particle.alpha = 210
            particle.age = 0
            particle.lifetime = FIREBALL_TRAIL_PARTICLE_LIFETIME
            particle.gravity = FIREBALL_TRAIL_GRAVITY

            self.particle_list.append(particle)

    def update_particles(self, delta_time):
        """更新所有粒子 / Update all particles"""
        particles_to_remove = []

        for particle in self.particle_list:
            lifetime = getattr(particle, "lifetime", PARTICLE_LIFETIME)
            gravity = getattr(particle, "gravity", PARTICLE_GRAVITY)

            # 更新年龄 / Update age
            particle.age += delta_time

            # 更新位置 / Update position
            particle.center_x += particle.change_x * delta_time
            particle.center_y += particle.change_y * delta_time

            # 应用重力 / Apply gravity
            particle.change_y -= gravity * delta_time

            # 淡出效果 / Fade out effect
            fade = 1 - (particle.age / lifetime)
            particle.alpha = int(255 * max(0, fade))

            # 标记要移除的粒子 / Mark particles for removal
            if particle.age >= lifetime:
                particles_to_remove.append(particle)

        # 移除过期粒子 / Remove expired particles
        for particle in particles_to_remove:
            particle.remove_from_sprite_lists()

    def on_key_press(self, key, modifiers):
        """按键按下事件 / Key press event"""

        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            if self.space_pressed:
                return
            self.space_pressed = True
            if self.game_status == GameStatus.NOT_STARTED:
                self.start_playing()
            elif self.game_status == GameStatus.PLAYING:
                if self.release_magnet_ball():
                    return
                self.left_pressed = False
                self.right_pressed = False
                self.game_status = GameStatus.PAUSED
            elif self.game_status == GameStatus.PAUSED:
                self.game_status = GameStatus.PLAYING
            elif self.game_status in (GameStatus.GAME_OVER, GameStatus.VICTORY):
                self.setup()
                self.start_playing()

    def on_key_release(self, key, modifiers):
        """按键释放事件 / Key release event"""

        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.SPACE:
            self.space_pressed = False

    def on_mouse_motion(self, x, y, dx, dy):
        """鼠标移动事件 / Mouse motion event"""
        if self.game_status == GameStatus.PAUSED:
            return
        # 使用鼠标X坐标控制挡板位置 / Use mouse X coordinate to control paddle
        self.paddle.center_x = x

        # 限制挡板在屏幕内 / Keep paddle on screen
        self.clamp_paddle_to_screen()

        # 如果游戏未开始，球跟随挡板 / If game hasn't started, ball follows paddle
        if self.game_status == GameStatus.NOT_STARTED:
            self.ball.center_x = self.paddle.center_x

        self.update_laser_guns()
        self.update_attached_ball()

    def on_mouse_press(self, x, y, button, modifiers):
        """鼠标左键优先释放吸附球，否则发射双激光 / Release first, otherwise fire."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            if not self.release_magnet_ball():
                self.fire_lasers()

    def start_playing(self):
        """发射小球并进入游戏 / Launch the ball and enter play."""
        self.magnet_attached = False
        self.game_status = GameStatus.PLAYING
        angle = math.radians(BALL_START_ANGLE)
        self.ball.change_x = BALL_SPEED * math.cos(angle)
        self.ball.change_y = BALL_SPEED * math.sin(angle)


def main():
    """主函数 / Main function"""
    game = BreakoutGame()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
