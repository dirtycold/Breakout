#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QML 版打砖块游戏主入口
Main Entry Point for QML Breakout Game

使用 qtpy 抽象层，优先选择 PyQt6
"""
import sys
import os
from pathlib import Path

# 优先使用 PyQt6
os.environ.setdefault('QT_API', 'pyqt6')

from qtpy.QtGui import QGuiApplication
from qtpy.QtQml import QQmlApplicationEngine, qmlRegisterType
from qtpy.QtCore import QObject, Property, Slot

# 导入游戏逻辑类
from game_logic_qml import GameState, Ball, GameController, getBrickColors
from constants import *


class ColorProvider(QObject):
    """颜色提供器 / Color Provider"""
    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(list, constant=True)
    def brickColors(self):
        return getBrickColors()

class GameStatusProvider(QObject):
    """游戏状态枚举提供器 / Game Status Enum Provider"""
    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(int, constant=True)
    def NOT_STARTED(self):
        return int(GameStatus.NOT_STARTED)

    @Property(int, constant=True)
    def PLAYING(self):
        return int(GameStatus.PLAYING)

    @Property(int, constant=True)
    def GAME_OVER(self):
        return int(GameStatus.GAME_OVER)

    @Property(int, constant=True)
    def VICTORY(self):
        return int(GameStatus.VICTORY)


class GameConfigProvider(QObject):
    """共享游戏配置提供器 / Shared Game Config Provider"""
    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(int, constant=True)
    def screenWidth(self):
        return SCREEN_WIDTH

    @Property(int, constant=True)
    def screenHeight(self):
        return SCREEN_HEIGHT

    @Property(str, constant=True)
    def screenTitleQml(self):
        return SCREEN_TITLE_QML

    @Property(str, constant=True)
    def backgroundColor(self):
        return COLOR_BACKGROUND_HEX

    @Property(str, constant=True)
    def paddleColor(self):
        return COLOR_PADDLE_HEX

    @Property(str, constant=True)
    def ballColor(self):
        return "#%02x%02x%02x" % COLOR_BALL

    @Property(int, constant=True)
    def frameIntervalMs(self):
        return FRAME_INTERVAL_MS

    @Property(float, constant=True)
    def fixedDeltaTime(self):
        return FIXED_DELTA_TIME

    @Property(int, constant=True)
    def paddleWidth(self):
        return PADDLE_WIDTH

    @Property(int, constant=True)
    def paddleHeight(self):
        return PADDLE_HEIGHT

    @Property(float, constant=True)
    def paddleY(self):
        return qml_paddle_y()

    @Property(int, constant=True)
    def paddleCornerRadius(self):
        return PADDLE_CORNER_RADIUS

    @Property(float, constant=True)
    def paddleMoveStep(self):
        return PADDLE_SPEED * FIXED_DELTA_TIME

    @Property(int, constant=True)
    def ballRadius(self):
        return BALL_RADIUS

    @Property(int, constant=True)
    def ballDiameter(self):
        return BALL_DIAMETER

    @Property(float, constant=True)
    def ballStartCenterY(self):
        return qml_ball_start_center_y()

    @Property(int, constant=True)
    def brickWidth(self):
        return BRICK_WIDTH

    @Property(int, constant=True)
    def brickHeight(self):
        return BRICK_HEIGHT

    @Property(int, constant=True)
    def brickMargin(self):
        return BRICK_MARGIN

    @Property(int, constant=True)
    def brickRows(self):
        return BRICK_ROWS

    @Property(int, constant=True)
    def brickCornerRadius(self):
        return BRICK_CORNER_RADIUS

    @Property(list, constant=True)
    def brickColors(self):
        return BRICK_COLORS_HEX

    @Property(int, constant=True)
    def particleCount(self):
        return PARTICLE_COUNT

    @Property(int, constant=True)
    def particleRadius(self):
        return PARTICLE_RADIUS

    @Property(int, constant=True)
    def particleDiameter(self):
        return PARTICLE_RADIUS * 2

    @Property(float, constant=True)
    def particleMinSpeed(self):
        return PARTICLE_MIN_SPEED

    @Property(float, constant=True)
    def particleMaxSpeed(self):
        return PARTICLE_MAX_SPEED

    @Property(float, constant=True)
    def particleGravity(self):
        return PARTICLE_GRAVITY

    @Property(float, constant=True)
    def particleLifetime(self):
        return PARTICLE_LIFETIME

    @Slot(int, result=int)
    def bricksInRow(self, row):
        return bricks_in_row(row)

    @Slot(result=int)
    def totalBrickCount(self):
        return total_brick_count()

    @Slot(int, result=float)
    def brickRowWidth(self, row):
        return brick_row_width(row)

    @Slot(int, result=float)
    def brickLeftX(self, row):
        return brick_row_left_x(row)

    @Slot(int, int, result=float)
    def brickX(self, row, column):
        return qml_brick_x(row, column)

    @Slot(int, result=float)
    def brickY(self, row):
        return qml_brick_y(row)

def main():
    """主程序 / Main Program"""
    app = QGuiApplication(sys.argv)

    # 注册 QML 类型
    qmlRegisterType(GameState, 'GameLogic', 1, 0, 'GameState')
    qmlRegisterType(Ball, 'GameLogic', 1, 0, 'Ball')
    qmlRegisterType(GameController, 'GameLogic', 1, 0, 'GameController')
    qmlRegisterType(ColorProvider, 'GameLogic', 1, 0, 'ColorProvider')
    qmlRegisterType(GameStatusProvider, 'GameLogic', 1, 0, 'GameStatusProvider')
    qmlRegisterType(GameConfigProvider, 'GameLogic', 1, 0, 'GameConfigProvider')

    engine = QQmlApplicationEngine()

    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    qml_file = current_dir / "main.qml"

    # 加载 QML 文件
    engine.load(str(qml_file))

    if not engine.rootObjects():
        print("错误：无法加载 QML 文件")
        print("提示：请确保已正确安装 PyQt6 或 PySide6")
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
