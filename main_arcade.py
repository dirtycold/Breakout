"""
DX-Ball 克隆游戏 - 主程序
DX-Ball Clone Game - Main Program

简单的打砖块游戏，适合小朋友学习
Simple brick-breaker game for kids to learn
"""

import arcade
import math
import random
from PIL import Image, ImageDraw
from ball_texture import RainbowBallMotion, create_rainbow_ball_image
from constants import *


class RainbowBall(arcade.Sprite):
    """彩虹条纹球类 / Rainbow Striped Ball Class"""

    def __init__(self, radius):
        super().__init__()
        self.radius = radius
        self.motion = RainbowBallMotion()

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

    def __init__(self, width, height, color, radius=PADDLE_CORNER_RADIUS):
        super().__init__()
        self.paddle_width = width
        self.paddle_height = height
        self.paddle_color = color
        self.corner_radius = radius
        self.gradient_offset = 0

        # 创建圆角矩形纹理
        self._create_rounded_rect_texture()

    def _create_rounded_rect_texture(self):
        """创建带圆角的矩形纹理 / Create rounded rectangle texture"""
        # 使用更大的尺寸进行超采样，然后缩小以获得更好的抗锯齿效果
        scale = 4  # 4x 超采样
        width = int(self.paddle_width * scale)
        height = int(self.paddle_height * scale)

        # 创建 PIL 图像
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)

        for x in range(width):
            gradient_x = (x / scale - self.gradient_offset) % self.paddle_width
            color = self._gradient_color(gradient_x / max(1, self.paddle_width))
            gradient_draw.line([(x, 0), (x, height)], fill=(*color, 255))

        # 使用圆角遮罩裁剪渐变 / Clip gradient to rounded rectangle
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, width - 1, height - 1],
            radius=self.corner_radius * scale,
            fill=255
        )
        image.paste(gradient, (0, 0), mask)
        draw = ImageDraw.Draw(image)

        fang_height = PADDLE_FANG_HEIGHT * scale
        fang_inset = PADDLE_FANG_SIDE_INSET * scale
        usable_width = width - fang_inset * 2
        fang_spacing = usable_width / PADDLE_FANG_COUNT

        for index in range(PADDLE_FANG_COUNT):
            base_left = fang_inset + index * fang_spacing
            base_right = fang_inset + (index + 1) * fang_spacing
            tip_x = (base_left + base_right) / 2

            draw.polygon(
                [
                    (base_left, 0),
                    (base_right, 0),
                    (tip_x, fang_height),
                ],
                fill=COLOR_PADDLE_FANG,
                outline=COLOR_PADDLE_FANG_SHADOW,
            )

        # 缩小到实际尺寸（提供抗锯齿效果）
        image = image.resize((int(self.paddle_width), int(self.paddle_height)), Image.Resampling.LANCZOS)

        # 转换为 Arcade 纹理
        self.texture = arcade.Texture(image=image, name=f"paddle_{id(self)}")

        # 设置碰撞框
        self.width = self.paddle_width
        self.height = self.paddle_height

    def update_animation(self, delta_time=FIXED_DELTA_TIME):
        """更新挡板彩虹渐变偏移 / Update paddle rainbow gradient offset."""
        self.gradient_offset = (
            self.gradient_offset + PADDLE_GRADIENT_SCROLL_SPEED * delta_time
        ) % self.paddle_width
        self._create_rounded_rect_texture()

    def _gradient_color(self, position):
        """返回渐变位置对应颜色 / Return color for a gradient position."""
        colors = PADDLE_GRADIENT_COLORS
        stops = PADDLE_GRADIENT_STOPS
        position = max(0.0, min(1.0, position))

        for index in range(len(stops) - 1):
            if position <= stops[index + 1]:
                start_stop = stops[index]
                end_stop = stops[index + 1]
                blend = 0 if end_stop == start_stop else (position - start_stop) / (end_stop - start_stop)
                start = colors[index]
                end = colors[index + 1]
                return tuple(
                    int(start[channel] + (end[channel] - start[channel]) * blend)
                    for channel in range(3)
                )

        return colors[-1]


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

        # 移动标志 / Movement flags
        self.left_pressed = False
        self.right_pressed = False

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

        # 绘制球 / Draw ball
        self.ball_list.draw()

        # 绘制粒子效果 / Draw particle effects
        self.particle_list.draw()

        # 绘制分数 / Draw score
        arcade.draw_text(
            f"{SCORE_LABEL}: {self.score}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            SCORE_FONT_SIZE
        )

        # 如果游戏未开始，显示开始提示 / Show start message if game hasn't started
        if self.game_status == GameStatus.NOT_STARTED:
            arcade.draw_text(
                MESSAGE_START_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_START_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_START_LINES[2],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                arcade.color.WHITE,
                MESSAGE_HINT_FONT_SIZE,
                anchor_x="center"
            )

        # 如果游戏结束，显示提示 / Show game over message
        if self.game_status == GameStatus.GAME_OVER:
            arcade.draw_text(
                MESSAGE_GAME_OVER_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_GAME_OVER_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                anchor_x="center"
            )

        # 如果胜利，显示提示 / Show victory message
        if self.game_status == GameStatus.VICTORY:
            arcade.draw_text(
                MESSAGE_VICTORY_LINES[0],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                MESSAGE_PRIMARY_FONT_SIZE,
                anchor_x="center"
            )
            arcade.draw_text(
                MESSAGE_VICTORY_LINES[1],
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                MESSAGE_SECONDARY_FONT_SIZE,
                anchor_x="center"
            )

    def on_update(self, delta_time):
        """更新游戏逻辑 / Update game logic"""
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
            if self.paddle.center_x < PADDLE_WIDTH / 2:
                self.paddle.center_x = PADDLE_WIDTH / 2
            if self.paddle.center_x > SCREEN_WIDTH - PADDLE_WIDTH / 2:
                self.paddle.center_x = SCREEN_WIDTH - PADDLE_WIDTH / 2

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
        if self.paddle.center_x < PADDLE_WIDTH / 2:
            self.paddle.center_x = PADDLE_WIDTH / 2
        if self.paddle.center_x > SCREEN_WIDTH - PADDLE_WIDTH / 2:
            self.paddle.center_x = SCREEN_WIDTH - PADDLE_WIDTH / 2

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

            # 移除砖块 / Remove brick
            brick.remove_from_sprite_lists()

            # 增加分数 / Increase score
            self.score += SCORE_PER_BRICK

            # 检测胜利 / Check victory
            if len(self.brick_list) == 0:
                self.game_status = GameStatus.VICTORY

            # 创建爆炸效果 / Create explosion effect
            self.create_explosion(brick.center_x, brick.center_y, brick.brick_color)
            # 只处理第一个碰撞的砖块 / Only handle first collision
            break

        # 更新球的彩虹效果 / Update ball rainbow effect
        self.ball.update_animation(delta_time)

        # 更新粒子效果 / Update particle effects
        self.update_particles(delta_time)

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

    def update_particles(self, delta_time):
        """更新所有粒子 / Update all particles"""
        particles_to_remove = []

        for particle in self.particle_list:
            # 更新年龄 / Update age
            particle.age += delta_time

            # 更新位置 / Update position
            particle.center_x += particle.change_x * delta_time
            particle.center_y += particle.change_y * delta_time

            # 应用重力 / Apply gravity
            particle.change_y -= PARTICLE_GRAVITY * delta_time

            # 淡出效果 / Fade out effect
            fade = 1 - (particle.age / PARTICLE_LIFETIME)
            particle.alpha = int(255 * max(0, fade))

            # 标记要移除的粒子 / Mark particles for removal
            if particle.age >= PARTICLE_LIFETIME:
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
            # 按空格键开始游戏 / Press space to start game
            if self.game_status == GameStatus.NOT_STARTED:
                self.game_status = GameStatus.PLAYING
                # 发射球 / Launch ball
                angle = math.radians(BALL_START_ANGLE)
                self.ball.change_x = BALL_SPEED * math.cos(angle)
                self.ball.change_y = BALL_SPEED * math.sin(angle)
        elif key == arcade.key.R:
            # 重新开始游戏 / Restart game
            self.setup()

    def on_key_release(self, key, modifiers):
        """按键释放事件 / Key release event"""

        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def on_mouse_motion(self, x, y, dx, dy):
        """鼠标移动事件 / Mouse motion event"""
        # 使用鼠标X坐标控制挡板位置 / Use mouse X coordinate to control paddle
        self.paddle.center_x = x

        # 限制挡板在屏幕内 / Keep paddle on screen
        if self.paddle.center_x < PADDLE_WIDTH / 2:
            self.paddle.center_x = PADDLE_WIDTH / 2
        if self.paddle.center_x > SCREEN_WIDTH - PADDLE_WIDTH / 2:
            self.paddle.center_x = SCREEN_WIDTH - PADDLE_WIDTH / 2

        # 如果游戏未开始，球跟随挡板 / If game hasn't started, ball follows paddle
        if self.game_status == GameStatus.NOT_STARTED:
            self.ball.center_x = self.paddle.center_x


def main():
    """主函数 / Main function"""
    game = BreakoutGame()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
