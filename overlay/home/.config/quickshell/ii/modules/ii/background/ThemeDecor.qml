import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Scope {
    id: root
    property string decor: ""

    FileView {
        path: `${Directories.state}/user/generated/theme.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.decor = JSON.parse(text()).decor ?? "";
            } catch (e) {
                root.decor = "";
            }
        }
        onLoadFailed: root.decor = ""
    }

    Variants {
        model: root.decor !== "" ? Quickshell.screens : []

        PanelWindow {
            id: win
            required property var modelData
            screen: modelData
            color: "transparent"
            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }
            exclusionMode: ExclusionMode.Ignore
            exclusiveZone: 0
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.namespace: "quickshell:themeDecor"
            mask: Region {}

            Item {
                id: field
                anchors.fill: parent

                Repeater {
                    model: root.decor === "stars" ? 70 : (root.decor === "leaves" ? 22 : (root.decor === "snow" ? 45 : 26))
                    delegate: Loader {
                        required property int index
                        sourceComponent: root.decor === "stars" ? star : drifter
                    }
                }

                Loader {
                    active: root.decor === "stars"
                    sourceComponent: shootingStar
                }
            }

            Component {
                id: drifter
                Item {
                    id: p
                    property real progress: 0
                    property real startX: 0
                    property real sway: 40
                    property real swayCycles: 1
                    property real spin: 0
                    property real depth: 1
                    property real size: 12
                    property real duration: 12000
                    property string asset: ""
                    readonly property bool rising: root.decor === "bubbles"

                    function pick(list) {
                        return list[Math.floor(Math.random() * list.length)];
                    }

                    function reset() {
                        startX = Math.random() * field.width;
                        depth = 0.45 + Math.random() * 0.55;
                        swayCycles = 0.6 + Math.random() * 1.4;
                        if (root.decor === "snow") {
                            size = (10 + Math.random() * 18) * depth;
                            sway = (20 + Math.random() * 45) * depth;
                            duration = (16000 + Math.random() * 10000) / depth;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (60 + Math.random() * 180);
                            asset = pick(["snowflake-1", "snowflake-2", "snowflake-3"]);
                        } else if (root.decor === "leaves") {
                            size = (20 + Math.random() * 18) * depth;
                            sway = (70 + Math.random() * 110) * depth;
                            duration = (15000 + Math.random() * 12000) / depth;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (240 + Math.random() * 420);
                            asset = pick(["leaf-green", "leaf-lime", "leaf-gold", "leaf-amber", "leaf-moss"]);
                        } else {
                            size = (14 + Math.random() * 30) * depth;
                            sway = (12 + Math.random() * 30) * depth;
                            duration = (14000 + Math.random() * 14000) / depth;
                            spin = 0;
                            asset = pick(["bubble-white", "bubble-mint", "bubble-teal"]);
                        }
                    }

                    width: size
                    height: size
                    x: startX + sway * Math.sin(progress * Math.PI * 2 * swayCycles)
                    y: rising ? field.height + 40 - progress * (field.height + 80) : -40 + progress * (field.height + 80)
                    rotation: spin * progress
                    opacity: (rising ? 0.95 * (1 - progress * 0.7) : 0.95) * (0.45 + 0.55 * depth)
                    transform: Scale {
                        origin.x: p.width / 2
                        origin.y: p.height / 2
                        xScale: root.decor === "leaves" ? Math.cos(p.progress * Math.PI * 2 * p.swayCycles * 2) : 1
                        yScale: root.decor === "bubbles" ? 1 + 0.06 * Math.sin(p.progress * Math.PI * 14) : 1
                    }

                    Image {
                        anchors.fill: parent
                        source: p.asset ? Quickshell.shellPath(`assets/decor/${p.asset}.svg`) : ""
                        sourceSize.width: 96
                        sourceSize.height: 96
                        smooth: true
                        mipmap: true
                    }

                    NumberAnimation {
                        id: fall
                        target: p
                        property: "progress"
                        to: 1
                        onFinished: {
                            p.reset();
                            fall.from = 0;
                            fall.duration = p.duration;
                            fall.start();
                        }
                    }

                    Component.onCompleted: {
                        reset();
                        const start = Math.random();
                        fall.from = start;
                        fall.duration = duration * (1 - start);
                        fall.start();
                    }
                }
            }

            Component {
                id: star
                Item {
                    id: s
                    readonly property bool sparkle: Math.random() < 0.22
                    property real size: sparkle ? 12 + Math.random() * 14 : 1.5 + Math.random() * 2.5
                    x: Math.random() * field.width
                    y: Math.pow(Math.random(), 1.4) * field.height * 0.75
                    width: s.sparkle ? s.size : s.size * 4
                    height: width

                    Rectangle {
                        visible: !s.sparkle
                        anchors.centerIn: parent
                        width: s.size
                        height: s.size
                        radius: width / 2
                        color: Math.random() < 0.25 ? "#F5D687" : "#E6E9FF"
                    }
                    Image {
                        visible: s.sparkle
                        anchors.fill: parent
                        source: s.sparkle ? Quickshell.shellPath(Math.random() < 0.35 ? "assets/decor/sparkle-gold.svg" : "assets/decor/sparkle-white.svg") : ""
                        sourceSize.width: 64
                        sourceSize.height: 64
                        smooth: true
                        mipmap: true
                    }

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        PauseAnimation { duration: Math.random() * 4000 }
                        NumberAnimation { from: 0.15; to: 1; duration: 1200 + Math.random() * 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1; to: 0.15; duration: 1200 + Math.random() * 1800; easing.type: Easing.InOutSine }
                    }
                    SequentialAnimation on scale {
                        running: s.sparkle
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.7; to: 1.15; duration: 1800 + Math.random() * 1500; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1.15; to: 0.7; duration: 1800 + Math.random() * 1500; easing.type: Easing.InOutSine }
                    }
                }
            }

            Component {
                id: shootingStar
                Item {
                    id: meteor
                    property real progress: 0
                    property real sx: 0
                    property real sy: 0
                    width: 140
                    height: 2
                    rotation: 28
                    x: sx + progress * 520
                    y: sy + progress * 280
                    opacity: progress < 0.15 ? progress / 0.15 : 1 - progress

                    Rectangle {
                        anchors.fill: parent
                        radius: 1
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: "transparent" }
                            GradientStop { position: 1; color: "#FFFFFF" }
                        }
                    }

                    SequentialAnimation {
                        running: true
                        loops: Animation.Infinite
                        PauseAnimation { duration: 9000 }
                        ScriptAction {
                            script: {
                                meteor.sx = Math.random() * field.width * 0.7;
                                meteor.sy = Math.random() * field.height * 0.3;
                            }
                        }
                        NumberAnimation { target: meteor; property: "progress"; from: 0; to: 1; duration: 900; easing.type: Easing.OutQuad }
                    }
                }
            }
        }
    }
}
