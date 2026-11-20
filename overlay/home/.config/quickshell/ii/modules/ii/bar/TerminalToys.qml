import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.modules.common
import qs.modules.common.widgets
import qs.services

MouseArea {
    id: root
    implicitWidth: 28
    implicitHeight: Appearance.sizes.barHeight
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton
    property bool menuOpen: false
    property int selected: 0
    property string demoState: "running"
    property bool paused: false
    property bool lightBackdrop: false
    property var preferences: ({scene: "cat", startup: true, ambient: true, commands: true, sounds: true, size: 6})
    function savePreferences(changes) {
        root.preferences = Object.assign({}, root.preferences, changes);
        preferencesFile.setText(JSON.stringify(root.preferences) + "\n");
    }
    FileView {
        id: preferencesFile
        path: Directories.state + "/user/terminal-toys.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            root.preferences = Object.assign({size: 6, sounds: true}, JSON.parse(text()));
            root.selected = Math.max(0, root.scenes.findIndex(s => s.key === root.preferences.scene));
        }
    }
    readonly property string script: Quickshell.shellPath("scripts/terminal-toys.py")
    property var scenes: [
        {key: "cat", name: "Cat", icon: "pets"},
        {key: "garden", name: "Sprout", icon: "local_florist"},
        {key: "robot", name: "Robot", icon: "smart_toy"},
        {key: "baker", name: "Toast", icon: "bakery_dining"}
    ]
    Process {
        id: sceneList
        command: ["python3", root.script, "--list"]
        running: true
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const list = JSON.parse(text);
                    if (list.length) {
                        root.scenes = list;
                        root.selected = Math.max(0, list.findIndex(s => s.key === root.preferences.scene));
                    }
                } catch (e) {}
            }
        }
    }
    onClicked: menuOpen = !menuOpen
    Rectangle {
        anchors.centerIn: parent
        width: 28
        height: 28
        radius: 14
        color: root.menuOpen || root.containsMouse ? Appearance.colors.colLayer1Hover : "transparent"
    }
    MaterialSymbol {
        anchors.centerIn: parent
        text: "animation"
        iconSize: Appearance.font.pixelSize.normal
        color: Appearance.colors.colOnLayer1
        fill: root.menuOpen ? 1 : 0
    }
    LazyLoader {
        active: root.menuOpen
        component: PanelWindow {
            id: popup
            screen: root.QsWindow.window.screen
            color: "transparent"
            implicitWidth: 460
            implicitHeight: 660
            anchors.top: !Config.options.bar.bottom || Config.options.bar.vertical
            anchors.bottom: Config.options.bar.bottom && !Config.options.bar.vertical
            anchors.left: true
            margins.top: Config.options.bar.vertical ? 12 : Appearance.sizes.barHeight + 6
            margins.bottom: Appearance.sizes.barHeight + 6
            margins.left: Config.options.bar.vertical ? Appearance.sizes.verticalBarWidth + 6 : Math.max(8, Math.min(screen.width - width - 8, root.QsWindow.window.mapFromItem(root, 0, 0).x - width / 2))
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "quickshell:terminal-toys"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
            property string preview: ""
            property string failure: ""

            HyprlandFocusGrab {
                active: true
                windows: [popup, root.QsWindow.window]
                onCleared: root.menuOpen = false
            }

            function update(restart) {
                renderer.write(JSON.stringify({scene: root.scenes[root.selected].key, state: root.demoState, paused: root.paused, restart: restart}) + "\n");
            }
            Process {
                id: renderer
                command: ["python3", root.script, root.scenes[root.selected].key, "--stream", "--state", root.demoState, "--scale", "8"]
                running: true
                stdinEnabled: true
                onStarted: popup.update(true)
                stdout: SplitParser {
                    onRead: data => popup.preview = JSON.parse(data).image
                }
                stderr: StdioCollector {
                    onStreamFinished: if (text.length) popup.failure = text
                }
                onExited: (code, status) => { if (code !== 0) popup.failure = "Preview stopped (" + code + "). Close and reopen to retry."; }
            }
            Rectangle {
                anchors.fill: parent
                radius: Appearance.rounding.normal
                color: Appearance.m3colors.m3surfaceContainer
                border.width: 1
                border.color: Appearance.colors.colLayer0Border
                focus: true
                Keys.onEscapePressed: root.menuOpen = false

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        StyledText {
                            text: "Terminal buddy"
                            font.pixelSize: 18
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        RippleButtonWithIcon {
                            materialIcon: "close"
                            mainText: "Close"
                            onClicked: root.menuOpen = false
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 220
                        color: root.lightBackdrop ? "#f6f3ec" : "#1e1e24"
                        radius: 14
                        clip: true
                        Image {
                            anchors.centerIn: parent
                            visible: !popup.failure && popup.preview.length > 0
                            source: popup.preview
                            width: 192
                            height: 192
                            smooth: false
                            mipmap: false
                            fillMode: Image.PreserveAspectFit
                        }
                        StyledText {
                            anchors.fill: parent
                            anchors.margins: 12
                            visible: popup.failure.length > 0
                            text: popup.failure
                            wrapMode: Text.Wrap
                            font.pixelSize: 11
                            color: "#ff92bd"
                        }
                        RippleButton {
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 8
                            implicitWidth: 30
                            implicitHeight: 30
                            buttonRadius: 15
                            colBackground: "transparent"
                            onClicked: root.lightBackdrop = !root.lightBackdrop
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                text: root.lightBackdrop ? "dark_mode" : "light_mode"
                                iconSize: 18
                                color: root.lightBackdrop ? "#4a4058" : "#cfc8dc"
                            }
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 5
                        rowSpacing: 6
                        columnSpacing: 6
                        Repeater {
                            model: root.scenes
                            delegate: RippleButton {
                                id: choice
                                required property var modelData
                                required property int index
                                Layout.fillWidth: true
                                implicitHeight: 54
                                buttonRadius: Appearance.rounding.small
                                toggled: root.selected === index
                                colBackground: Appearance.colors.colLayer2
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                onClicked: {
                                    root.selected = index;
                                    root.savePreferences({scene: modelData.key});
                                    popup.update(true);
                                }
                                contentItem: Column {
                                    spacing: 3
                                    MaterialSymbol {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: choice.modelData.icon
                                        iconSize: 20
                                        fill: choice.toggled ? 1 : 0
                                        color: choice.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                    StyledText {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: choice.modelData.name
                                        font.pixelSize: 11
                                        color: choice.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: [{key: "idle", name: "Idle", icon: "bedtime"}, {key: "running", name: "Busy", icon: "bolt"}, {key: "waiting", name: "Ask", icon: "priority_high"}, {key: "success", name: "Done", icon: "favorite"}, {key: "error", name: "Oops", icon: "error"}]
                            delegate: RippleButton {
                                id: stateButton
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: 32
                                buttonRadius: 16
                                toggled: root.demoState === modelData.key
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                onClicked: { root.demoState = modelData.key; popup.update(false); }
                                contentItem: Row {
                                    spacing: 4
                                    anchors.centerIn: parent
                                    MaterialSymbol {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: stateButton.modelData.icon
                                        iconSize: 16
                                        fill: stateButton.toggled ? 1 : 0
                                        color: stateButton.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                    StyledText {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: stateButton.modelData.name
                                        font.pixelSize: 12
                                        color: stateButton.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                }
                            }
                        }
                        RippleButton {
                            implicitWidth: 32
                            implicitHeight: 32
                            buttonRadius: 16
                            onClicked: { root.paused = !root.paused; popup.update(false); }
                            contentItem: MaterialSymbol {
                                anchors.centerIn: parent
                                text: root.paused ? "play_arrow" : "pause"
                                iconSize: 18
                                color: Appearance.colors.colOnLayer1
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        StyledText {
                            text: "Size in terminal"
                            font.pixelSize: 12
                            color: Appearance.colors.colSubtext
                            Layout.fillWidth: true
                        }
                        Repeater {
                            model: [{size: 4, name: "S"}, {size: 6, name: "M"}, {size: 8, name: "L"}]
                            delegate: RippleButton {
                                id: sizeButton
                                required property var modelData
                                implicitWidth: 40
                                implicitHeight: 28
                                buttonRadius: 14
                                toggled: root.preferences.size === modelData.size
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                onClicked: root.savePreferences({size: modelData.size})
                                contentItem: StyledText {
                                    text: sizeButton.modelData.name
                                    horizontalAlignment: Text.AlignHCenter
                                    font.pixelSize: 12
                                    color: sizeButton.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                }
                            }
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 4
                        Repeater {
                            model: [{key: "startup", name: "Say hello"}, {key: "ambient", name: "Always there"}, {key: "commands", name: "Commands and agents"}, {key: "sounds", name: "Theme sounds"}]
                            delegate: RippleButtonWithIcon {
                                required property var modelData
                                Layout.fillWidth: true
                                materialIcon: root.preferences[modelData.key] ? "check_box" : "check_box_outline_blank"
                                mainText: modelData.name
                                onClicked: {
                                    const change = {};
                                    change[modelData.key] = !root.preferences[modelData.key];
                                    root.savePreferences(change);
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        StyledText {
                            text: "Lives in the top-right corner of Kitty."
                            font.pixelSize: 11
                            color: Appearance.colors.colSubtext
                            Layout.fillWidth: true
                        }
                        RippleButtonWithIcon {
                            materialIcon: "terminal"
                            mainText: "Open in terminal"
                            onClicked: Quickshell.execDetached(["kitty", "--class", "terminal-playground", "--title", "Terminal buddy", "-o", "initial_window_width=72c", "-o", "initial_window_height=26c", "python3", root.script, root.scenes[root.selected].key, "--state", root.demoState])
                        }
                    }
                }
            }
        }
    }
}
