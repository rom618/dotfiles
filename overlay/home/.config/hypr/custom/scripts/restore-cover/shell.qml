import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root

    property string flag: Quickshell.env("RESTORE_COVER_FLAG") || ""
    property string wallpaper: Quickshell.env("RESTORE_COVER_WALLPAPER") || ""
    property bool closing: false

    function close() {
        if (closing)
            return;
        closing = true;
        quitTimer.start();
    }

    Process {
        id: check
        command: ["test", "-e", root.flag]
        onExited: (code, status) => {
            if (code !== 0)
                root.close();
        }
    }

    Timer {
        interval: 300
        running: root.flag !== "" && !root.closing
        repeat: true
        onTriggered: check.running = true
    }

    Timer {
        interval: 45000
        running: true
        onTriggered: root.close()
    }

    Timer {
        id: quitTimer
        interval: 500
        onTriggered: Qt.quit()
    }

    Variants {
        model: Quickshell.screens

        PanelWindow {
            required property var modelData

            screen: modelData
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.namespace: "restore-cover"
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }

            Rectangle {
                anchors.fill: parent
                color: "#141313"
                opacity: root.closing ? 0 : 1

                Behavior on opacity {
                    NumberAnimation {
                        duration: 450
                        easing.type: Easing.OutCubic
                    }
                }

                Image {
                    anchors.fill: parent
                    source: root.wallpaper !== "" ? "file://" + root.wallpaper : ""
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: false
                    cache: false
                }

                Rectangle {
                    anchors.fill: parent
                    color: "#000000"
                    opacity: 0.45
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 18

                    BusyIndicator {
                        anchors.horizontalCenter: parent.horizontalCenter
                        running: true
                        width: 56
                        height: 56
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Restoring your windows"
                        color: "#f2f0ef"
                        font.pixelSize: 18
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.AllButtons
                }
            }
        }
    }
}
