pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.modules.common

Singleton {
    id: root

    readonly property string iconPath: Quickshell.shellPath("assets/icons/claude-symbolic.svg")
    readonly property var icons: ({
        "claude": Quickshell.shellPath("assets/icons/claude-symbolic.svg"),
        "pi": Quickshell.shellPath("assets/icons/pi-symbolic.svg"),
        "codex": Quickshell.shellPath("assets/icons/codex-symbolic.svg")
    })
    property var agents: ({})
    readonly property var rank: ({ "idle": -1, "done": 0, "running": 1, "waiting": 2 })
    property var states: ({})
    property var cwds: ({})
    property var subagents: ({})
    property var unread: ({})
    property var doneReplies: ({})
    readonly property string focusedAddress: ToplevelManager.activeToplevel?.HyprlandToplevel?.address ? `0x${ToplevelManager.activeToplevel.HyprlandToplevel.address}` : ""
    readonly property var labels: ({ "claude": "Claude", "pi": "pi", "codex": "Codex" })
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

    function sessionLabel(window) {
        if (!window || !root.states[window.address])
            return "";
        const cwd = root.cwds[window.address] ?? "";
        const home = Quickshell.env("HOME");
        const place = cwd === home ? "~" : cwd.split("/").pop();
        return place ? `${root.labels[root.agentFor(window)]} · ${place}` : root.labels[root.agentFor(window)];
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

    function workspaceUnread(workspaceId) {
        let total = 0;
        for (const w of HyprlandData.windowList) {
            if (w.workspace?.id === workspaceId)
                total += root.unread[w.address] ?? 0;
        }
        return total;
    }

    function countUnread(previous, next, replies) {
        const counts = {};
        const doneReplies = {};
        for (const address in next) {
            let n = root.unread[address] ?? 0;
            const reply = replies[address];
            const newReply = reply === undefined || reply !== root.doneReplies[address];
            if (next[address] === "done" && previous[address] && previous[address] !== "done" && address !== root.focusedAddress && newReply)
                n += 1;
            if (n > 0)
                counts[address] = n;
            doneReplies[address] = next[address] === "done" || !(address in root.doneReplies) ? reply : root.doneReplies[address];
        }
        root.unread = counts;
        root.doneReplies = doneReplies;
    }

    onFocusedAddressChanged: {
        if (!root.unread[root.focusedAddress])
            return;
        const counts = Object.assign({}, root.unread);
        delete counts[root.focusedAddress];
        root.unread = counts;
    }

    function workspaceSubagents(workspaceId) {
        let total = 0;
        for (const w of HyprlandData.windowList) {
            if (w.workspace?.id === workspaceId)
                total += root.subagents[w.address] ?? 0;
        }
        return total;
    }

    Process {
        id: proc
        running: true
        command: [Quickshell.shellPath("scripts/claude/claude-windows.py")]
        stdout: SplitParser {
            onRead: line => {
                try {
                    const data = JSON.parse(line);
                    root.countUnread(root.states, data.states ?? {}, data.replies ?? {});
                    root.states = data.states ?? {};
                    root.agents = data.agents ?? {};
                    root.cwds = data.cwds ?? {};
                    root.subagents = data.subagents ?? {};
                } catch (e) {}
            }
        }
        onExited: {
            root.states = {};
            root.doneReplies = {};
            root.agents = {};
            root.cwds = {};
            root.subagents = {};
            restartTimer.start();
        }
    }

    Timer {
        id: restartTimer
        interval: 5000
        onTriggered: proc.running = true
    }
}
