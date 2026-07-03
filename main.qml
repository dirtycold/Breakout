import QtQuick
import QtQuick.Window
import GameLogic 1.0

Window {
    id: root
    width: config.screenWidth
    height: config.screenHeight
    visible: true
    title: config.screenTitleQml
    color: config.backgroundColor

    // 游戏配置（从 Python constants 读取）
    GameConfigProvider {
        id: config
    }

    // 计算砖块数量（菱形布局）
    function calculateBrickCount() {
        return config.totalBrickCount()
    }

    // 游戏状态枚举（从 Python constants 读取）
    GameStatusProvider {
        id: gameStatus
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
            if (event.key === Qt.Key_Space && gameController && gameController.state && gameController.state.gameStatus === gameStatus.NOT_STARTED) {
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
                    width: config.brickWidth
                    height: config.brickHeight
                    radius: config.brickCornerRadius

                    property int brickIndex: index
                    property bool destroyed: false

                    // 计算砖块位置（菱形布局）
                    Component.onCompleted: {
                        let currentIndex = brickIndex
                        let currentRow = 0
                        let posInRow = 0

                        // 找到当前砖块在哪一行
                        for (let row = 0; row < config.brickRows; row++) {
                            let rowBrickCount = config.bricksInRow(row)
                            if (currentIndex < rowBrickCount) {
                                currentRow = row
                                posInRow = currentIndex
                                break
                            }
                            currentIndex -= rowBrickCount
                        }

                        brick.x = config.brickX(currentRow, posInRow)
                        brick.y = config.brickY(currentRow)

                        // 设置颜色（从 Python constants 读取）
                        brick.color = config.brickColors[currentRow % config.brickColors.length]
                    }

                    // 碰撞检测（每帧）
                    Timer {
                        running: !brick.destroyed
                        repeat: true
                        interval: config.frameIntervalMs
                        onTriggered: {
                            if (gameController && gameController.state &&
                                gameController.state.gameStatus === gameStatus.PLAYING &&
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
            width: config.paddleWidth
            height: config.paddleHeight
            color: config.paddleColor
            radius: config.paddleCornerRadius
            x: (root.width - width) / 2
            y: config.paddleY

            property bool moveLeft: false
            property bool moveRight: false

            // 键盘移动逻辑
            Timer {
                running: true
                repeat: true
                interval: config.frameIntervalMs
                onTriggered: {
                    if (paddle.moveLeft) {
                        paddle.x = Math.max(0, paddle.x - config.paddleMoveStep)
                    }
                    if (paddle.moveRight) {
                        paddle.x = Math.min(root.width - paddle.width, paddle.x + config.paddleMoveStep)
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
            width: config.ballDiameter
            height: config.ballDiameter
            radius: config.ballRadius
            x: gameController && gameController.ball ? gameController.ball.x - config.ballRadius : paddle.x + paddle.width / 2 - config.ballRadius
            y: gameController && gameController.ball ? gameController.ball.y - config.ballRadius : config.ballStartCenterY - config.ballRadius
            color: config.ballColor

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
                for (let i = 0; i < config.particleCount; i++) {
                    let angle = Math.random() * Math.PI * 2
                    let speed = config.particleMinSpeed + Math.random() * (config.particleMaxSpeed - config.particleMinSpeed)

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
                width: config.particleDiameter
                height: config.particleDiameter
                radius: config.particleRadius

                property color particleColor
                property real vx: 0
                property real vy: 0
                property real lifetime: config.particleLifetime

                color: particleColor
                opacity: Math.max(0, lifetime / config.particleLifetime)

                Timer {
                    running: true
                    repeat: true
                    interval: config.frameIntervalMs
                    onTriggered: {
                        particle.x += particle.vx * config.fixedDeltaTime
                        particle.y += particle.vy * config.fixedDeltaTime
                        particle.vy += config.particleGravity * config.fixedDeltaTime
                        particle.lifetime -= config.fixedDeltaTime

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
            visible: gameController && gameController.state && gameController.state.gameStatus !== gameStatus.PLAYING
        }
    }  // 主 Item 结束
}
