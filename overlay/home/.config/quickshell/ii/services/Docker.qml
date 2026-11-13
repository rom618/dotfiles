pragma Singleton

import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property bool available: false
    property var containers: []
    readonly property int count: containers.length

    function refresh() {
        if (!root.available) return;
        listProc.running = true;
    }

    Timer {
        interval: Config.options.docker.checkInterval * 1000
        repeat: true
        running: Config.ready && Config.options.docker.enableCheck && root.available
        onTriggered: root.refresh()
    }

    Process {
        id: checkAvailabilityProc
        running: Config.ready && Config.options.docker.enableCheck
        command: ["bash", "-c", "command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1"]
        onExited: (exitCode, exitStatus) => {
            root.available = (exitCode === 0);
            if (root.available) root.refresh();
        }
    }

    Process {
        id: listProc
        command: ["bash", "-c", "docker ps --format '{{json .}}'"]
        stdout: StdioCollector {
            onStreamFinished: {
                const lines = text.trim().length > 0 ? text.trim().split("\n") : [];
                root.containers = lines.map(line => {
                    try { return JSON.parse(line); } catch (e) { return null; }
                }).filter(c => c !== null);
            }
        }
    }
}
