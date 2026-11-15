pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

/**
 * Automatically reloads generated material colors.
 * It is necessary to run reapplyTheme() on startup because Singletons are lazily loaded.
 */
Singleton {
    id: root
    property string filePath: Directories.generatedMaterialThemePath

    function reapplyTheme() {
        themeFileView.reload()
    }

    property bool hold: false
    property bool animateNext: false
    property color targetBackground: Appearance.m3colors.m3background
    property var fromColors: ({})
    property var toColors: ({})
    property bool targetDark: false
    property real blend: 1

    Timer {
        id: holdLimit
        interval: 20000
        onTriggered: root.hold = false
    }

    onHoldChanged: {
        if (hold) {
            holdLimit.restart()
        } else {
            holdLimit.stop()
            root.animateNext = true
            delayedFileRead.restart()
        }
    }

    function applyColors(fileContent) {
        let json
        try {
            json = JSON.parse(fileContent)
        } catch (e) {
            return
        }
        const from = {}
        const to = {}
        for (const key in json) {
            if (!json.hasOwnProperty(key))
                continue
            const camelCaseKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase())
            const m3Key = `m3${camelCaseKey}`
            const current = Appearance.m3colors[m3Key]
            if (root.animateNext && current !== undefined && typeof json[key] === "string" && json[key].startsWith("#")) {
                if (!Qt.colorEqual(current, json[key])) {
                    from[m3Key] = Qt.color(current)
                    to[m3Key] = Qt.color(json[key])
                }
            } else {
                Appearance.m3colors[m3Key] = json[key]
            }
        }
        const bg = json.background ? Qt.color(json.background) : Appearance.m3colors.m3background
        root.targetBackground = bg
        root.targetDark = bg.hslLightness < 0.5
        blendTimer.stop()
        if (Object.keys(to).length === 0) {
            root.animateNext = false
            Appearance.m3colors.darkmode = root.targetDark
            return
        }
        root.fromColors = from
        root.toColors = to
        root.animateNext = false
        root.blendStart = Date.now()
        root.blend = 0
        root.stepBlend()
        blendTimer.restart()
    }

    function stepBlend() {
        const t = root.blend
        const u = 1 - t
        for (const key in root.toColors) {
            const a = root.fromColors[key]
            const b = root.toColors[key]
            Appearance.m3colors[key] = t >= 1 ? b : Qt.rgba(a.r * u + b.r * t, a.g * u + b.g * t, a.b * u + b.b * t, a.a * u + b.a * t)
        }
        if (t >= 0.5 && Appearance.m3colors.darkmode !== root.targetDark)
            Appearance.m3colors.darkmode = root.targetDark
    }

    property real blendStart: 0
    readonly property int blendDuration: 450

    Timer {
        id: blendTimer
        interval: 16
        repeat: true
        onTriggered: {
            const x = Math.min(1, (Date.now() - root.blendStart) / root.blendDuration)
            root.blend = x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2
            root.stepBlend()
            if (x >= 1)
                stop()
        }
    }

    function resetFilePathNextTime() {
        resetFilePathNextWallpaperChange.enabled = true
    }

    Connections {
        id: resetFilePathNextWallpaperChange
        enabled: false
        target: Config.options.background
        function onWallpaperPathChanged() {
            root.filePath = ""
            root.filePath = Directories.generatedMaterialThemePath
            resetFilePathNextWallpaperChange.enabled = false
        }
    }

    Timer {
        id: delayedFileRead
        interval: Config.options?.hacks?.arbitraryRaceConditionDelay ?? 100
        repeat: false
        running: false
        onTriggered: {
            root.applyColors(themeFileView.text())
        }
    }

	FileView { 
        id: themeFileView
        path: Qt.resolvedUrl(root.filePath)
        watchChanges: true
        onFileChanged: {
            this.reload()
            if (root.hold)
                return
            root.animateNext = true
            delayedFileRead.restart()
        }
        onLoadedChanged: {
            if (!loaded || root.hold || delayedFileRead.running || blendTimer.running)
                return
            const fileContent = themeFileView.text()
            root.applyColors(fileContent)
        }
        onLoadFailed: root.resetFilePathNextTime();
    }

    function toggleLightDark() {
        const currentlyDark = Appearance.m3colors.darkmode;
        Quickshell.execDetached([Directories.wallpaperSwitchScriptPath, "--mode", currentlyDark ? "light" : "dark", "--noswitch"]);
    }

    GlobalShortcut {
        name: "toggleLightDark"
        description: "Toggles between dark theme and light theme"

        onPressed: {
            root.toggleLightDark();
        }
    }

    IpcHandler {
        target: "theme"

        function toggleLightDark(): void {
            root.toggleLightDark();
        }

        function hold(): void {
            root.hold = true;
        }

        function release(): void {
            root.hold = false;
        }
    }
}
