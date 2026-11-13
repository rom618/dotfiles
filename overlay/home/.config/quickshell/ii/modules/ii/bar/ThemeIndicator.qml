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
            return Appearance.m3colors.darkmode ? "dark" : "white";
        return "";
    }

    function nextWallpaper(t) {
        if (root.pending !== "")
            return;
        root.pending = t.key;
        root.slow = false;
        slowTimer.restart();
        giveUpTimer.restart();
        applyProc.command = [root.script, t.key, "--next-wallpaper"];
        applyProc.running = true;
    }

    function apply(t) {
        if (root.pending !== "" || t.key === root.current)
            return;
        root.pending = t.key;
        root.slow = false;
        slowTimer.restart();
        giveUpTimer.restart();
        applyProc.command = [root.script, t.key];
        applyProc.running = true;
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

                                RippleButton {
                                    visible: row.active && !row.busy && (row.modelData.wallpapers ?? 0) > 1
                                    implicitHeight: 26
                                    implicitWidth: wallRow.implicitWidth + 12
                                    buttonRadius: Appearance.rounding.full
                                    colBackground: Appearance.colors.colSecondaryContainerHover
                                    onClicked: root.nextWallpaper(row.modelData)
                                    contentItem: RowLayout {
                                        id: wallRow
                                        spacing: 4
                                        MaterialSymbol {
                                            text: "wallpaper"
                                            iconSize: Appearance.font.pixelSize.normal
                                            color: Appearance.colors.colOnSecondaryContainer
                                        }
                                        StyledText {
                                            text: `${(root.applied.wallpaper_index ?? 0) + 1}/${row.modelData.wallpapers}`
                                            font.pixelSize: Appearance.font.pixelSize.smaller
                                            color: Appearance.colors.colOnSecondaryContainer
                                        }
                                    }
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
                }
            }
        }
    }
}
