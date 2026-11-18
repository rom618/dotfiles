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

    property var prefs: ({})
    property var applied: ({})
    property var available: ({})
    property var files: []
    property string filesTheme: ""
    property int index: 0
    property bool fetching: false

    readonly property bool enabled: root.prefs.ambiance === true
    readonly property real volume: Math.max(0, Math.min(1, root.prefs.ambianceVolume ?? 0.35))
    readonly property bool pauseForMedia: root.prefs.ambiancePauseForMedia !== false
    readonly property string theme: root.applied.theme ?? ""
    readonly property bool hasSounds: (root.available[root.theme] ?? 0) > 0
    readonly property bool mediaPlaying: MprisController.players.some(p => p.isPlaying)
    readonly property bool shouldPlay: root.enabled && root.hasSounds && !GlobalStates.screenLocked && !(root.pauseForMedia && root.mediaPlaying)
    readonly property bool playing: player.playbackState === MediaPlayer.PlayingState
    readonly property string currentFile: root.files.length > 0 ? root.files[root.index % root.files.length] : ""
    readonly property string trackName: {
        const base = root.currentFile.split("/").pop().replace(/\.[a-z0-9]+$/i, "");
        return /-[0-9a-f]{10}$/.test(base) ? "" : base.replace(/^BGM_/, "").replace(/_/g, " ");
    }

    function skipTrack() {
        root.next();
    }

    function banTrack() {
        const f = root.currentFile;
        if (f === "")
            return;
        skipProc.command = [root.script, "--skip", root.theme, f];
        skipProc.running = true;
        const rest = root.files.filter(x => x !== f);
        root.files = rest;
        root.index = rest.length > 0 ? root.index % rest.length : 0;
        player.source = "";
        if (rest.length > 0)
            root.start();
        else
            player.stop();
    }

    function savePrefs(changes) {
        const next = Object.assign({}, root.prefs, changes);
        prefsFile.setText(JSON.stringify(next) + "\n");
        root.prefs = next;
    }

    function setEnabled(on) {
        root.savePrefs({ ambiance: on });
    }

    function setVolume(v) {
        root.savePrefs({ ambianceVolume: Math.round(v * 100) / 100 });
    }

    function shuffle(list) {
        const a = list.slice();
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function load() {
        if (!root.shouldPlay) {
            fadeOut.start();
            return;
        }
        if (root.filesTheme === root.theme && root.files.length > 0) {
            if (!root.playing)
                root.start();
            return;
        }
        if (fetchProc.running)
            return;
        root.fetching = true;
        fetchProc.theme = root.theme;
        fetchProc.command = [root.script, root.theme];
        fetchProc.running = true;
    }

    function start() {
        if (root.files.length === 0)
            return;
        fadeOut.stop();
        const src = "file://" + root.files[root.index % root.files.length];
        if (player.source.toString() !== src) {
            output.volume = 0;
            player.source = src;
        }
        player.play();
        fadeIn.restart();
    }

    function next() {
        root.index = (root.index + 1) % Math.max(1, root.files.length);
        player.source = "";
        root.start();
    }

    onShouldPlayChanged: settle.restart()
    onThemeChanged: {
        if (root.filesTheme !== root.theme && root.playing) {
            fadeOut.switching = true;
            fadeOut.start();
        } else {
            settle.restart();
        }
    }
    onVolumeChanged: if (!fadeIn.running && !fadeOut.running && root.playing) output.volume = root.volume

    Timer {
        id: settle
        interval: 800
        onTriggered: root.load()
    }

    Timer {
        interval: 30 * 60 * 1000
        repeat: true
        running: root.enabled
        onTriggered: listProc.running = true
    }

    MediaPlayer {
        id: player
        audioOutput: AudioOutput {
            id: output
            volume: 0
        }
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.EndOfMedia)
                root.next();
            else if (mediaStatus === MediaPlayer.InvalidMedia)
                root.next();
        }
    }

    NumberAnimation {
        id: fadeIn
        target: output
        property: "volume"
        to: root.volume
        duration: 2500
        easing.type: Easing.InOutQuad
    }

    NumberAnimation {
        id: fadeOut
        property bool switching: false
        target: output
        property: "volume"
        to: 0
        duration: 1500
        easing.type: Easing.InOutQuad
        onFinished: {
            player.pause();
            if (switching) {
                switching = false;
                player.source = "";
                root.files = [];
                root.filesTheme = "";
                settle.restart();
            }
        }
    }

    Process {
        id: listProc
        running: true
        command: [root.script, "--list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.available = JSON.parse(text);
                } catch (e) {}
                settle.restart();
            }
        }
    }

    Process {
        id: skipProc
    }

    Process {
        id: fetchProc
        property string theme: ""
        stdout: StdioCollector {
            onStreamFinished: {
                root.fetching = false;
                let list = [];
                try {
                    list = JSON.parse(text);
                } catch (e) {}
                if (fetchProc.theme !== root.theme) {
                    settle.restart();
                    return;
                }
                root.files = root.shuffle(list);
                root.filesTheme = fetchProc.theme;
                root.index = 0;
                if (root.shouldPlay)
                    root.start();
            }
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
        }
        onLoadFailed: root.applied = {}
    }
}
