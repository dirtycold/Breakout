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
    property real paddleVisualX: (width - config.paddleWidth) / 2

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

    // Qt maps "Ctrl" to Command and "Meta" to physical Control on macOS.
    // Window-level shortcuts avoid depending on which game item owns focus.
    Shortcut {
        sequences: ["Ctrl+F1", "Meta+F1"]
        autoRepeat: false
        onActivated: gameController.handleCheat(1, false)
    }

    Shortcut {
        sequences: ["Ctrl+F2", "Meta+F2"]
        autoRepeat: false
        onActivated: gameController.handleCheat(2, false)
    }

    Shortcut {
        sequences: ["Ctrl+Shift+F2", "Meta+Shift+F2"]
        autoRepeat: false
        onActivated: gameController.handleCheat(2, true)
    }

    Shortcut {
        sequences: ["Ctrl+F3", "Meta+F3"]
        autoRepeat: false
        onActivated: gameController.handleCheat(3, false)
    }

    Shortcut {
        sequences: ["Ctrl+Shift+F3", "Meta+Shift+F3"]
        autoRepeat: false
        onActivated: gameController.handleCheat(3, true)
    }

    Shortcut {
        sequences: ["Ctrl+F4", "Meta+F4"]
        autoRepeat: false
        onActivated: gameController.handleCheat(4, false)
    }

    Shortcut {
        sequences: ["Ctrl+Shift+F4", "Meta+Shift+F4"]
        autoRepeat: false
        onActivated: gameController.handleCheat(4, true)
    }

    Connections {
        target: gameController

        function onPaddleXChanged(paddleX) {
            root.paddleVisualX = paddleX
        }
    }

    // 主游戏区域（用于接收键盘输入）
    Item {
        anchors.fill: parent
        focus: true

        Keys.onPressed: (event) => {
            if (event.isAutoRepeat) {
                event.accepted = true
                return
            }

            if (event.key === Qt.Key_Space) {
                gameController.handleSpace()
                event.accepted = true
            } else if (event.key === Qt.Key_Left) {
                gameController.setPaddleMovingLeft(true)
                event.accepted = true
            } else if (event.key === Qt.Key_Right) {
                gameController.setPaddleMovingRight(true)
                event.accepted = true
            }
        }

        Keys.onReleased: (event) => {
            if (event.isAutoRepeat) {
                event.accepted = true
                return
            }

            if (event.key === Qt.Key_Left) {
                gameController.setPaddleMovingLeft(false)
                event.accepted = true
            } else if (event.key === Qt.Key_Right) {
                gameController.setPaddleMovingRight(false)
                event.accepted = true
            }
        }

        // 鼠标控制
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton
            onPositionChanged: function(mouse) {
                if (gameController.state.gameStatus === gameStatus.PAUSED) {
                    return
                }
                var nextX = Math.max(
                    0,
                    Math.min(root.width - paddle.width, mouse.x - paddle.width / 2)
                )
                // Update the visible paddle before crossing the QML/Python boundary.
                root.paddleVisualX = nextX
                gameController.setPaddleX(nextX)
            }
            onPressed: function(mouse) {
                gameController.handlePrimaryAction()
                mouse.accepted = true
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

        // 奖励物件
        Item {
            id: rewardContainer
            anchors.fill: parent

            Repeater {
                model: gameController.rewardModel

                delegate: Item {
                    x: model.rewardX
                    y: model.rewardY
                    width: model.rewardSize
                    height: model.rewardSize
                    rotation: model.rewardRotation

                    Image {
                        anchors.fill: parent
                        source: model.rewardTexture
                        smooth: true
                        mipmap: true
                    }
                }
            }
        }

        // 挡板
        Item {
            id: laserBulletContainer
            anchors.fill: parent

            Repeater {
                model: gameController.laserModel

                delegate: Rectangle {
                    x: model.bulletX
                    y: model.bulletY
                    width: model.bulletWidth
                    height: model.bulletHeight
                    radius: width / 2
                    color: config.laserBulletColor
                }
            }
        }

        Rectangle {
            id: paddle
            width: gameController.paddleWidth
            height: config.paddleHeight
            color: "transparent"
            radius: config.paddleCornerRadius
            x: root.paddleVisualX
            y: config.paddleY

            property real gradientOffset: 0
            property int frameIndex: 0
            property int magnetFrameIndex: 0

            Item {
                id: paddleTextureViewport
                anchors.fill: parent
                clip: true

                Image {
                    id: paddleTexture
                    x: -paddle.frameIndex * paddle.width
                    y: 0
                    width: paddle.width * config.paddleGradientFrameCount
                    height: config.paddleHeight
                    source: gameController.paddleTextureSource
                    fillMode: Image.Stretch
                    smooth: false
                    cache: true
                    asynchronous: false
                }
            }

            Rectangle {
                visible: gameController.laserActive
                width: config.laserGunWidth
                height: config.laserGunHeight
                radius: width / 2
                color: config.laserGunColor
                x: config.laserGunSideInset
                y: -height + 3
            }

            Rectangle {
                visible: gameController.laserActive
                width: config.laserGunWidth
                height: config.laserGunHeight
                radius: width / 2
                color: config.laserGunColor
                x: paddle.width - config.laserGunSideInset - width
                y: -height + 3
            }

            Item {
                visible: gameController.ball.magnetAttached
                width: config.magnetEffectWidth
                height: config.magnetEffectHeight
                x: paddle.width / 2
                   + gameController.magnetEffectCenterOffset
                   - width / 2
                y: -config.magnetEffectDeckY
                clip: true

                Image {
                    x: -paddle.magnetFrameIndex * config.magnetEffectWidth
                    y: 0
                    width: config.magnetEffectWidth * config.magnetEffectFrameCount
                    height: config.magnetEffectHeight
                    source: gameController.magnetEffectTextureSource
                    smooth: false
                    cache: true
                }
            }

            // 键盘移动逻辑
            Timer {
                running: true
                repeat: true
                interval: config.frameIntervalMs
                onTriggered: {
                    paddle.gradientOffset = (paddle.gradientOffset + config.paddleGradientScrollSpeed * config.fixedDeltaTime) % paddle.width
                    var nextFrameIndex = Math.floor(
                        paddle.gradientOffset / paddle.width * config.paddleGradientFrameCount
                    ) % config.paddleGradientFrameCount
                    if (nextFrameIndex !== paddle.frameIndex) {
                        paddle.frameIndex = nextFrameIndex
                    }
                }
            }

            Timer {
                running: gameController.ball.magnetAttached
                         && gameController.state.gameStatus === gameStatus.PLAYING
                repeat: true
                interval: config.magnetEffectFrameIntervalMs
                onTriggered: {
                    paddle.magnetFrameIndex =
                        (paddle.magnetFrameIndex + 1) % config.magnetEffectFrameCount
                }
            }
        }

        // 球（彩虹条纹）
        Item {
            id: ball
            width: config.ballDiameter
            height: config.ballDiameter
            x: gameController && gameController.ball ? gameController.ball.x - config.ballRadius : paddle.x + paddle.width / 2 - config.ballRadius
            y: gameController && gameController.ball ? gameController.ball.y - config.ballRadius : config.ballStartCenterY - config.ballRadius

            Image {
                anchors.fill: parent
                source: gameController && gameController.ball ? gameController.ball.textureSource : ""
                rotation: gameController && gameController.ball ? gameController.ball.rotation : 0
                transformOrigin: Item.Center
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
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
            font.family: config.gameFontFamily
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
                font.family: config.gameFontFamily
                color: "white"
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: messageOverlay.messageLine(1)
                font.pixelSize: config.messageSecondaryFontSize
                font.family: config.gameFontFamily
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                visible: text.length > 0
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: messageOverlay.messageLine(2)
                font.pixelSize: config.messageHintFontSize
                font.family: config.gameFontFamily
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                visible: text.length > 0
            }
        }
    }  // 主 Item 结束
}
