pragma Singleton

import QtQuick
import qs.modules.common
import qs.services
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string picker: Quickshell.shellPath("scripts/colors/auto-theme.py")
    readonly property string applier: Quickshell.shellPath("scripts/colors/apply-theme.py")

    property var prefs: ({})
    property var applied: ({})
    property var pick: ({})
    property bool applying: false
    property string tried: ""

    readonly property bool enabled: root.prefs.autoTheme === true
    readonly property string reason: {
        if (!root.pick.theme)
            return "";
        const parts = [root.pick.why];
        if (root.pick.temp !== null && root.pick.temp !== undefined)
            parts.push(Math.round(root.pick.temp) + String.fromCharCode(176) + "C");
        return parts.join(", ");
    }

    function setEnabled(on) {
        const next = Object.assign({}, root.prefs, { autoTheme: on });
        prefsFile.setText(JSON.stringify(next) + "\n");
        root.prefs = next;
        root.tried = "";
        if (on)
            root.evaluate();
    }

    function evaluate() {
        if (pickProc.running)
            return;
        pickProc.command = [root.picker, "--sunrise", Hyprsunset.sunrise || "", "--sunset", Hyprsunset.sunset || "",
            "--temp", Weather.data.temp || "", "--code", String(Weather.data.wCode || "")];
        pickProc.running = true;
    }

    function follow() {
        if (!root.enabled || root.applying || !root.pick.theme)
            return;
        if (root.pick.theme === root.applied.theme || root.pick.theme === root.tried)
            return;
        root.tried = root.pick.theme;
        root.applying = true;
        applyProc.command = [root.applier, root.pick.theme];
        applyProc.running = true;
    }

    onEnabledChanged: if (enabled) evaluate()

    Connections {
        target: Weather
        function onDataChanged() {
            if (root.enabled)
                root.evaluate();
        }
    }

    Timer {
        interval: 5 * 60 * 1000
        running: root.enabled
        repeat: true
        triggeredOnStart: true
        onTriggered: root.evaluate()
    }

    Process {
        id: pickProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.pick = JSON.parse(text);
                } catch (e) {
                    return;
                }
                root.follow();
            }
        }
    }

    Process {
        id: applyProc
        onExited: (exitCode, exitStatus) => {
            root.applying = false;
            stateFile.reload();
        }
    }

    FileView {
        id: prefsFile
        path: `${Directories.state}/user/generated/theme-prefs.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.prefs = JSON.parse(text());
            } catch (e) {
                root.prefs = {};
            }
        }
    }

    FileView {
        id: stateFile
        path: `${Directories.state}/user/generated/theme.json`
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.applied = JSON.parse(text());
            } catch (e) {
                root.applied = {};
            }
            if (root.applied.theme === root.pick.theme)
                root.tried = "";
        }
        onLoadFailed: root.applied = {}
    }
}
