pragma Singleton

import qs
import QtQuick
import QtMultimedia
import qs.modules.common
import qs.services
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string script: Quickshell.shellPath("scripts/colors/ambiance.py")
    property var effects: ({})
    property string effectsTheme: ""
    property var lastPlayed: ({})

    readonly property bool enabled: Ambiance.prefs.themeSounds !== false
    readonly property real volume: Math.max(0, Math.min(1, Ambiance.prefs.themeSoundsVolume ?? 0.6))
    readonly property bool available: Object.keys(root.effects).length > 0
    readonly property string theme: Ambiance.theme

    function setEnabled(on) {
        Ambiance.savePrefs({ themeSounds: on });
    }

    function setVolume(v) {
        Ambiance.savePrefs({ themeSoundsVolume: Math.round(v * 100) / 100 });
    }

    function play(event) {
        if (!root.enabled || !root.effects[event])
            return;
        const now = Date.now();
        if (now - (root.lastPlayed[event] ?? 0) < 350)
            return;
        root.lastPlayed[event] = now;
        const p = players[event];
        if (!p)
            return;
        p.stop();
        p.play();
    }

    readonly property var players: ({
        popupOpen: popupOpen,
        popupClose: popupClose,
        notification: notification,
        lock: lock,
        unlock: unlock
    })

    component Fx: MediaPlayer {
        id: fx
        property string file: ""
        property real level: 0.6
        source: fx.file !== "" ? "file://" + fx.file : ""
        audioOutput: AudioOutput {
            volume: fx.level
        }
    }

    Fx { id: popupOpen; file: root.effects.popupOpen ?? ""; level: root.volume }
    Fx { id: popupClose; file: root.effects.popupClose ?? ""; level: root.volume }
    Fx { id: notification; file: root.effects.notification ?? ""; level: root.volume }
    Fx { id: lock; file: root.effects.lock ?? ""; level: root.volume }
    Fx { id: unlock; file: root.effects.unlock ?? ""; level: root.volume }

    onThemeChanged: load()
    Component.onCompleted: load()

    function load() {
        if (root.theme === root.effectsTheme && !loadProc.running)
            return;
        if (root.theme === "") {
            root.effects = {};
            root.effectsTheme = "";
            return;
        }
        loadProc.theme = root.theme;
        loadProc.command = [root.script, "--effects", root.theme];
        loadProc.running = true;
    }

    Process {
        id: loadProc
        property string theme: ""
        stdout: StdioCollector {
            onStreamFinished: {
                let map = {};
                try {
                    map = JSON.parse(text);
                } catch (e) {}
                if (loadProc.theme !== root.theme) {
                    root.load();
                    return;
                }
                root.effects = map;
                root.effectsTheme = loadProc.theme;
            }
        }
    }

    Connections {
        target: GlobalStates
        function onScreenLockedChanged() {
            root.play(GlobalStates.screenLocked ? "lock" : "unlock");
        }
        function onSidebarRightOpenChanged() {
            root.play(GlobalStates.sidebarRightOpen ? "popupOpen" : "popupClose");
        }
        function onSidebarLeftOpenChanged() {
            root.play(GlobalStates.sidebarLeftOpen ? "popupOpen" : "popupClose");
        }
    }

    Connections {
        target: Notifications
        function onNotify(notification) {
            if (!Notifications.silent)
                root.play("notification");
        }
    }
}
