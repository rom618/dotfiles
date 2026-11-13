pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common

Singleton {
    id: root

    readonly property string iconPath: Quickshell.shellPath("assets/icons/claude-symbolic.svg")
    readonly property var icons: ({
        "claude": Quickshell.shellPath("assets/icons/claude-symbolic.svg"),
        "pi": Quickshell.shellPath("assets/icons/pi-symbolic.svg"),
        "codex": Quickshell.shellPath("assets/icons/openai-symbolic.svg")
    })
    property var agents: ({})
    readonly property var rank: ({ "done": 0, "running": 1, "waiting": 2 })
    property var states: ({})
    property bool installed: false

    Process {
        running: true
        command: ["bash", "-lc", "command -v claude || test -x \"$HOME/.local/bin/claude\""]
        onExited: (exitCode, exitStatus) => root.installed = exitCode === 0
    }

    function agentFor(window) {
        return window ? (root.agents[window.address] ?? "claude") : "";
    }

    function iconFor(window) {
        return root.icons[window ? (root.agents[window.address] ?? "claude") : "claude"] ?? root.iconPath;
    }

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
                    const data = JSON.parse(line);
                    root.states = data.states ?? {};
                    root.agents = data.agents ?? {};
                } catch (e) {}
            }
        }
        onExited: {
            root.states = {};
            root.agents = {};
            restartTimer.start();
        }
    }

    Timer {
        id: restartTimer
        interval: 5000
        onTriggered: proc.running = true
    }
}
