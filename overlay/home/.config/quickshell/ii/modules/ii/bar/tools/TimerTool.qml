import QtQuick
import QtQuick.Layouts
import qs.modules.ii.sidebarRight.pomodoro

Item {
    id: tool
    required property var host
    implicitHeight: 380

    PomodoroWidget {
        id: widget
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: tool.host.menuOpen = false
        Component.onCompleted: widget.forceActiveFocus()
    }
}
