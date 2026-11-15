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

    readonly property var kinds: ({ bubbles: 0, snow: 1, leaves: 2, autumn: 3, petals: 4, sand: 5, rain: 6, embers: 7, fireflies: 8, ocean: 9, stars: 10 })
    readonly property var counts: ({ stars: 70, leaves: 22, autumn: 22, petals: 28, snow: 45, sand: 90, rain: 140, embers: 40, fireflies: 30, ocean: 30 })
    readonly property var atlases: ({
        bubbles: ["bubble-white", "bubble-mint", "bubble-teal"],
        snow: ["snowflake-1", "snowflake-2", "snowflake-3"],
        leaves: ["leaf-green", "leaf-lime", "leaf-gold", "leaf-amber", "leaf-moss"],
        autumn: ["leaf-red", "leaf-rust", "leaf-orange", "leaf-yellow", "leaf-amber"],
        petals: ["petal-pink", "petal-blush", "petal-white"],
        embers: ["ember", "ember", "ember-red"],
        fireflies: ["firefly"],
        ocean: ["bubble-white", "bubble-teal", "jellyfish-cyan", "jellyfish-violet", "jellyfish-pink"],
        stars: ["sparkle-white", "sparkle-gold"]
    })
    readonly property int kind: kinds[shownDecor] ?? 0
    readonly property int count: counts[shownDecor] ?? 26
    readonly property var atlas: atlases[shownDecor] ?? (shownDecor === "sand" || shownDecor === "rain" ? [""] : atlases.bubbles)

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
                visible: GraphicsInfo.api !== GraphicsInfo.Software

                Row {
                    id: atlasRow
                    spacing: 8
                    leftPadding: 4
                    rightPadding: 4
                    topPadding: 4
                    bottomPadding: 4

                    Repeater {
                        model: root.atlas
                        delegate: Image {
                            required property string modelData
                            width: 96
                            height: 96
                            source: modelData ? Quickshell.shellPath(`assets/decor/${modelData}.svg`) : ""
                            sourceSize.width: 96
                            sourceSize.height: 96
                            smooth: true
                        }
                    }
                }

                ShaderEffectSource {
                    id: atlasTexture
                    sourceItem: atlasRow
                    hideSource: true
                    mipmap: true
                    smooth: true
                    width: 0
                    height: 0
                }

                ShaderEffect {
                    id: particles
                    anchors.fill: parent
                    property var atlas: atlasTexture
                    property real time: 0
                    property real kind: root.kind
                    property real cols: root.count * 4 - 1
                    property real cells: root.atlas.length
                    property real seed: Math.random() * 100
                    property size field: Qt.size(width, height)
                    mesh: GridMesh {
                        resolution: Qt.size(root.count * 4 - 1, 1)
                    }
                    vertexShader: Qt.resolvedUrl("decor/particles.vert.qsb")
                    fragmentShader: Qt.resolvedUrl("decor/particles.frag.qsb")

                    readonly property real startedAt: Date.now()

                    Timer {
                        running: field.visible && root.decorOpacity > 0
                        repeat: true
                        interval: root.shownDecor === "rain" ? 22 : 33
                        onTriggered: particles.time = ((Date.now() - particles.startedAt) / 1000) % 3600
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
                id: tumbleweed
                Item {
                    id: tw
                    readonly property real cycle: Math.floor(particles.time / 22)
                    readonly property real pause: 6 + (Math.abs(Math.sin(cycle * 12.9898 + particles.seed) * 43758.5453) % 1) * 7
                    readonly property real progress: Math.max(0, Math.min(1, (particles.time - cycle * 22 - pause) / 9))
                    readonly property real size: 50 + (Math.abs(Math.sin(cycle * 78.233 + particles.seed) * 43758.5453) % 1) * 40
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
                }
            }

            Component {
                id: shootingStar
                Item {
                    id: meteor
                    readonly property real cycle: Math.floor(particles.time / 9.9)
                    readonly property real raw: Math.max(0, (particles.time - cycle * 9.9 - 9) / 0.9)
                    readonly property real progress: 1 - (1 - raw) * (1 - raw)
                    readonly property real sx: (Math.abs(Math.sin(cycle * 12.9898 + particles.seed) * 43758.5453) % 1) * field.width * 0.7
                    readonly property real sy: (Math.abs(Math.sin(cycle * 78.233 + particles.seed) * 43758.5453) % 1) * field.height * 0.3
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
                }
            }
        }
    }
}
