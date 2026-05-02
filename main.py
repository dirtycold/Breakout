"""
DX-Ball 克隆游戏 - 主程序
DX-Ball Clone Game - Main Program

简单的打砖块游戏，适合小朋友学习
Simple brick-breaker game for kids to learn
"""

import arcade
import math
import random
import colorsys
from PIL import Image, ImageDraw
from constants import *


class RainbowBall(arcade.Sprite):
    """彩虹渐变球类 / Rainbow Gradient Ball Class"""

    def __init__(self, radius):
        super().__init__()
        self.radius = radius
        self.rainbow_phase = 0

        # 创建抗锯齿的圆形纹理
        self._create_circle_texture()

    def _create_circle_texture(self):
        """创建带抗锯齿的圆形纹理 / Create antialiased circle texture"""
        # 创建一个更大的图像用于超采样抗锯齿
        size = int(self.radius * 2 * 4)  # 4x超采样

        # 创建PIL图像
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制抗锯齿圆形
        draw.ellipse([0, 0, size - 1, size - 1], fill=(255, 255, 255, 255))

        # 缩小到实际尺寸（提供抗锯齿效果）
        image = image.resize((int(self.radius * 2), int(self.radius * 2)), Image.Resampling.LANCZOS)

        # 转换为Arcade纹理 - 使用正确的方法
        self.texture = arcade.Texture(image=image, name=f"rainbow_ball_{id(self)}")

        # 设置碰撞框
        self.width = self.radius * 2
        self.height = self.radius * 2

    def update_animation(self, delta_time=1/60):
        """更新彩虹颜色 / Update rainbow color"""
        self.rainbow_phase += RAINBOW_SPEED * delta_time

        # 使用HSV色彩空间创建彩虹效果
        # Using HSV color space to create rainbow effect
        hue = (self.rainbow_phase * 60) % 360  # 0-360度

        # 转换HSV到RGB (hue: 0-360, saturation: 0-1, value: 0-1)
        rgb = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)

        # 转换为0-255范围的整数
        self.color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


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
        self.game_over = False
        self.game_started = False

    def setup(self):
        """设置游戏（开始或重置）/ Set up the game (start or reset)"""

        # 创建挡板 / Create paddle
        self.paddle_list = arcade.SpriteList()
        self.paddle = arcade.SpriteSolidColor(
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
            COLOR_PADDLE
        )
        self.paddle.center_x = SCREEN_WIDTH / 2
        self.paddle.center_y = PADDLE_Y_POSITION
        self.paddle_list.append(self.paddle)

        # 创建球 / Create ball
        self.ball_list = arcade.SpriteList()
        self.ball = RainbowBall(BALL_RADIUS)
        self.ball.center_x = SCREEN_WIDTH / 2
        self.ball.center_y = PADDLE_Y_POSITION + PADDLE_HEIGHT + 20
        self.ball_list.append(self.ball)

        # 设置球的初始速度为0（等待开始）/ Set initial ball velocity to 0 (waiting to start)
        self.ball.change_x = 0
        self.ball.change_y = 0

        # 创建砖块列表 / Create brick list
        self.brick_list = arcade.SpriteList()

        # 生成菱形砖块布局 / Generate diamond-shaped brick layout
        for row in range(BRICK_ROWS):
            # 计算这一行应该有多少砖块（菱形效果）
            if row < BRICK_ROWS // 2:
                # 上半部分：逐渐增加砖块数量
                bricks_in_row = (row + 1) * 2
            else:
                # 下半部分：逐渐减少砖块数量
                bricks_in_row = (BRICK_ROWS - row) * 2

            # 计算这一行的起始偏移，使其居中
            total_row_width = bricks_in_row * BRICK_WIDTH + (bricks_in_row - 1) * BRICK_MARGIN
            row_offset = (SCREEN_WIDTH - total_row_width) / 2

            for column in range(bricks_in_row):
                # 选择颜色（根据行数）/ Choose color based on row
                color = BRICK_COLORS[row % len(BRICK_COLORS)]

                # 创建砖块 / Create brick
                brick = arcade.SpriteSolidColor(BRICK_WIDTH, BRICK_HEIGHT, color)

                # 设置位置（菱形布局）/ Set position (diamond layout)
                brick.center_x = row_offset + (BRICK_MARGIN + BRICK_WIDTH) * column + BRICK_WIDTH / 2
                brick.center_y = SCREEN_HEIGHT - BRICK_TOP_MARGIN - (BRICK_MARGIN + BRICK_HEIGHT) * row

                # 添加到列表 / Add to list
                self.brick_list.append(brick)

        # 重置粒子效果 / Reset particle effects
        self.particle_list = arcade.SpriteList()

        # 重置游戏状态 / Reset game state
        self.score = 0
        self.game_over = False
        self.game_started = False
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
            f"分数 Score: {self.score}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            20,
            font_name="Noto Sans CJK SC"
        )

        # 如果游戏未开始，显示开始提示 / Show start message if game hasn't started
        if not self.game_started and not self.game_over:
            arcade.draw_text(
                "按空格键开始游戏",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                30,
                anchor_x="center",
                font_name="Noto Sans CJK SC"
            )
            arcade.draw_text(
                "Press SPACE to Start",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                20,
                anchor_x="center",
                font_name="Noto Sans CJK SC"
            )
            arcade.draw_text(
                "← → 移动挡板 / Move Paddle",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                arcade.color.WHITE,
                16,
                anchor_x="center",
                font_name="Noto Sans CJK SC"
            )

        # 如果游戏结束，显示提示 / Show game over message
        if self.game_over:
            arcade.draw_text(
                "游戏结束！按 R 重新开始",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                30,
                anchor_x="center",
                font_name="Noto Sans CJK SC"
            )
            arcade.draw_text(
                "Game Over! Press R to Restart",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                arcade.color.WHITE,
                20,
                anchor_x="center",
                font_name="Noto Sans CJK SC"
            )

    def on_update(self, delta_time):
        """更新游戏逻辑 / Update game logic"""

        if self.game_over:
            # 只更新粒子效果 / Only update particle effects
            self.update_particles(delta_time)
            return

        # 如果游戏未开始，只允许移动挡板 / If game hasn't started, only allow paddle movement
        if not self.game_started:
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
        if self.ball.center_y < 0:
            self.game_over = True
            return

        # 球与挡板碰撞 / Ball collision with paddle
        if arcade.check_for_collision(self.ball, self.paddle):
            # 计算击中挡板的相对位置 / Calculate relative hit position on paddle
            relative_hit = (self.ball.center_x - self.paddle.center_x) / (PADDLE_WIDTH / 2)
            relative_hit = max(-1, min(1, relative_hit))  # 限制在 -1 到 1 之间

            # 根据击中位置调整反弹角度 / Adjust bounce angle based on hit position
            angle = relative_hit * 60  # 最大偏转 60 度
            angle_rad = math.radians(angle)

            speed = math.sqrt(self.ball.change_x**2 + self.ball.change_y**2)
            self.ball.change_x = speed * math.sin(angle_rad)
            self.ball.change_y = abs(speed * math.cos(angle_rad))  # 确保向上

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
            self.score += 10

            # 创建爆炸效果 / Create explosion effect
            self.create_explosion(brick.center_x, brick.center_y, brick.color)

            # 只处理第一个碰撞的砖块 / Only handle first collision
            break

        # 更新球的彩虹效果 / Update ball rainbow effect
        self.ball.update_animation(delta_time)

        # 更新粒子效果 / Update particle effects
        self.update_particles(delta_time)

        # 检查胜利条件 / Check win condition
        if len(self.brick_list) == 0:
            self.game_over = True

    def create_explosion(self, x, y, color):
        """创建爆炸粒子效果 / Create explosion particle effect"""

        for _ in range(PARTICLE_COUNT):
            # 随机速度 / Random velocity
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            # 创建粒子 / Create particle
            particle = arcade.SpriteCircle(3, color)
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
            particle.change_y -= 200 * delta_time

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
            if not self.game_started and not self.game_over:
                self.game_started = True
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
        if not self.game_started and not self.game_over:
            self.ball.center_x = self.paddle.center_x


def main():
    """主函数 / Main function"""
    game = BreakoutGame()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
