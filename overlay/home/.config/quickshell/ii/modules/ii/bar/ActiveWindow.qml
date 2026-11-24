import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

Item {
    id: root
    readonly property HyprlandMonitor monitor: Hyprland.monitors.values.find(m => m.name === root.QsWindow.window?.screen?.name) ?? null
    readonly property Toplevel activeWindow: ToplevelManager.activeToplevel

    property string activeWindowAddress: `0x${activeWindow?.HyprlandToplevel?.address}`
    property bool focusingThisMonitor: HyprlandData.activeWorkspace?.monitor == monitor?.name
    property var biggestWindow: HyprlandData.biggestWindowForWorkspace(HyprlandData.monitors[root.monitor?.id]?.activeWorkspace.id)
    readonly property bool showingActive: !!(root.focusingThisMonitor && root.activeWindow?.activated && root.biggestWindow)
    readonly property var shownWindow: root.showingActive ? HyprlandData.windowList.find(w => w.address === root.activeWindowAddress) : root.biggestWindow
    readonly property string agentLabel: ClaudeWindows.sessionLabel(root.shownWindow)

    implicitWidth: colLayout.implicitWidth

    MouseArea {
        anchors.fill: parent
        onPressed: {
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
    }

    ColumnLayout {
        id: colLayout

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: -4

        StyledText {
            Layout.fillWidth: true
            font.pixelSize: Appearance.font.pixelSize.smaller
            color: Appearance.colors.colSubtext
            elide: Text.ElideRight
            text: root.agentLabel || (root.showingActive ? root.activeWindow?.appId :
                (root.biggestWindow?.class) ?? Translation.tr("Desktop"))

        }

        StyledText {
            Layout.fillWidth: true
            font.pixelSize: Appearance.font.pixelSize.small
            color: Appearance.colors.colOnLayer0
            elide: Text.ElideRight
            readonly property string rawTitle: root.showingActive ? root.activeWindow?.title :
                (root.biggestWindow?.title) ?? `${Translation.tr("Workspace")} ${monitor?.activeWorkspace?.id ?? 1}`
            text: root.agentLabel ? rawTitle.replace(/^[^0-9A-Za-zÀ-ÿ~\/.]+/, "") : rawTitle
        }

    }

}
