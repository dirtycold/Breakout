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


class ColorProvider(QObject):
    """颜色提供器 / Color Provider"""
    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(list, constant=True)
    def brickColors(self):
        return getBrickColors()

def main():
    """主程序 / Main Program"""
    app = QGuiApplication(sys.argv)

    # 注册 QML 类型
    qmlRegisterType(GameState, 'GameLogic', 1, 0, 'GameState')
    qmlRegisterType(Ball, 'GameLogic', 1, 0, 'Ball')
    qmlRegisterType(GameController, 'GameLogic', 1, 0, 'GameController')
    qmlRegisterType(ColorProvider, 'GameLogic', 1, 0, 'ColorProvider')

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
