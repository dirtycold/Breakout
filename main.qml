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

    // 游戏状态枚举（从 Python constants 读取）
    GameStatusProvider {
        id: gameStatus
    }

    // 游戏控制器（Python 后端）
    GameController {
        id: gameController
    }

    // 主游戏区域（用于接收键盘输入）
    Item {
        anchors.fill: parent
        focus: true

        Keys.onPressed: (event) => {
            if (event.key === Qt.Key_Space && gameController && gameController.state && gameController.state.gameStatus === gameStatus.NOT_STARTED) {
                gameController.startGame()
            } else if (event.key === Qt.Key_R) {
                paddle.x = (root.width - paddle.width) / 2
                gameController.updatePaddle(paddle.x, paddle.y, paddle.width)
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
                gameController.updatePaddle(paddle.x, paddle.y, paddle.width)
            }
        }

        // 砖块容器
        Item {
            id: brickContainer
            anchors.fill: parent

            Repeater {
                id: brickRepeater
                model: gameController.brickModel

                delegate: Rectangle {
                    id: brick
                    x: model.brickX
                    y: model.brickY
                    width: model.brickWidth
                    height: model.brickHeight
                    radius: config.brickCornerRadius
                    color: model.brickColor
                    visible: !model.destroyed
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

                    gameController.updatePaddle(paddle.x, paddle.y, paddle.width)
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

            Repeater {
                id: particleRepeater
                model: gameController.particleModel

                delegate: Rectangle {
                    id: particle
                    x: model.particleX
                    y: model.particleY
                    width: config.particleDiameter
                    height: config.particleDiameter
                    radius: config.particleRadius
                    color: model.particleColor
                    opacity: model.particleOpacity
                }
            }
        }

        // UI 文字
        Text {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.leftMargin: config.scoreMarginX
            anchors.topMargin: config.scoreMarginTop
            text: gameController && gameController.state ? config.scoreLabel + ": " + gameController.state.score : config.scoreLabel + ": 0"
            font.pixelSize: config.scoreFontSize
            color: "white"
        }

        Column {
            id: messageOverlay
            anchors.centerIn: parent
            spacing: config.messageLineSpacing
            visible: gameController && gameController.state && gameController.state.gameStatus !== gameStatus.PLAYING

            property var messageLines: gameController && gameController.state ? gameController.state.message.split("\n") : []

            function messageLine(lineIndex) {
                return lineIndex < messageLines.length ? messageLines[lineIndex] : ""
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: messageOverlay.messageLine(0)
                font.pixelSize: config.messagePrimaryFontSize
                color: "white"
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: messageOverlay.messageLine(1)
                font.pixelSize: config.messageSecondaryFontSize
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                visible: text.length > 0
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: messageOverlay.messageLine(2)
                font.pixelSize: config.messageHintFontSize
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                visible: text.length > 0
            }
        }
    }  // 主 Item 结束
}
