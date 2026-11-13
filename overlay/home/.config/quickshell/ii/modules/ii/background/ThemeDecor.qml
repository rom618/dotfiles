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
                    model: root.decor === "stars" ? 60 : (root.decor === "leaves" ? 18 : 30)
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
                    property real size: 6
                    property real duration: 12000
                    property color tint: "white"
                    readonly property bool rising: root.decor === "bubbles"

                    function reset() {
                        startX = Math.random() * field.width;
                        if (root.decor === "snow") {
                            size = 3 + Math.random() * 6;
                            sway = 20 + Math.random() * 50;
                            duration = 10000 + Math.random() * 10000;
                            tint = "white";
                        } else if (root.decor === "leaves") {
                            size = 16 + Math.random() * 12;
                            sway = 60 + Math.random() * 90;
                            duration = 13000 + Math.random() * 11000;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (180 + Math.random() * 360);
                            const greens = ["#52B788", "#74C69D", "#95D5B2", "#E9C46A", "#40916C"];
                            tint = greens[Math.floor(Math.random() * greens.length)];
                        } else {
                            size = 8 + Math.random() * 20;
                            sway = 15 + Math.random() * 35;
                            duration = 12000 + Math.random() * 14000;
                            const mints = ["#FFFFFF", "#C7F9CC", "#80ED99", "#38A3A5"];
                            tint = mints[Math.floor(Math.random() * mints.length)];
                        }
                        swayCycles = 0.6 + Math.random() * 1.4;
                    }

                    width: size
                    height: size
                    x: startX + sway * Math.sin(progress * Math.PI * 2 * swayCycles)
                    y: rising ? field.height + 30 - progress * (field.height + 60) : -30 + progress * (field.height + 60)
                    rotation: spin * progress
                    opacity: rising ? 0.75 * (1 - progress * 0.8) : (root.decor === "snow" ? 0.85 : 0.9)

                    Rectangle {
                        visible: root.decor === "snow"
                        anchors.fill: parent
                        radius: width / 2
                        color: p.tint
                    }

                    Rectangle {
                        visible: root.decor === "bubbles"
                        anchors.fill: parent
                        radius: width / 2
                        color: Qt.rgba(p.tint.r, p.tint.g, p.tint.b, 0.18)
                        border.width: 1.5
                        border.color: p.tint
                        Rectangle {
                            width: parent.width * 0.25
                            height: width
                            radius: width / 2
                            x: parent.width * 0.22
                            y: parent.height * 0.2
                            color: "#FFFFFF"
                            opacity: 0.8
                        }
                    }

                    MaterialSymbol {
                        visible: root.decor === "leaves"
                        anchors.centerIn: parent
                        text: "eco"
                        fill: 1
                        iconSize: p.size
                        color: p.tint
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
                    property real size: 1.5 + Math.random() * 2.5
                    x: Math.random() * field.width
                    y: Math.pow(Math.random(), 1.4) * field.height * 0.75
                    width: size * 4
                    height: size * 4

                    Rectangle {
                        anchors.centerIn: parent
                        width: s.size
                        height: s.size
                        radius: width / 2
                        color: Math.random() < 0.25 ? "#F5D687" : "#E6E9FF"
                    }
                    Rectangle {
                        visible: s.size > 3
                        anchors.centerIn: parent
                        width: s.size * 4
                        height: 1
                        color: "#E6E9FF"
                        opacity: 0.6
                    }
                    Rectangle {
                        visible: s.size > 3
                        anchors.centerIn: parent
                        width: 1
                        height: s.size * 4
                        color: "#E6E9FF"
                        opacity: 0.6
                    }

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        PauseAnimation { duration: Math.random() * 4000 }
                        NumberAnimation { from: 0.15; to: 1; duration: 1200 + Math.random() * 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1; to: 0.15; duration: 1200 + Math.random() * 1800; easing.type: Easing.InOutSine }
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
