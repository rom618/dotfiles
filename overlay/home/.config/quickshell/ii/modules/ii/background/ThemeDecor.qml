import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Scope {
    id: root
    property string themeDecor: ""
    property bool particlesOn: true
    readonly property string decor: particlesOn ? themeDecor : ""
    property string shownDecor: ""
    property real decorOpacity: 0

    onDecorChanged: decorSwap.restart()
    Component.onCompleted: decorSwap.restart()

    SequentialAnimation {
        id: decorSwap
        NumberAnimation {
            target: root
            property: "decorOpacity"
            to: 0
            duration: root.shownDecor === "" ? 0 : 350
            easing.type: Easing.InOutCubic
        }
        ScriptAction {
            script: root.shownDecor = root.decor
        }
        NumberAnimation {
            target: root
            property: "decorOpacity"
            to: 1
            duration: 600
            easing.type: Easing.InOutCubic
        }
    }

    FileView {
        path: `${Directories.state}/user/generated/theme-prefs.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.particlesOn = JSON.parse(text()).particles !== false;
            } catch (e) {
                root.particlesOn = true;
            }
        }
    }

    FileView {
        path: `${Directories.state}/user/generated/theme.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.themeDecor = JSON.parse(text()).decor ?? "";
            } catch (e) {
                root.themeDecor = "";
            }
        }
        onLoadFailed: root.themeDecor = ""
    }

    Variants {
        model: root.shownDecor !== "" ? Quickshell.screens : []

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
                opacity: root.decorOpacity

                Repeater {
                    model: ({ stars: 70, leaves: 22, autumn: 22, petals: 28, snow: 45, sand: 90, rain: 140, embers: 40, fireflies: 30, ocean: 30 })[root.shownDecor] ?? 26
                    delegate: Loader {
                        required property int index
                        sourceComponent: root.shownDecor === "stars" ? star : drifter
                    }
                }

                Loader {
                    active: root.shownDecor === "stars"
                    sourceComponent: shootingStar
                }

                Loader {
                    active: root.shownDecor === "sand"
                    sourceComponent: tumbleweed
                }
            }

            Component {
                id: drifter
                Item {
                    id: p
                    property real progress: 0
                    property real startX: 0
                    property real startY: 0
                    property real sway: 40
                    property real swayCycles: 1
                    property real spin: 0
                    property real depth: 1
                    property real size: 12
                    property real duration: 12000
                    property real blinks: 3
                    property string asset: ""
                    property color tint: "#D9A066"
                    readonly property string kind: root.shownDecor
                    readonly property bool rising: kind === "bubbles" || kind === "embers" || kind === "ocean"
                    readonly property bool windy: kind === "sand"
                    readonly property bool wander: kind === "fireflies"
                    readonly property bool rain: kind === "rain"
                    readonly property bool flat: windy || rain
                    readonly property bool tumble: kind === "leaves" || kind === "autumn" || kind === "petals"
                    readonly property bool jelly: asset.startsWith("jellyfish")

                    function pick(list) {
                        return list[Math.floor(Math.random() * list.length)];
                    }

                    function reset() {
                        startX = Math.random() * field.width;
                        startY = Math.random() * field.height;
                        depth = 0.45 + Math.random() * 0.55;
                        swayCycles = 0.6 + Math.random() * 1.4;
                        spin = 0;
                        asset = "";
                        if (kind === "snow") {
                            size = (10 + Math.random() * 18) * depth;
                            sway = (20 + Math.random() * 45) * depth;
                            duration = (16000 + Math.random() * 10000) / depth;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (60 + Math.random() * 180);
                            asset = pick(["snowflake-1", "snowflake-2", "snowflake-3"]);
                        } else if (kind === "leaves" || kind === "autumn") {
                            size = (20 + Math.random() * 18) * depth;
                            sway = (70 + Math.random() * 110) * depth;
                            duration = (15000 + Math.random() * 12000) / depth;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (240 + Math.random() * 420);
                            asset = kind === "leaves" ? pick(["leaf-green", "leaf-lime", "leaf-gold", "leaf-amber", "leaf-moss"])
                                                      : pick(["leaf-red", "leaf-rust", "leaf-orange", "leaf-yellow", "leaf-amber"]);
                        } else if (kind === "petals") {
                            size = (12 + Math.random() * 12) * depth;
                            sway = (60 + Math.random() * 120) * depth;
                            duration = (18000 + Math.random() * 12000) / depth;
                            spin = (Math.random() < 0.5 ? -1 : 1) * (120 + Math.random() * 260);
                            asset = pick(["petal-pink", "petal-blush", "petal-white"]);
                        } else if (kind === "sand") {
                            startY = field.height * (0.35 + Math.pow(Math.random(), 0.7) * 0.65);
                            size = (2 + Math.random() * 3.5) * depth;
                            sway = (10 + Math.random() * 40) * depth;
                            duration = (5000 + Math.random() * 5000) / depth;
                            tint = pick(["#E0B07A", "#D9A066", "#C9824E", "#F2CE96", "#B5713F"]);
                        } else if (kind === "rain") {
                            size = (18 + Math.random() * 30) * depth;
                            sway = 0;
                            duration = (650 + Math.random() * 550) / depth;
                            tint = pick(["#3EE6FF", "#FF4FD8", "#C9F6FF", "#8A80B0"]);
                        } else if (kind === "embers") {
                            size = (6 + Math.random() * 12) * depth;
                            sway = (20 + Math.random() * 60) * depth;
                            duration = (7000 + Math.random() * 7000) / depth;
                            blinks = 4 + Math.random() * 6;
                            asset = pick(["ember", "ember", "ember-red"]);
                        } else if (kind === "fireflies") {
                            startY = field.height * (0.3 + Math.random() * 0.65);
                            size = (12 + Math.random() * 14) * depth;
                            sway = (60 + Math.random() * 140) * depth;
                            duration = 12000 + Math.random() * 12000;
                            blinks = 2 + Math.random() * 4;
                            asset = "firefly";
                        } else if (kind === "ocean") {
                            if (Math.random() < 0.18) {
                                size = (44 + Math.random() * 40) * depth;
                                sway = (20 + Math.random() * 40) * depth;
                                duration = (30000 + Math.random() * 20000) / depth;
                                asset = pick(["jellyfish-cyan", "jellyfish-violet", "jellyfish-pink"]);
                            } else {
                                size = (8 + Math.random() * 18) * depth;
                                sway = (12 + Math.random() * 25) * depth;
                                duration = (12000 + Math.random() * 10000) / depth;
                                asset = pick(["bubble-white", "bubble-teal"]);
                            }
                        } else {
                            size = (14 + Math.random() * 30) * depth;
                            sway = (12 + Math.random() * 30) * depth;
                            duration = (14000 + Math.random() * 14000) / depth;
                            asset = pick(["bubble-white", "bubble-mint", "bubble-teal"]);
                        }
                    }

                    width: rain ? 1.6 : size
                    height: size
                    x: windy ? -40 + progress * (field.width + 80)
                       : rain ? startX - 140 + progress * 260
                       : startX + sway * Math.sin(progress * Math.PI * 2 * swayCycles)
                    y: windy ? startY + sway * Math.sin(progress * Math.PI * 2 * swayCycles) - progress * 60 * depth
                       : wander ? startY + sway * 0.6 * Math.cos(progress * Math.PI * 2 * swayCycles * 0.7)
                       : rain ? -60 + progress * (field.height + 120)
                       : rising ? field.height + 40 - progress * (field.height + 80)
                       : -40 + progress * (field.height + 80)
                    rotation: rain ? 28 : spin * progress
                    opacity: {
                        const d = 0.45 + 0.55 * depth;
                        if (kind === "embers")
                            return d * (1 - progress) * (0.55 + 0.45 * Math.abs(Math.sin(progress * Math.PI * blinks)));
                        if (wander)
                            return d * (0.08 + 0.92 * Math.pow(Math.max(0, Math.sin(progress * Math.PI * 2 * blinks)), 2));
                        if (rain)
                            return 0.5 * d;
                        if (rising)
                            return 0.95 * (1 - progress * 0.7) * d;
                        return 0.95 * d;
                    }
                    transform: Scale {
                        origin.x: p.width / 2
                        origin.y: p.height / 2
                        xScale: p.tumble ? Math.cos(p.progress * Math.PI * 2 * p.swayCycles * 2) : 1
                        yScale: p.jelly ? 1 + 0.12 * Math.sin(p.progress * Math.PI * 40)
                                : (p.kind === "bubbles" || p.kind === "ocean" ? 1 + 0.06 * Math.sin(p.progress * Math.PI * 14) : 1)
                    }

                    Rectangle {
                        visible: p.flat
                        anchors.fill: parent
                        radius: p.rain ? 1 : width / 2
                        color: p.tint
                    }

                    Image {
                        visible: !p.flat
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
                id: tumbleweed
                Item {
                    id: tw
                    property real progress: 0
                    property real size: 70
                    width: size
                    height: size
                    x: -size + progress * (field.width + size * 2)
                    y: field.height - size - 30 - Math.abs(Math.sin(progress * Math.PI * 9)) * 70 * (1 - progress * 0.4)
                    rotation: progress * 360 * 6
                    opacity: progress > 0 && progress < 1 ? 0.9 : 0

                    Image {
                        anchors.fill: parent
                        source: Quickshell.shellPath("assets/decor/tumbleweed.svg")
                        sourceSize.width: 128
                        sourceSize.height: 128
                        smooth: true
                        mipmap: true
                    }

                    SequentialAnimation {
                        running: true
                        loops: Animation.Infinite
                        PauseAnimation { duration: 6000 + Math.random() * 10000 }
                        ScriptAction { script: tw.size = 50 + Math.random() * 40 }
                        NumberAnimation { target: tw; property: "progress"; from: 0; to: 1; duration: 9000; easing.type: Easing.Linear }
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
