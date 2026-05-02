#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt 绑定配置

设置 QT_API 环境变量以选择 Qt 绑定
优先级: PyQt6 > PySide6 > PyQt5 > PySide2
"""
import os
import sys


def setup_qt_api(preferred='pyqt6'):
    """
    设置 Qt API 优先级

    参数:
        preferred: 'pyqt6', 'pyside6', 'pyqt5', 或 'pyside2'
    """
    os.environ['QT_API'] = preferred.lower()

    # 验证选择的绑定是否可用
    try:
        import qtpy
        print(f"✅ 使用 Qt 绑定: {qtpy.API_NAME} (版本 {qtpy.QT_VERSION})")
        return True
    except ImportError as e:
        print(f"❌ 无法导入 qtpy: {e}")
        print("请安装: pip install qtpy PyQt6")
        return False


def get_available_bindings():
    """检测所有可用的 Qt 绑定"""
    bindings = []

    for api in ['pyqt6', 'pyside6', 'pyqt5', 'pyside2']:
        try:
            os.environ['QT_API'] = api
            import qtpy
            bindings.append(f"{qtpy.API_NAME} {qtpy.QT_VERSION}")
        except ImportError:
            pass

    return bindings


if __name__ == "__main__":
    print("检测可用的 Qt 绑定...")
    available = get_available_bindings()

    if available:
        print("\n可用的 Qt 绑定:")
        for binding in available:
            print(f"  - {binding}")
    else:
        print("\n❌ 未检测到任何 Qt 绑定!")
        print("请安装: pip install PyQt6 或 pip install PySide6")

    print("\n设置默认绑定为 PyQt6...")
    setup_qt_api('pyqt6')
