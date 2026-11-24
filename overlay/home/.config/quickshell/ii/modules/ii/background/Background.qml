pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.widgets.widgetCanvas
import qs.modules.common.functions as CF
import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

import qs.modules.ii.background.widgets
import qs.modules.ii.background.widgets.clock
import qs.modules.ii.background.widgets.weather

Variants {
    id: root
    model: Quickshell.screens

    PanelWindow {
        id: bgRoot

        required property var modelData

        // Hide when fullscreen
        property list<HyprlandWorkspace> workspacesForMonitor: Hyprland.workspaces.values.filter(workspace => workspace.monitor && workspace.monitor.name == monitor.name)
        property var activeWorkspaceWithFullscreen: workspacesForMonitor.filter(workspace => ((workspace.toplevels.values.filter(window => window.wayland?.fullscreen)[0] != undefined) && workspace.active))[0]
        visible: GlobalStates.screenLocked || (!(activeWorkspaceWithFullscreen != undefined)) || !Config?.options.background.hideWhenFullscreen

        // Workspaces
        property HyprlandMonitor monitor: Hyprland.monitors.values.find(m => m.name === modelData?.name) ?? null
        property list<var> relevantWindows: HyprlandData.windowList.filter(win => win.monitor == monitor?.id && win.workspace.id >= 0).sort((a, b) => a.workspace.id - b.workspace.id)
        property int firstWorkspaceId: relevantWindows[0]?.workspace.id || 1
        property int lastWorkspaceId: relevantWindows[relevantWindows.length - 1]?.workspace.id || 10
        property int workspaceChunkSize: Config?.options.bar.workspaces.shown ?? 10
        property int totalWorkspaces: Math.ceil(lastWorkspaceId / workspaceChunkSize) * workspaceChunkSize
        // Wallpaper
        property bool wallpaperIsVideo: Config.options.background.wallpaperPath.endsWith(".mp4") || Config.options.background.wallpaperPath.endsWith(".webm") || Config.options.background.wallpaperPath.endsWith(".mkv") || Config.options.background.wallpaperPath.endsWith(".avi") || Config.options.background.wallpaperPath.endsWith(".mov")
        property string wallpaperPath: wallpaperIsVideo ? Config.options.background.thumbnailPath : Config.options.background.wallpaperPath
        property bool wallpaperSafetyTriggered: {
            const enabled = Config.options.workSafety.enable.wallpaper;
            const sensitiveWallpaper = (CF.StringUtils.stringListContainsSubstring(wallpaperPath.toLowerCase(), Config.options.workSafety.triggerCondition.fileKeywords));
            const sensitiveNetwork = (CF.StringUtils.stringListContainsSubstring(Network.networkName.toLowerCase(), Config.options.workSafety.triggerCondition.networkNameKeywords));
            return enabled && sensitiveWallpaper && sensitiveNetwork;
        }
        readonly property real parallaxRation: Config.options.background.parallax.workspaceZoom
        property real minSuitableScale: 1 // Some reasonable init, to be updated
        property real effectiveWallpaperScale: minSuitableScale * parallaxRation
        property int wallpaperWidth: modelData.width // Some reasonable init value, to be updated
        property int wallpaperHeight: modelData.height // Some reasonable init value, to be updated
        property real scaledWallpaperWidth: wallpaperWidth * effectiveWallpaperScale
        property real scaledWallpaperHeight: wallpaperHeight * effectiveWallpaperScale
        property real parallaxTotalPixelsX: Math.max(0, scaledWallpaperWidth - screen.width)
        property real parallaxTotalPixelsY: Math.max(0, scaledWallpaperHeight - screen.height)
        readonly property bool verticalParallax: (Config.options.background.parallax.autoVertical && wallpaperHeight > wallpaperWidth) || Config.options.background.parallax.vertical
        // Colors
        property bool shouldBlur: (GlobalStates.screenLocked && Config.options.lock.blur.enable)
        property color dominantColor: Appearance.colors.colPrimary // Default, to be changed
        property bool dominantColorIsDark: dominantColor.hslLightness < 0.5
        property color colText: {
            if (wallpaperSafetyTriggered)
                return CF.ColorUtils.mix(Appearance.colors.colOnLayer0, Appearance.colors.colPrimary, 0.75);
            return (GlobalStates.screenLocked && shouldBlur) ? Appearance.colors.colOnLayer0 : CF.ColorUtils.colorWithLightness(Appearance.colors.colPrimary, (dominantColorIsDark ? 0.8 : 0.12));
        }
        Behavior on colText {
            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
        }

        // Layer props
        screen: modelData
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: (GlobalStates.screenLocked && !scaleAnim.running) ? WlrLayer.Overlay : WlrLayer.Background
        // WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell:background"
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        color: {
            if (!bgRoot.wallpaperSafetyTriggered || bgRoot.wallpaperIsVideo)
                return "transparent";
            return CF.ColorUtils.mix(Appearance.colors.colLayer0, Appearance.colors.colPrimary, 0.75);
        }
        Behavior on color {
            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
        }

        readonly property string targetPath: wallpaperSafetyTriggered ? "" : wallpaperPath
        property string shownPath: ""
        property string incomingPath: ""
        property bool incomingSized: false
        property bool changePending: false
        property int incomingWidth: modelData.width
        property int incomingHeight: modelData.height
        property int frontSlot: 0
        property bool snapGeometry: false

        onTargetPathChanged: bgRoot.beginWallpaperChange()
        Component.onCompleted: bgRoot.beginWallpaperChange()

        function decodeSize(w, h) {
            const scale = Math.max(bgRoot.screen.width / w, bgRoot.screen.height / h) * bgRoot.parallaxRation;
            return Qt.size(Math.round(w * scale * wallpaper.dpr), Math.round(h * scale * wallpaper.dpr));
        }

        function beginWallpaperChange() {
            const path = bgRoot.targetPath;
            const back = bgRoot.frontSlot === 0 ? slotB : slotA;
            if (path === bgRoot.shownPath && !bgRoot.changePending) {
                return;
            }
            bgRoot.incomingPath = path;
            bgRoot.incomingSized = false;
            bgRoot.changePending = true;
            back.source = "";
            if (path === "") {
                bgRoot.incomingSized = true;
                bgRoot.tryCommitWallpaper();
                return;
            }
            getWallpaperSizeProc.running = false;
            getWallpaperSizeProc.path = path;
            getWallpaperSizeProc.running = true;
        }

        function tryCommitWallpaper() {
            const back = bgRoot.frontSlot === 0 ? slotB : slotA;
            if (!bgRoot.changePending || !bgRoot.incomingSized || MaterialThemeLoader.hold)
                return;
            if (bgRoot.incomingPath !== "" && back.status !== Image.Ready && back.status !== Image.Error)
                return;
            bgRoot.snapGeometry = true;
            bgRoot.wallpaperWidth = bgRoot.incomingWidth;
            bgRoot.wallpaperHeight = bgRoot.incomingHeight;
            bgRoot.minSuitableScale = Math.max(bgRoot.screen.width / bgRoot.incomingWidth, bgRoot.screen.height / bgRoot.incomingHeight);
            const front = bgRoot.frontSlot === 0 ? slotA : slotB;
            front.z = 0;
            back.z = 1;
            back.opacity = 0;
            bgRoot.frontSlot = 1 - bgRoot.frontSlot;
            bgRoot.shownPath = bgRoot.incomingPath;
            bgRoot.incomingPath = "";
            bgRoot.changePending = false;
            bgRoot.incomingSized = false;
            crossfade.target = back;
            crossfade.restart();
            bgRoot.snapGeometry = false;
        }

        Connections {
            target: MaterialThemeLoader
            function onHoldChanged() {
                bgRoot.tryCommitWallpaper();
            }
        }

        NumberAnimation {
            id: crossfade
            property: "opacity"
            from: 0
            to: 1
            duration: 450
            easing.type: Easing.InOutCubic
            onFinished: {
                const old = bgRoot.frontSlot === 0 ? slotB : slotA;
                if (!bgRoot.changePending)
                    old.source = "";
            }
        }

        Process {
            id: getWallpaperSizeProc
            property string path: ""
            command: ["magick", "identify", "-format", "%w %h", path + "[0]"]
            stdout: StdioCollector {
                id: wallpaperSizeOutputCollector
                onStreamFinished: {
                    if (getWallpaperSizeProc.path !== bgRoot.incomingPath)
                        return;
                    const [width, height] = wallpaperSizeOutputCollector.text.split(" ").map(Number);
                    const ok = width > 0 && height > 0;
                    bgRoot.incomingWidth = ok ? width : bgRoot.screen.width;
                    bgRoot.incomingHeight = ok ? height : bgRoot.screen.height;
                    const back = bgRoot.frontSlot === 0 ? slotB : slotA;
                    back.sourceSize = bgRoot.decodeSize(bgRoot.incomingWidth, bgRoot.incomingHeight);
                    back.source = bgRoot.incomingPath;
                    bgRoot.incomingSized = true;
                    bgRoot.tryCommitWallpaper();
                }
            }
        }

        component WallpaperSlot: Image {
            anchors.fill: parent
            asynchronous: true
            cache: false
            smooth: false
            fillMode: Image.PreserveAspectCrop
            onStatusChanged: {
                if (status === Image.Ready || status === Image.Error)
                    bgRoot.tryCommitWallpaper();
            }
        }

        Item {
            anchors.fill: parent

            // Wallpaper
            Item {
                id: wallpaper
                readonly property Image frontImage: bgRoot.frontSlot === 0 ? slotA : slotB
                readonly property bool ready: frontImage.status === Image.Ready
                readonly property real dpr: (QsWindow.window as QsWindow)?.devicePixelRatio ?? 1
                visible: opacity > 0 && !blurLoader.active
                opacity: (ready && !bgRoot.wallpaperIsVideo) ? 1 : 0
                Behavior on opacity {
                    animation: Appearance.animation.elementMoveEnter.numberAnimation.createObject(this)
                }

                WallpaperSlot {
                    id: slotA
                }
                WallpaperSlot {
                    id: slotB
                }

                property int workspaceIndex: (bgRoot.monitor.activeWorkspace?.id ?? 1) - 1
                property real middleFraction: 0.5
                property real fraction: {
                    // 0 - start of the picture
                    // 1 - end of the picture
                    if (bgRoot.totalWorkspaces <= 1) {
                        return middleFraction;
                    }
                    return Math.max(0, Math.min(1, workspaceIndex / (bgRoot.totalWorkspaces - 1)));
                }

                property real usedFractionX: {
                    let usedFraction = middleFraction;
                    if (Config.options.background.parallax.enableWorkspace && !bgRoot.verticalParallax) {
                        usedFraction = fraction;
                    }
                    if (Config.options.background.parallax.enableSidebar) {
                        let sidebarFraction = bgRoot.parallaxRation / bgRoot.workspaceChunkSize / 2;
                        usedFraction += (sidebarFraction * GlobalStates.sidebarRightOpen - sidebarFraction * GlobalStates.sidebarLeftOpen);
                    }
                    return Math.max(0, Math.min(1, usedFraction));
                }
                property real usedFractionY: {
                    let usedFraction = middleFraction;
                    if (Config.options.background.parallax.enableWorkspace && bgRoot.verticalParallax) {
                        usedFraction = fraction;
                    }
                    return Math.max(0, Math.min(1, usedFraction));
                }

                x: {
                    if (bgRoot.screen.width > width) {
                        // Center the picture
                        return (bgRoot.screen.width - width) / 2;
                    }
                    return - bgRoot.parallaxTotalPixelsX * usedFractionX;
                }
                y: {
                    if (bgRoot.screen.height > height) {
                        // Center the picture
                        return (bgRoot.screen.height - height) / 2;
                    }
                    return - bgRoot.parallaxTotalPixelsY * usedFractionY;
                }

                Behavior on x {
                    enabled: !bgRoot.snapGeometry
                    NumberAnimation {
                        duration: 600
                        easing.type: Easing.OutCubic
                    }
                }
                Behavior on y {
                    enabled: !bgRoot.snapGeometry
                    NumberAnimation {
                        duration: 600
                        easing.type: Easing.OutCubic
                    }
                }
                width: bgRoot.scaledWallpaperWidth
                height: bgRoot.scaledWallpaperHeight
            }

            Loader {
                id: blurLoader
                active: Config.options.lock.blur.enable && (GlobalStates.screenLocked || scaleAnim.running)
                anchors.fill: wallpaper
                scale: GlobalStates.screenLocked ? Config.options.lock.blur.extraZoom : 1
                Behavior on scale {
                    NumberAnimation {
                        id: scaleAnim
                        duration: 400
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Appearance.animationCurves.expressiveDefaultSpatial
                    }
                }
                sourceComponent: GaussianBlur {
                    source: wallpaper
                    radius: GlobalStates.screenLocked ? Config.options.lock.blur.radius : 0
                    samples: radius * 2 + 1

                    Rectangle {
                        opacity: GlobalStates.screenLocked ? 1 : 0
                        anchors.fill: parent
                        color: CF.ColorUtils.transparentize(Appearance.colors.colLayer0, 0.7)
                    }
                }
            }

            WidgetCanvas {
                id: widgetCanvas
                width: parent.width
                height: parent.height
                readonly property real parallaxFactor: {
                    var f = Config.options.background.parallax.widgetsFactor;
                    return f / bgRoot.parallaxRation;
                }
                readonly property real baseWallpaperOffsetX: (bgRoot.screen.width - wallpaper.width) / 2
                readonly property real baseWallpaperOffsetY: (bgRoot.screen.height - wallpaper.height) / 2
                readonly property real wallpaperTotalOffsetX: wallpaper.x - baseWallpaperOffsetX
                readonly property real wallpaperTotalOffsetY: wallpaper.y - baseWallpaperOffsetY
                readonly property bool locked: GlobalStates.screenLocked
                x: wallpaperTotalOffsetX * parallaxFactor * !locked
                y: wallpaperTotalOffsetY * parallaxFactor * !locked

                transitions: Transition {
                    PropertyAnimation {
                        properties: "width,height"
                        duration: Appearance.animation.elementMove.duration
                        easing.type: Appearance.animation.elementMove.type
                        easing.bezierCurve: Appearance.animation.elementMove.bezierCurve
                    }
                    AnchorAnimation {
                        duration: Appearance.animation.elementMove.duration
                        easing.type: Appearance.animation.elementMove.type
                        easing.bezierCurve: Appearance.animation.elementMove.bezierCurve
                    }
                }

                FadeLoader {
                    shown: Config.options.background.widgets.weather.enable
                    sourceComponent: WeatherWidget {
                        screenWidth: bgRoot.screen.width
                        screenHeight: bgRoot.screen.height
                        scaledScreenWidth: bgRoot.screen.width
                        scaledScreenHeight: bgRoot.screen.height
                        wallpaperScale: 1
                    }
                }

                FadeLoader {
                    shown: Config.options.background.widgets.clock.enable
                    sourceComponent: ClockWidget {
                        screenWidth: bgRoot.screen.width
                        screenHeight: bgRoot.screen.height
                        scaledScreenWidth: bgRoot.screen.width
                        scaledScreenHeight: bgRoot.screen.height
                        wallpaperScale: 1
                        wallpaperSafetyTriggered: bgRoot.wallpaperSafetyTriggered
                    }
                }
            }
        }
    }
}
