pragma Singleton

import qs
import QtQuick
import QtMultimedia
import qs.modules.common
import qs.services
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

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

    function fileFor(event, variant) {
        const e = root.effects[event];
        if (Array.isArray(e)) {
            const n = Math.max(0, Number(variant) || 0);
            return e[n % e.length] || e.find(x => x) || "";
        }
        return e || "";
    }

    function play(event, variant) {
        if (!root.enabled || !root.effects[event])
            return;
        const now = Date.now();
        const gap = (event === "lock" || event === "unlock") ? 350 : 60;
        if (now - (root.lastPlayed[event] ?? 0) < gap)
            return;
        root.lastPlayed[event] = now;
        const i = root.voiceFiles.indexOf(root.fileFor(event, variant));
        if (i < 0)
            return;
        root.voiceTurn[i] = ((root.voiceTurn[i] ?? 0) + 1) % root.voicesPerFile;
        const v = voices.objectAt(i * root.voicesPerFile + root.voiceTurn[i]);
        if (!v)
            return;
        v.stop();
        v.play();
    }

    readonly property int voicesPerFile: 3
    property var voiceTurn: ({})
    readonly property var voiceFiles: {
        const all = [];
        for (const k of Object.keys(root.effects)) {
            const e = root.effects[k];
            for (const f of (Array.isArray(e) ? e : [e]))
                if (f && !all.includes(f))
                    all.push(f);
        }
        return all;
    }

    Instantiator {
        id: voices
        model: root.voiceFiles.length * root.voicesPerFile
        delegate: SoundEffect {
            required property int index
            source: "file://" + root.voiceFiles[Math.floor(index / root.voicesPerFile)]
            volume: root.volume
        }
    }

    readonly property bool launcherShown: GlobalStates.overviewOpen || GlobalStates.searchOpen
    onLauncherShownChanged: play(launcherShown ? "launcherOpen" : "launcherClose")

    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (GlobalStates.screenLocked)
                return;
            if (event.name === "openwindow") {
                const cls = (event.data.split(",")[2] ?? "").trim();
                if (cls === "")
                    return;
                if (Date.now() - (root.lastPlayed.launcherClose ?? 0) < 800)
                    launcherClose.stop();
                root.play("windowOpen");
            } else if (event.name === "closewindow") {
                root.play("windowClose");
            } else if (event.name === "workspacev2") {
                if (Date.now() - (root.lastPlayed.windowOpen ?? 0) < 600)
                    return;
                root.play("workspace", parseInt(event.data) - 1);
            }
        }
    }

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
        function onRegionSelectorOpenChanged() {
            if (GlobalStates.regionSelectorOpen)
                root.play("screenshot");
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
