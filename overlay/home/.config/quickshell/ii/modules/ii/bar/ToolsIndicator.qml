import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
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
    property string tab: "wolfram"
    property var store: ({})
    readonly property var tools: [
        { key: "wolfram", name: "Wolfram Alpha", icon: "calculate", file: "WolframTool.qml" },
        { key: "convert", name: "Convert", icon: "swap_horiz", file: "ConvertTool.qml" },
        { key: "translate", name: "Translate", icon: "translate", file: "TranslateTool.qml" },
        { key: "dictionary", name: "Dictionary", icon: "menu_book", file: "DictionaryTool.qml" },
        { key: "color", name: "Color picker", icon: "colorize", file: "ColorTool.qml" },
        { key: "timer", name: "Timer", icon: "timer", file: "TimerTool.qml" }
    ]

    function setTab(key) {
        root.tab = key;
    }
    property string query: ""
    property var result: null
    property bool busy: false
    property bool slow: false
    property var history: []
    property bool preferDecimal: false
    property string decimalText: ""
    property bool decimalBusy: false
    readonly property bool exactAnswer: !!root.result?.ok && root.result.answer.length < 120 && /(\d\s*\/\s*\d|\bpi\b|sqrt|\^|\be\b|log|\u03c0|\u221a)/.test(root.result.answer)
    readonly property bool showingDecimal: root.preferDecimal && root.exactAnswer && root.decimalText !== ""

    function wantDecimal(on) {
        root.preferDecimal = on;
        if (on && root.exactAnswer && root.decimalText === "" && !root.decimalBusy) {
            root.decimalBusy = true;
            decProc.running = false;
            decProc.command = ["python3", root.script, "--decimal", root.query];
            decProc.running = true;
        }
    }
    readonly property string script: Quickshell.shellPath("scripts/tools/wolfram.py")

    onClicked: menuOpen = !menuOpen
    onMenuOpenChanged: {
        // share:begin bar-themes
        ThemeSounds.play(menuOpen ? "popupOpen" : "popupClose");
        // share:end
        if (menuOpen)
            loadHistory();
    }

    function ask(q) {
        q = (q || "").trim();
        if (q === "")
            return;
        root.query = q;
        root.result = null;
        root.decimalText = "";
        root.decimalBusy = false;
        root.busy = true;
        root.slow = false;
        slowTimer.restart();
        askProc.running = false;
        askProc.command = ["python3", root.script, q];
        askProc.running = true;
    }

    function loadHistory() {
        if (!historyProc.running)
            historyProc.running = true;
    }

    IpcHandler {
        target: "tools"
        function toggle(): void {
            root.menuOpen = !root.menuOpen;
        }
        function close(): void {
            root.menuOpen = false;
        }
        function open(tab: string): void {
            if (root.tools.some(t => t.key === tab))
                root.tab = tab;
            root.menuOpen = true;
        }
    }

    Timer {
        id: slowTimer
        interval: 1000
        onTriggered: root.slow = root.busy
    }

    Process {
        id: askProc
        stdout: StdioCollector {
            onStreamFinished: {
                let r = null;
                try {
                    r = JSON.parse(text);
                } catch (e) {
                    r = { ok: false, query: root.query, error: "Unexpected answer from the script", retry: true };
                }
                if (r.query !== root.query)
                    return;
                root.result = r;
                root.decimalText = r.decimal ?? "";
                root.busy = false;
                root.loadHistory();
                if (root.preferDecimal)
                    root.wantDecimal(true);
            }
        }
        onExited: (code, status) => {
            if (code !== 0 && root.busy) {
                root.busy = false;
                root.result = { ok: false, query: root.query, error: "The tool stopped (" + code + ")", retry: true };
            }
        }
    }

    Process {
        id: decProc
        stdout: StdioCollector {
            onStreamFinished: {
                let r = null;
                try {
                    r = JSON.parse(text);
                } catch (e) {}
                root.decimalBusy = false;
                if (r && r.ok && r.query === root.query)
                    root.decimalText = r.decimal;
            }
        }
    }

    Process {
        id: historyProc
        command: ["python3", root.script, "--history"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.history = JSON.parse(text);
                } catch (e) {}
            }
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 28
        height: 28
        radius: 14
        color: root.menuOpen || root.containsMouse ? Appearance.colors.colLayer1Hover : "transparent"
    }

    MaterialSymbol {
        anchors.centerIn: parent
        text: "handyman"
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
            implicitWidth: 520
            implicitHeight: card.implicitHeight
            anchors.top: !Config.options.bar.bottom || Config.options.bar.vertical
            anchors.bottom: Config.options.bar.bottom && !Config.options.bar.vertical
            anchors.left: true
            margins.top: Config.options.bar.vertical ? 12 : Appearance.sizes.barHeight + 6
            margins.bottom: Appearance.sizes.barHeight + 6
            margins.left: Config.options.bar.vertical ? Appearance.sizes.verticalBarWidth + 6 : Math.max(8, Math.min(screen.width - width - 8, root.QsWindow.window.mapFromItem(root, 0, 0).x - width / 2))
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "quickshell:tools"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

            HyprlandFocusGrab {
                active: true
                windows: [popup]
                onCleared: root.menuOpen = false
            }

            Rectangle {
                id: card
                anchors.left: parent.left
                anchors.right: parent.right
                implicitHeight: content.implicitHeight + 32
                radius: Appearance.rounding.normal
                color: Appearance.m3colors.m3surfaceContainer
                border.width: 1
                border.color: Appearance.colors.colLayer0Border
                Keys.onEscapePressed: root.menuOpen = false

                ColumnLayout {
                    id: content
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Repeater {
                            model: root.tools
                            delegate: RippleButton {
                                id: tab
                                required property var modelData
                                implicitHeight: 32
                                implicitWidth: tab.toggled ? tabRow.implicitWidth + 20 : 36
                                buttonRadius: 16
                                toggled: root.tab === modelData.key
                                colBackgroundToggled: Appearance.colors.colSecondaryContainer
                                onClicked: root.setTab(modelData.key)
                                StyledToolTip {
                                    text: tab.modelData.name
                                }
                                contentItem: RowLayout {
                                    id: tabRow
                                    spacing: 6
                                    MaterialSymbol {
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.leftMargin: tab.toggled ? 0 : 0
                                        text: tab.modelData.icon
                                        iconSize: 18
                                        fill: tab.toggled ? 1 : 0
                                        color: tab.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1
                                    }
                                    StyledText {
                                        visible: tab.toggled
                                        text: tab.modelData.name
                                        font.pixelSize: Appearance.font.pixelSize.small
                                        color: Appearance.colors.colOnSecondaryContainer
                                    }
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        RippleButton {
                            implicitWidth: 30
                            implicitHeight: 30
                            buttonRadius: 15
                            onClicked: root.menuOpen = false
                            contentItem: MaterialSymbol {
                                text: "close"
                                iconSize: 18
                                horizontalAlignment: Text.AlignHCenter
                                color: Appearance.colors.colOnLayer1
                            }
                        }
                    }

                    Loader {
                        id: toolLoader
                        Layout.fillWidth: true
                        readonly property string file: (root.tools.find(t => t.key === root.tab) ?? root.tools[0]).file
                        onFileChanged: setSource("tools/" + file, { host: root })
                        Component.onCompleted: setSource("tools/" + file, { host: root })
                    }
                }
            }
        }
    }
}
