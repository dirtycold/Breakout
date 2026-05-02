import QtQuick
import QtQuick.Window
import GameLogic 1.0

Window {
    id: root
    width: 800
    height: 600
    visible: true
    title: "DX-Ball Clone (QML版) / 打砖块游戏"
    color: "#1A1A2E"

    // 计算砖块数量（菱形布局）
    function calculateBrickCount() {
        let count = 0
        for (let row = 0; row < 5; row++) {
            let bricks_in_row = 5 + row * 2
            count += bricks_in_row
        }
        return count
    }

    // 颜色提供器（从 Python constants 读取）
    ColorProvider {
        id: colorProvider
    }

    // 游戏控制器（Python 后端）
    GameController {
        id: gameController

        onRequestCreateExplosion: (x, y, color) => {
            particleSystem.createExplosion(x, y, color)
        }
    }

    // 主游戏区域（用于接收键盘输入）
    Item {
        anchors.fill: parent
        focus: true

        Keys.onPressed: (event) => {
            if (event.key === Qt.Key_Space && gameController && gameController.state && !gameController.state.gameOver) {
                gameController.startGame()
            } else if (event.key === Qt.Key_R) {
                brickRepeater.model = 0  // 清空砖块
                brickRepeater.model = root.calculateBrickCount()  // 重新创建
                gameController.resetGame()
            } else if (event.key === Qt.Key_Left) {
                paddle.moveLeft = true
            } else if (event.key === Qt.Key_Right) {
                paddle.moveRight = true
            }
        }

        Keys.onReleased: (event) => {
            if (event.key === Qt.Key_Left) {
                paddle.moveLeft = false
            } else if (event.key === Qt.Key_Right) {
                paddle.moveRight = false
            }
        }

        // 鼠标控制
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onPositionChanged: function(mouse) {
                paddle.x = Math.max(0, Math.min(root.width - paddle.width, mouse.x - paddle.width / 2))
            }
        }

        // 砖块容器
        Item {
            id: brickContainer
            anchors.fill: parent

            Repeater {
                id: brickRepeater
                model: root.calculateBrickCount()

                delegate: Rectangle {
                id: brick
                width: 55
                height: 25
                radius: 5

                property int brickIndex: index
                property bool destroyed: false

                // 计算砖块位置（菱形布局）
                Component.onCompleted: {
                    let currentIndex = brickIndex
                    let currentRow = 0
                    let posInRow = 0

                    // 找到当前砖块在哪一行
                    for (let row = 0; row < 5; row++) {
                        let bricks_in_row = 5 + row * 2
                        if (currentIndex < bricks_in_row) {
                            currentRow = row
                            posInRow = currentIndex
                            break
                        }
                        currentIndex -= bricks_in_row
                    }

                    let bricks_in_row = 5 + currentRow * 2
                    let row_width = bricks_in_row * (55 + 4) - 4
                    let start_x = (root.width - row_width) / 2

                    brick.x = start_x + posInRow * (55 + 4)
                    brick.y = 80 + currentRow * (25 + 4)

                    // 设置颜色（从 Python constants 读取）
                    brick.color = colorProvider.brickColors[currentRow % colorProvider.brickColors.length]
                }

                // 碰撞检测（每帧）
                Timer {
                    running: !brick.destroyed
                    repeat: true
                    interval: 16
                    onTriggered: {
                        if (gameController && gameController.state && !gameController.state.gameOver &&
                            gameController.checkBrickCollision(
                                brick.x, brick.y, brick.width, brick.height, brick.color
                            )) {
                            brick.destroyed = true
                            brick.visible = false
                        }
                    }
                }
                }  // Rectangle (brick) 结束
            }  // Repeater 结束
        }  // Item (brickContainer) 结束

        // 挡板
        Rectangle {
            id: paddle
            width: 100
            height: 20
            color: "#3498DB"
            radius: 10
            x: (root.width - width) / 2
            y: root.height - 70

            property bool moveLeft: false
            property bool moveRight: false

            // 键盘移动逻辑
            Timer {
                running: true
                repeat: true
                interval: 16
                onTriggered: {
                    if (paddle.moveLeft) {
                        paddle.x = Math.max(0, paddle.x - 8)
                    }
                    if (paddle.moveRight) {
                        paddle.x = Math.min(root.width - paddle.width, paddle.x + 8)
                    }

                    // 检测挡板碰撞
                    gameController.checkPaddleCollision(paddle.x, paddle.y, paddle.width)

                    // 球跟随挡板（游戏未开始时）
                    if (gameController && gameController.ball) {
                        gameController.ball.followPaddle(paddle.x, paddle.width)
                    }
                }
            }
        }

        // 球（彩虹渐变）
        Rectangle {
            id: ball
            width: 20
            height: 20
            radius: 10
            x: gameController && gameController.ball ? gameController.ball.x - 10 : paddle.x + paddle.width / 2 - 10
            y: gameController && gameController.ball ? gameController.ball.y - 10 : paddle.y - 20
            color: "#FF0000"

            Connections {
                target: gameController ? gameController.ball : null
                function onColorChanged(newColor) {
                    ball.color = newColor
                }
            }

            // 抗锯齿效果
            layer.enabled: true
            layer.smooth: true
            antialiasing: true
        }

        // 粒子系统
        Item {
            id: particleSystem
            anchors.fill: parent

            function createExplosion(x, y, color) {
                for (let i = 0; i < 15; i++) {
                    let angle = Math.random() * Math.PI * 2
                    let speed = 100 + Math.random() * 100

                    let particle = particleComponent.createObject(particleSystem, {
                        "x": x,
                        "y": y,
                        "particleColor": color,
                        "vx": Math.cos(angle) * speed,
                        "vy": Math.sin(angle) * speed
                    })
                }
            }
        }

        Component {
            id: particleComponent

            Rectangle {
                id: particle
                width: 6
                height: 6
                radius: 3

                property color particleColor
                property real vx: 0
                property real vy: 0
                property real lifetime: 1.0

                color: particleColor
                opacity: lifetime

                Timer {
                    running: true
                    repeat: true
                    interval: 16
                    onTriggered: {
                        particle.x += particle.vx * 0.016
                        particle.y += particle.vy * 0.016
                        particle.vy += 500 * 0.016  // 重力
                        particle.lifetime -= 0.016 / 1.0

                        if (particle.lifetime <= 0) {
                            particle.destroy()
                        }
                    }
                }
            }
        }

        // UI 文字
        Text {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: 20
            text: gameController && gameController.state ? "分数 Score: " + gameController.state.score : "分数 Score: 0"
            font.family: "Noto Sans CJK SC"
            font.pixelSize: 24
            color: "white"
        }

        Text {
            anchors.centerIn: parent
            text: gameController && gameController.state ? gameController.state.message : ""
            font.family: "Noto Sans CJK SC"
            font.pixelSize: 32
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            visible: gameController && gameController.state && gameController.state.message !== ""
        }
    }  // 主 Item 结束
}
