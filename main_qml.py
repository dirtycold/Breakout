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
from qtpy.QtCore import QObject, Property

# 导入游戏逻辑类
from game_logic_qml import GameState, Ball, GameController, getBrickColors
from constants import GameStatus


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
        return GameStatus.NOT_STARTED

    @Property(int, constant=True)
    def PLAYING(self):
        return GameStatus.PLAYING

    @Property(int, constant=True)
    def GAME_OVER(self):
        return GameStatus.GAME_OVER

    @Property(int, constant=True)
    def VICTORY(self):
        return GameStatus.VICTORY

def main():
    """主程序 / Main Program"""
    app = QGuiApplication(sys.argv)

    # 注册 QML 类型
    qmlRegisterType(GameState, 'GameLogic', 1, 0, 'GameState')
    qmlRegisterType(Ball, 'GameLogic', 1, 0, 'Ball')
    qmlRegisterType(GameController, 'GameLogic', 1, 0, 'GameController')
    qmlRegisterType(ColorProvider, 'GameLogic', 1, 0, 'ColorProvider')
    qmlRegisterType(GameStatusProvider, 'GameLogic', 1, 0, 'GameStatusProvider')

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
