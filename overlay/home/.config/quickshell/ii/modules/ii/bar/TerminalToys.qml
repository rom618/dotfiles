import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
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
    property var preferences: ({scene: "cat", startup: true, ambient: true, commands: true})
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
            root.preferences = JSON.parse(text());
            root.selected = root.scenes.findIndex(s => s.key === root.preferences.scene);
        }
    }
    readonly property string script: Quickshell.shellPath("scripts/terminal-toys.py")
    readonly property var scenes: [
        {key: "cat", name: "Terminal cat", icon: "pets"},
        {key: "garden", name: "Growing garden", icon: "local_florist"},
        {key: "robot", name: "Sleepy robot", icon: "smart_toy"},
        {key: "baker", name: "Little baker", icon: "cake"},
        {key: "wizard", name: "Pocket wizard", icon: "auto_fix_high"},
        {key: "planet", name: "Little planet", icon: "public"}
    ]
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
            implicitWidth: 700
            implicitHeight: 706
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

            function update(restart) {
                renderer.write(JSON.stringify({scene: root.scenes[root.selected].key, state: root.demoState, paused: root.paused, restart: restart}) + "\n");
            }
            Process {
                id: renderer
                command: ["python3", root.script, root.scenes[root.selected].key, "--stream", "--state", root.demoState]
                running: true
                stdinEnabled: true
                onStarted: popup.update(true)
                stdout: SplitParser {
                    onRead: data => popup.preview = JSON.parse(data).html
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
                    anchors.margins: 18
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        StyledText {
                            text: "Terminal playground"
                            font.pixelSize: 20
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        RippleButtonWithIcon {
                            materialIcon: "close"
                            mainText: "Close"
                            onClicked: root.menuOpen = false
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 3
                        rowSpacing: 6
                        columnSpacing: 6
                        Repeater {
                            model: root.scenes
                            delegate: RippleButton {
                                id: choice
                                required property var modelData
                                required property int index
                                Layout.fillWidth: true
                                implicitHeight: 52
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
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#0d1220"
                        radius: 12
                        clip: true
                        Text {
                            anchors.centerIn: parent
                            text: popup.failure || popup.preview
                            textFormat: popup.failure ? Text.PlainText : Text.RichText
                            font.family: "monospace"
                            font.pixelSize: 12
                            color: "#ff92bd"
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        StyledText {
                            text: "Demo state"
                            font.pixelSize: 12
                            color: Appearance.colors.colSubtext
                        }
                        Repeater {
                            model: [{key: "idle", name: "Idle"}, {key: "running", name: "Working"}, {key: "success", name: "Success"}, {key: "error", name: "Error"}]
                            delegate: RippleButton {
                                id: stateButton
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: 30
                                buttonRadius: 15
                                toggled: root.demoState === modelData.key
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                onClicked: { root.demoState = modelData.key; popup.update(false); }
                                contentItem: StyledText {
                                    text: stateButton.modelData.name
                                    horizontalAlignment: Text.AlignHCenter
                                    font.pixelSize: 12
                                    color: stateButton.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Repeater {
                            model: [{key: "startup", name: "On opening"}, {key: "ambient", name: "Always visible"}, {key: "commands", name: "Command activity"}]
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
                    StyledText {
                        text: "Applied to Kitty terminals · selected animation and toggles are saved."
                        font.pixelSize: 11
                        color: Appearance.colors.colSubtext
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        RippleButtonWithIcon {
                            materialIcon: root.paused ? "play_arrow" : "pause"
                            mainText: root.paused ? "Play" : "Pause"
                            onClicked: { root.paused = !root.paused; popup.update(false); }
                        }
                        RippleButtonWithIcon {
                            materialIcon: "replay"
                            mainText: "Replay"
                            onClicked: popup.update(true)
                        }
                        Item { Layout.fillWidth: true }
                        RippleButtonWithIcon {
                            materialIcon: "terminal"
                            mainText: "Open in terminal"
                            onClicked: Quickshell.execDetached(["kitty", "--class", "terminal-playground", "--title", "Terminal playground", "-o", "initial_window_width=90c", "-o", "initial_window_height=30c", "python3", root.script, root.scenes[root.selected].key, "--state", root.demoState])
                        }
                    }
                    StyledText {
                        text: "Preview mode · try the states above; terminal keys 1–6 switch animations."
                        font.pixelSize: 11
                        color: Appearance.colors.colSubtext
                    }
                }
            }
        }
    }
}
