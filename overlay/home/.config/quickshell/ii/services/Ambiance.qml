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
    readonly property string syncScript: Quickshell.shellPath("scripts/colors/ambiance-playlist.py")

    property var prefs: ({})
    property var applied: ({})
    property var available: ({})
    property var musicStatus: ({})
    property var files: []
    property string filesKey: ""
    property int index: 0
    property var names: ({})
    property bool fetching: false
    property bool syncing: false
    property bool afterSync: false

    readonly property bool enabled: root.prefs.ambiance === true
    readonly property real volume: Math.max(0, Math.min(1, root.prefs.ambianceVolume ?? 0.35))
    readonly property bool pauseForMedia: root.prefs.ambiancePauseForMedia !== false
    readonly property string theme: root.applied.theme ?? ""
    readonly property bool musicAvailable: root.musicStatus.configured === true || (root.musicStatus.tracks ?? 0) > 0
    readonly property bool wantsMusic: root.prefs.ambianceSource === "music"
    readonly property string playSource: root.wantsMusic && root.musicAvailable ? "music" : "sounds"
    readonly property string wantKey: root.playSource === "music" ? "@music:" + root.theme : root.theme
    readonly property bool hasSounds: root.playSource === "music" ? (root.musicStatus.tracks ?? 0) > 0 : (root.available[root.theme] ?? 0) > 0
    readonly property bool mediaPlaying: MprisController.players.some(p => p.isPlaying)
    readonly property bool shouldPlay: root.enabled && root.hasSounds && !GlobalStates.screenLocked && !(root.pauseForMedia && root.mediaPlaying)
    readonly property bool playing: player.playbackState === MediaPlayer.PlayingState
    readonly property string currentFile: root.files.length > 0 ? root.files[root.index % root.files.length] : ""
    readonly property string trackName: root.nameOf(root.currentFile)

    function nameOf(f) {
        if (!f)
            return "";
        if (root.names[f])
            return root.names[f];
        const base = f.split("/").pop().replace(/\.[a-z0-9]+$/i, "");
        return /-[0-9a-f]{10}$/.test(base) ? "" : base.replace(/^BGM_/, "").replace(/_/g, " ");
    }

    function previousTrack() {
        const n = Math.max(1, root.files.length);
        root.index = (root.index - 1 + n) % n;
        player.source = "";
        root.start();
    }

    function playFile(f) {
        const i = root.files.indexOf(f);
        if (i < 0)
            return;
        root.index = i;
        player.source = "";
        root.start();
    }

    function skipTrack() {
        root.next();
    }

    function banTrack() {
        const f = root.currentFile;
        if (f === "")
            return;
        skipProc.command = [root.script, "--skip", root.playSource === "music" ? "@music" : root.theme, f];
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

    function setSource(s) {
        root.savePrefs({ ambianceSource: s === "music" ? "music" : "sounds" });
    }

    function sync() {
        if (syncProc.running)
            return;
        root.syncing = true;
        syncProc.running = true;
    }

    function shuffle(list) {
        const a = list.slice();
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function fetch(mode) {
        if (fetchProc.running)
            return false;
        root.fetching = mode === "";
        fetchProc.wantKey = root.wantKey;
        fetchProc.fetchMode = mode;
        fetchProc.command = root.playSource === "music" ? [root.script, "--music", root.theme] : [root.script, root.theme];
        fetchProc.running = true;
        return true;
    }

    function load() {
        if (root.wantsMusic && root.musicStatus.configured === undefined)
            return;
        if (!root.shouldPlay) {
            fadeOut.start();
            return;
        }
        if (root.filesKey === root.wantKey && root.files.length > 0) {
            if (!root.playing)
                root.start();
            return;
        }
        root.fetch("");
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

    function switchAway() {
        fadeOut.switching = true;
        fadeOut.start();
    }

    function loadNames() {
        namesProc.command = root.playSource === "music" ? [root.script, "--music-names"] : [root.script, "--names", root.theme];
        namesProc.running = true;
    }

    function received(list) {
        const mode = fetchProc.fetchMode;
        if (fetchProc.wantKey !== root.wantKey) {
            settle.restart();
            return;
        }
        if (mode === "check") {
            const same = list.length === root.files.length && list.every(f => root.files.includes(f));
            if (same)
                root.filesKey = root.wantKey;
            else
                root.switchAway();
            return;
        }
        if (mode === "refresh" && root.filesKey === root.wantKey && root.files.length > 0) {
            const current = root.currentFile;
            const kept = root.files.filter(f => list.includes(f));
            root.files = kept.concat(root.shuffle(list.filter(f => !kept.includes(f))));
            root.loadNames();
            const i = root.files.indexOf(current);
            if (i >= 0) {
                root.index = i;
            } else {
                root.index = 0;
                player.source = "";
                if (root.shouldPlay)
                    root.start();
                else
                    player.stop();
            }
            return;
        }
        root.files = root.shuffle(list);
        root.filesKey = fetchProc.wantKey;
        root.loadNames();
        root.index = 0;
        if (root.shouldPlay)
            root.start();
    }

    onShouldPlayChanged: settle.restart()
    onWantKeyChanged: {
        if (root.filesKey === root.wantKey || root.files.length === 0) {
            settle.restart();
        } else if (root.playing && root.playSource === "music" && root.filesKey.startsWith("@music:")) {
            if (!root.fetch("check"))
                root.switchAway();
        } else if (root.playing) {
            root.switchAway();
        } else {
            player.source = "";
            root.files = [];
            root.filesKey = "";
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
        onTriggered: {
            listProc.running = true;
            statusProc.running = true;
        }
    }

    Timer {
        interval: 30 * 60 * 1000
        repeat: true
        triggeredOnStart: true
        running: root.enabled && root.wantsMusic
        onTriggered: root.sync()
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
                root.filesKey = "";
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
        id: statusProc
        running: true
        command: [root.script, "--music-status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.musicStatus = JSON.parse(text);
                } catch (e) {}
                if (root.afterSync) {
                    root.afterSync = false;
                    if (root.playSource === "music" && root.filesKey === root.wantKey && root.files.length > 0) {
                        root.fetch("refresh");
                        return;
                    }
                }
                settle.restart();
            }
        }
    }

    Process {
        id: syncProc
        command: [root.syncScript]
        stdout: StdioCollector {
            onStreamFinished: {
                root.syncing = false;
                root.afterSync = true;
                statusProc.running = true;
            }
        }
    }

    Process {
        id: skipProc
    }

    Process {
        id: namesProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.names = JSON.parse(text);
                } catch (e) {
                    root.names = {};
                }
            }
        }
    }

    Process {
        id: fetchProc
        property string wantKey: ""
        property string fetchMode: ""
        stdout: StdioCollector {
            onStreamFinished: {
                root.fetching = false;
                let list = [];
                try {
                    list = JSON.parse(text);
                } catch (e) {}
                root.received(list);
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
