import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

MouseArea {
    id: root
    implicitWidth: barIcon.implicitWidth + 8
    implicitHeight: Appearance.sizes.barHeight
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton

    property bool menuOpen: false
    property bool menuHovered: false
    property string pending: ""
    property bool slow: false

    readonly property string script: Quickshell.shellPath("scripts/colors/apply-theme.py")
    property var themes: []
    property var applied: ({})

    readonly property string current: {
        const bg = Appearance.m3colors.m3background.toString().toLowerCase();
        if (root.applied.theme && root.applied.background === bg)
            return root.applied.theme;
        const accent = Config.options.appearance.palette.accentColor || "";
        if (accent === "")
            return "default";
        return "";
    }

    property var prefs: ({})
    readonly property bool particlesOn: root.prefs.particles !== false
    readonly property bool hasDecor: !!root.applied.decor && root.applied.theme === root.current

    readonly property string modePref: ["light", "dark", "auto"].includes(root.prefs.mode) ? root.prefs.mode : ""
    readonly property string currentMode: Appearance.m3colors.darkmode ? "dark" : "light"
    readonly property string autoMode: Hyprsunset.shouldBeOn ? "dark" : "light"
    readonly property string wantedMode: root.modePref === "auto" ? root.autoMode : (root.modePref || root.currentMode)
    property string autoTried: ""
    property string pendingMode: ""

    function savePrefs(changes) {
        const next = Object.assign({}, root.prefs, changes);
        prefsFile.setText(JSON.stringify(next) + "\n");
        root.prefs = next;
    }

    function setParticles(on) {
        root.savePrefs({ particles: on });
    }

    function setMode(mode) {
        if (root.pending !== "")
            return;
        root.savePrefs({ mode: mode });
        root.pendingMode = mode;
        root.autoTried = "";
        const target = mode === "auto" ? root.autoMode : mode;
        if (target !== root.currentMode)
            root.run("mode", [root.script, root.current || "default", "--mode", target]);
    }

    function run(tag, command) {
        root.pending = tag;
        root.slow = false;
        slowTimer.restart();
        giveUpTimer.restart();
        applyProc.command = command;
        applyProc.running = true;
    }

    function syncAuto() {
        if (root.modePref !== "auto" || root.pending !== "" || root.autoMode === root.currentMode || root.autoTried === root.autoMode)
            return;
        root.autoTried = root.autoMode;
        root.pendingMode = "auto";
        root.run("mode", [root.script, root.current || "default", "--mode", root.autoMode]);
    }

    onAutoModeChanged: autoTimer.restart()
    onModePrefChanged: autoTimer.restart()

    Timer {
        id: autoTimer
        interval: 3000
        running: true
        onTriggered: root.syncAuto()
    }

    FileView {
        id: prefsFile
        path: `${Directories.state}/user/generated/theme-prefs.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.prefs = JSON.parse(text());
            } catch (e) {
                root.prefs = {};
            }
        }
    }

    readonly property int wallpaperCount: root.applied.theme && root.applied.theme === root.current ? (root.applied.wallpapers ?? 0) : 0

    function stepWallpaper(direction) {
        if (root.pending !== "" || root.wallpaperCount < 2)
            return;
        root.run("wallpaper", [root.script, root.current, direction > 0 ? "--next-wallpaper" : "--prev-wallpaper", "--mode", root.wantedMode]);
    }

    function apply(t) {
        if (root.pending !== "" || t.key === root.current)
            return;
        root.run(t.key, [root.script, t.key, "--mode", root.wantedMode]);
    }

    Process {
        id: listProc
        running: true
        command: [root.script, "--list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.themes = JSON.parse(text);
                } catch (e) {}
            }
        }
    }

    Process {
        id: applyProc
        onExited: (exitCode, exitStatus) => {
            stateFile.reload();
            root.done();
        }
    }

    FileView {
        id: stateFile
        path: `${Directories.state}/user/generated/theme.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.applied = JSON.parse(text());
            } catch (e) {
                root.applied = {};
            }
        }
        onLoadFailed: root.applied = {}
    }

    onMenuOpenChanged: if (menuOpen) listProc.running = true

    function done() {
        root.pending = "";
        root.slow = false;
        slowTimer.stop();
        giveUpTimer.stop();
    }

    onPressed: root.menuOpen = !root.menuOpen

    Timer {
        id: slowTimer
        interval: 1000
        onTriggered: root.slow = true
    }

    Timer {
        id: giveUpTimer
        interval: 20000
        onTriggered: root.done()
    }

    Timer {
        interval: 500
        running: root.menuOpen && !root.containsMouse && !root.menuHovered && root.pending === ""
        onTriggered: root.menuOpen = false
    }

    Rectangle {
        anchors.centerIn: parent
        width: barIcon.implicitWidth + 8
        height: barIcon.implicitHeight + 6
        radius: Appearance.rounding.full
        color: root.menuOpen || root.pressed ? Appearance.colors.colLayer1Active : (root.containsMouse ? Appearance.colors.colLayer1Hover : "transparent")
    }

    MaterialSymbol {
        id: barIcon
        anchors.centerIn: parent
        fill: root.menuOpen ? 1 : 0
        text: "palette"
        iconSize: Appearance.font.pixelSize.normal
        color: Appearance.colors.colOnLayer1
    }

    LazyLoader {
        active: root.menuOpen

        component: PanelWindow {
            id: menuWindow
            color: "transparent"

            anchors.left: !Config.options.bar.vertical || (Config.options.bar.vertical && !Config.options.bar.bottom)
            anchors.right: Config.options.bar.vertical && Config.options.bar.bottom
            anchors.top: Config.options.bar.vertical || (!Config.options.bar.vertical && !Config.options.bar.bottom)
            anchors.bottom: !Config.options.bar.vertical && Config.options.bar.bottom

            implicitWidth: menuBackground.implicitWidth + Appearance.sizes.elevationMargin * 2
            implicitHeight: menuBackground.implicitHeight + Appearance.sizes.elevationMargin * 2

            mask: Region {
                item: menuBackground
            }

            exclusionMode: ExclusionMode.Ignore
            exclusiveZone: 0
            margins {
                left: {
                    if (!Config.options.bar.vertical)
                        return root.QsWindow?.mapFromItem(root, (root.width - menuBackground.implicitWidth) / 2, 0).x;
                    return Appearance.sizes.verticalBarWidth;
                }
                top: {
                    if (!Config.options.bar.vertical)
                        return Appearance.sizes.barHeight;
                    return root.QsWindow?.mapFromItem(root, 0, (root.height - menuBackground.implicitHeight) / 2).y;
                }
                right: Appearance.sizes.verticalBarWidth
                bottom: Appearance.sizes.barHeight
            }
            WlrLayershell.namespace: "quickshell:popup"
            WlrLayershell.layer: WlrLayer.Overlay

            StyledRectangularShadow {
                target: menuBackground
            }

            Rectangle {
                id: menuBackground
                anchors.fill: parent
                anchors.margins: Appearance.sizes.elevationMargin
                implicitWidth: menuColumn.implicitWidth + 12
                implicitHeight: menuColumn.implicitHeight + 12
                color: Appearance.m3colors.m3surfaceContainer
                radius: Appearance.rounding.small
                border.width: 1
                border.color: Appearance.colors.colLayer0Border

                HoverHandler {
                    onHoveredChanged: root.menuHovered = hovered
                }

                ColumnLayout {
                    id: menuColumn
                    anchors.centerIn: parent
                    spacing: 2

                    StyledText {
                        Layout.leftMargin: 8
                        Layout.topMargin: 2
                        Layout.bottomMargin: 2
                        text: root.slow ? "Applying, still working..." : "Theme"
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colSubtext
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 4
                        Layout.rightMargin: 4
                        Layout.bottomMargin: 4
                        spacing: 4

                        Repeater {
                            model: [
                                { key: "light", icon: "light_mode", name: "Light" },
                                { key: "dark", icon: "dark_mode", name: "Dark" },
                                { key: "auto", icon: "brightness_auto", name: "Auto" }
                            ]

                            delegate: RippleButton {
                                id: modeButton
                                required property var modelData
                                readonly property bool active: root.modePref === "auto" ? modelData.key === "auto" : (modelData.key === root.currentMode)
                                readonly property bool busy: root.pending === "mode" && root.pendingMode === modelData.key
                                Layout.fillWidth: true
                                implicitHeight: 30
                                buttonRadius: Appearance.rounding.full
                                toggled: active
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                colBackgroundToggledHover: Appearance.colors.colSecondaryContainerHover
                                colRippleToggled: Appearance.colors.colSecondaryContainerActive
                                enabled: root.pending === ""
                                onClicked: root.setMode(modelData.key)

                                contentItem: RowLayout {
                                    spacing: 4
                                    Item { Layout.fillWidth: true }
                                    MaterialSymbol {
                                        visible: !modeButton.busy
                                        text: modeButton.modelData.icon
                                        iconSize: Appearance.font.pixelSize.normal
                                        fill: modeButton.active ? 1 : 0
                                        color: modeButton.active ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                    MaterialLoadingIndicator {
                                        visible: modeButton.busy
                                        loading: modeButton.busy
                                        implicitSize: 16
                                    }
                                    StyledText {
                                        text: modeButton.modelData.name
                                        font.pixelSize: Appearance.font.pixelSize.small
                                        color: modeButton.active ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }
                    }

                    Repeater {
                        model: root.themes

                        delegate: RippleButton {
                            id: row
                            required property var modelData
                            readonly property bool active: root.current === modelData.key
                            readonly property bool busy: root.pending === modelData.key
                            Layout.fillWidth: true
                            implicitWidth: rowContent.implicitWidth + 20
                            implicitHeight: 34
                            buttonRadius: Appearance.rounding.small
                            toggled: active
                            colBackgroundToggled: Appearance.colors.colSecondaryContainer
                            colBackgroundToggledHover: Appearance.colors.colSecondaryContainerHover
                            colRippleToggled: Appearance.colors.colSecondaryContainerActive
                            enabled: root.pending === "" || busy
                            onClicked: root.apply(modelData)

                            contentItem: RowLayout {
                                id: rowContent
                                spacing: 10

                                Row {
                                    spacing: -4
                                    Repeater {
                                        model: row.modelData.swatch
                                        delegate: Rectangle {
                                            required property string modelData
                                            width: 14
                                            height: 14
                                            radius: 7
                                            color: modelData
                                            border.width: 1
                                            border.color: Appearance.colors.colOutlineVariant
                                        }
                                    }
                                }

                                MaterialSymbol {
                                    text: row.modelData.icon
                                    iconSize: Appearance.font.pixelSize.larger
                                    fill: row.active ? 1 : 0
                                    color: row.active ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                }

                                StyledText {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 70
                                    text: row.modelData.name
                                    font.pixelSize: Appearance.font.pixelSize.small
                                    color: row.active ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                }

                                MaterialLoadingIndicator {
                                    visible: row.busy
                                    loading: row.busy
                                    implicitSize: 18
                                }

                                MaterialSymbol {
                                    visible: row.active && !row.busy
                                    text: "check"
                                    iconSize: Appearance.font.pixelSize.normal
                                    color: Appearance.colors.colOnSecondaryContainer
                                }
                            }
                        }
                    }

                    Rectangle {
                        visible: root.wallpaperCount > 1 || root.hasDecor
                        Layout.fillWidth: true
                        Layout.topMargin: 4
                        Layout.bottomMargin: 2
                        implicitHeight: 1
                        color: Appearance.colors.colOutlineVariant
                    }

                    RowLayout {
                        visible: root.wallpaperCount > 1
                        Layout.fillWidth: true
                        Layout.leftMargin: 10
                        Layout.rightMargin: 2
                        spacing: 4

                        MaterialSymbol {
                            text: "wallpaper"
                            iconSize: Appearance.font.pixelSize.larger
                            color: Appearance.colors.colOnLayer1
                        }
                        StyledText {
                            Layout.fillWidth: true
                            Layout.leftMargin: 6
                            text: "Wallpaper"
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer1
                        }
                        RippleButton {
                            implicitWidth: 30
                            implicitHeight: 30
                            buttonRadius: Appearance.rounding.full
                            enabled: root.pending === ""
                            onClicked: root.stepWallpaper(-1)
                            contentItem: MaterialSymbol {
                                horizontalAlignment: Text.AlignHCenter
                                text: "chevron_left"
                                iconSize: Appearance.font.pixelSize.larger
                                color: Appearance.colors.colOnLayer1
                            }
                        }
                        Item {
                            implicitWidth: 30
                            implicitHeight: 30
                            StyledText {
                                anchors.centerIn: parent
                                visible: root.pending !== "wallpaper"
                                text: `${(root.applied.wallpaper_index ?? 0) + 1}/${root.wallpaperCount}`
                                font.pixelSize: Appearance.font.pixelSize.small
                                color: Appearance.colors.colOnLayer1
                            }
                            MaterialLoadingIndicator {
                                anchors.centerIn: parent
                                visible: root.pending === "wallpaper"
                                loading: visible
                                implicitSize: 18
                            }
                        }
                        RippleButton {
                            implicitWidth: 30
                            implicitHeight: 30
                            buttonRadius: Appearance.rounding.full
                            enabled: root.pending === ""
                            onClicked: root.stepWallpaper(1)
                            contentItem: MaterialSymbol {
                                horizontalAlignment: Text.AlignHCenter
                                text: "chevron_right"
                                iconSize: Appearance.font.pixelSize.larger
                                color: Appearance.colors.colOnLayer1
                            }
                        }
                    }

                    RowLayout {
                        visible: root.hasDecor
                        Layout.fillWidth: true
                        Layout.leftMargin: 10
                        Layout.rightMargin: 6
                        spacing: 4

                        MaterialSymbol {
                            text: "auto_awesome"
                            iconSize: Appearance.font.pixelSize.larger
                            color: Appearance.colors.colOnLayer1
                        }
                        StyledText {
                            Layout.fillWidth: true
                            Layout.leftMargin: 6
                            text: "Particles"
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colOnLayer1
                        }
                        StyledSwitch {
                            checked: root.particlesOn
                            onToggled: root.setParticles(checked)
                        }
                    }
                }
            }
        }
    }
}
