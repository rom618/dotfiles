pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common

Singleton {
    id: root

    readonly property string iconPath: Quickshell.shellPath("assets/icons/claude-symbolic.svg")
    readonly property var rank: ({ "done": 0, "running": 1, "waiting": 2 })
    property var states: ({})

    function stateFor(window) {
        return window ? (root.states[window.address] ?? "") : "";
    }

    function workspaceState(workspaceId) {
        let best = "";
        for (const w of HyprlandData.windowList) {
            if (w.workspace?.id !== workspaceId)
                continue;
            const s = root.states[w.address];
            if (s && (best === "" || root.rank[s] > root.rank[best]))
                best = s;
        }
        return best;
    }

    Process {
        id: proc
        running: true
        command: [Quickshell.shellPath("scripts/claude/claude-windows.py")]
        stdout: SplitParser {
            onRead: line => {
                try {
                    root.states = JSON.parse(line);
                } catch (e) {}
            }
        }
        onExited: {
            root.states = {};
            restartTimer.start();
        }
    }

    Timer {
        id: restartTimer
        interval: 5000
        onTriggered: proc.running = true
    }
}
