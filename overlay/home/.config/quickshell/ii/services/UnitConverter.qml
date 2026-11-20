pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string script: Quickshell.shellPath("scripts/tools/convert.py")
    property string query: ""
    property var result: null
    property bool busy: false
    property bool slow: false
    property string rates: ""
    property bool ready: false
    property int lastId: 0
    property string pending: ""
    property real sentAt: 0
    property real lastMs: 0

    function convert(q) {
        root.query = q;
        if (q.trim() === "") {
            root.result = null;
            root.busy = false;
            debounce.stop();
            return;
        }
        root.busy = true;
        root.slow = false;
        slowTimer.restart();
        debounce.restart();
    }

    function sendNow() {
        idle.restart();
        root.lastId += 1;
        const line = root.lastId + "\t" + root.query.replace(/[\t\n]/g, " ") + "\n";
        if (!proc.running || !root.ready) {
            root.pending = line;
            proc.running = true;
            return;
        }
        root.sentAt = Date.now();
        proc.write(line);
    }

    function warm() {
        idle.restart();
        if (!proc.running)
            proc.running = true;
    }

    Timer {
        id: debounce
        interval: 150
        onTriggered: root.sendNow()
    }

    Timer {
        id: slowTimer
        interval: 1000
        onTriggered: root.slow = root.busy
    }

    Timer {
        id: idle
        interval: 600000
        onTriggered: proc.running = false
    }

    Process {
        id: proc
        command: ["python3", root.script, "--serve"]
        stdinEnabled: true
        onRunningChanged: {
            if (!running)
                root.ready = false;
        }
        onExited: (code, status) => {
            if (root.busy && code !== 0) {
                root.busy = false;
                root.result = { ok: false, query: root.query, error: "The converter stopped (" + code + ")", retry: true };
            }
        }
        stdout: SplitParser {
            onRead: data => {
                let r = null;
                try {
                    r = JSON.parse(data);
                } catch (e) {
                    return;
                }
                if (r.type === "ready" || r.type === "rates") {
                    root.rates = r.rates ?? "";
                    if (r.type === "ready") {
                        root.ready = true;
                        if (root.pending !== "") {
                            root.sentAt = Date.now();
                            proc.write(root.pending);
                            root.pending = "";
                        }
                    } else if (root.query.trim() !== "") {
                        root.sendNow();
                    }
                    return;
                }
                if (String(r.id) !== String(root.lastId))
                    return;
                root.lastMs = Date.now() - root.sentAt;
                root.result = r;
                if (!debounce.running)
                    root.busy = false;
            }
        }
    }
}
