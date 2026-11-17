pragma ComponentBehavior: Bound
import qs
import qs.services
import qs.modules.common
import qs.modules.common.models
import qs.modules.common.widgets
import qs.modules.common.functions
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland

ButtonMouseArea {
    id: root

    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(root.QsWindow.window?.screen)
    WorkspaceModel {
        id: wsModel
        monitor: root.monitor
    }

    property bool vertical: Config.options.bar.vertical
    property bool superPressAndHeld: false // Relevant modifications at bottom of file

    property real workspaceButtonWidth: 26
    property real activeWorkspaceMargin: 2
    property real activeWorkspaceSize: workspaceButtonWidth - activeWorkspaceMargin * 2
    property real workspaceIconSize: workspaceButtonWidth * 0.69
    readonly property real dpr: root.QsWindow.window?.devicePixelRatio ?? 1
    property real workspaceIconSizeShrinked: workspaceButtonWidth * 0.55
    property real workspaceIconOpacityShrinked: 1
    property real workspaceIconMarginShrinked: -4
    property int workspaceIndexInGroup: (monitor?.activeWorkspace?.id - 1) % wsModel.shownCount
    property real specialTextSize: workspaceButtonWidth * 0.5

    Layout.alignment: vertical ? Qt.AlignHCenter : Qt.AlignVCenter
    Layout.fillWidth: vertical
    Layout.fillHeight: !vertical
    readonly property real barThickness: vertical ? Appearance.sizes.verticalBarWidth : Appearance.sizes.barHeight
    implicitWidth: vertical ? barThickness : occupiedIndicators.implicitWidth
    implicitHeight: vertical ? occupiedIndicators.implicitHeight : barThickness

    property real specialBlur: (wsModel.specialWorkspaceActive && !containsMouse) ? 1 : 0
    Behavior on specialBlur {
        animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
    }

    // Interactions
    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.BackButton
    hoverEnabled: true
    property int hoverIndex: {
        const position = root.vertical ? mouseY : mouseX;
        return Math.floor(position / root.workspaceButtonWidth);
    }

    function switchWorkspaceToHovered() {
        Hyprland.dispatch(`hl.dsp.focus({workspace = ${wsModel.getWorkspaceIdAt(hoverIndex)}})`);
    }

    function toggleSpecial() {
        Hyprland.dispatch(`hl.dsp.workspace.toggle_special("special")`);
    }

    onPressed: mouse => {
        if (mouse.button == Qt.LeftButton)
            switchWorkspaceToHovered();
        else if (mouse.button == Qt.RightButton)
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        else if (mouse.button == Qt.BackButton) 
            toggleSpecial()
    }
    onWheel: event => {
        if (event.angleDelta.y < 0)
            Hyprland.dispatch(`hl.dsp.focus({workspace = "r+1"})`);
        else if (event.angleDelta.y > 0)
            Hyprland.dispatch(`hl.dsp.focus({workspace = "r-1"})`);
    }

    // Indications
    Item {
        id: regularWorkspaces
        anchors.fill: parent

        scale: 1 - 0.08 * root.specialBlur
        layer.smooth: true
        layer.enabled: root.specialBlur > 0
        layer.effect: MultiEffect {
            brightness: -0.1 * root.specialBlur
            blurEnabled: true
            blur: root.specialBlur
            blurMax: 32
        }

        /////////////////// Occupied indicators ///////////////////
        StyledRectangle {
            id: occupiedIndicatorsBg
            anchors.fill: parent
            contentLayer: StyledRectangle.ContentLayer.Group
            color: ColorUtils.transparentize(Appearance.m3colors.m3secondaryContainer, 0.4)
            visible: false
        }

        WorkspaceLayout {
            id: occupiedIndicators
            anchors.centerIn: parent

            layer.enabled: true
            visible: false

            Repeater {
                model: wsModel.shownCount
                delegate: Item {
                    id: wsBg
                    required property int index
                    readonly property int wsId: wsModel.getWorkspaceIdAt(index)
                    property bool currentOccupied: wsModel.occupied[index] && wsId != wsModel.fakeWorkspace
                    property bool previousOccupied: index > 0 && wsModel.occupied[index - 1] && (wsId - 1) != wsModel.fakeWorkspace
                    property bool nextOccupied: index < wsModel.shownCount - 1 && wsModel.occupied[index + 1] && (wsId + 1) != wsModel.fakeWorkspace
                    implicitWidth: root.workspaceButtonWidth
                    implicitHeight: root.workspaceButtonWidth

                    // The idea: over-stretch to occupied sides, animate this for a smooth transition.
                    //           masking already prevents weird overlaps
                    Pill {
                        property real undirectionalWidth: root.workspaceButtonWidth * wsBg.currentOccupied
                        property real undirectionalLength: root.workspaceButtonWidth * (1 + 0.5 * wsBg.previousOccupied + 0.5 * wsBg.nextOccupied) * currentOccupied
                        property real undirectionalOffset: (!wsBg.currentOccupied ? 0.5 : -0.5 * wsBg.previousOccupied) * root.workspaceButtonWidth
                        anchors.verticalCenter: root.vertical ? undefined : parent.verticalCenter
                        anchors.horizontalCenter: root.vertical ? parent.horizontalCenter : undefined
                        x: root.vertical ? 0 : undirectionalOffset
                        y: root.vertical ? undirectionalOffset : 0
                        implicitWidth: root.vertical ? undirectionalWidth : undirectionalLength
                        implicitHeight: root.vertical ? undirectionalLength : undirectionalWidth

                        Behavior on undirectionalWidth {
                            animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
                        }
                        Behavior on undirectionalLength {
                            animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
                        }
                        Behavior on undirectionalOffset {
                            animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
                        }
                    }
                }
            }
        }

        MaskMultiEffect {
            id: occupiedIndicatorsMultiEffect
            z: 1
            anchors.centerIn: parent
            implicitWidth: occupiedIndicators.implicitWidth
            implicitHeight: occupiedIndicators.implicitHeight
            source: occupiedIndicatorsBg
            maskSource: occupiedIndicators
        }

        /////////////////// Active indicator ///////////////////
        TrailingIndicator {
            id: activeIndicator
            anchors.fill: parent
            z: 2

            index: root.workspaceIndexInGroup
        }

        /////////////////// Hover ///////////////////
        TrailingIndicator {
            id: interactionIndicator
            z: 3
            index: root.containsMouse ? root.hoverIndex : root.workspaceIndexInGroup
            color: "transparent"
            StateOverlay {
                id: hoverOverlay
                anchors.fill: interactionIndicator.indicatorRectangle
                radius: root.activeWorkspaceSize / 2
                hover: root.containsMouse
                press: root.containsPress
                drag: true // There are too many layers so we need to force this to be a lil more opaque
                contentColor: Appearance.colors.colPrimary
            }
        }

        /////////////////// Numbers ///////////////////
        WorkspaceLayout {
            id: numbersGrid
            z: 4
            layer.enabled: true // For the masking

            Repeater {
                model: wsModel.shownCount
                delegate: NumberWorkspaceItem {}
            }
        }
        Colorizer {
            z: 5
            anchors.fill: numbersGrid
            colorizationColor: Appearance.colors.colOnPrimary
            sourceColor: Appearance.colors.colOnSecondaryContainer

            source: activeIndicator
            maskEnabled: true
            maskSource: numbersGrid

            maskThresholdMin: 0.5
            maskSpreadAtMin: 1
        }

        /////////////////// App icons ///////////////////
        WorkspaceLayout {
            id: appsGrid
            z: 6

            Repeater {
                model: wsModel.shownCount
                delegate: WorkspaceItem {
                    id: wsApp
                    property var biggestWindow: wsModel.biggestWindow[index]
                    property bool claudeShown: ClaudeWindows.stateFor(biggestWindow) !== ""
                    property string claudeState: claudeShown ? ClaudeWindows.workspaceState(wsId) : ""
                    property string agent: claudeShown ? ClaudeWindows.agentFor(biggestWindow) : ""
                    property bool agentWorking: claudeState === "running" && iconsShown
                    property int subagents: claudeShown && agent === "claude" ? ClaudeWindows.workspaceSubagents(wsId) : 0
                    property int unread: claudeShown ? ClaudeWindows.workspaceUnread(wsId) : 0
                    property bool iconsShown: !root.superPressAndHeld && Config.options?.bar.workspaces.showAppIcons && !!biggestWindow
                    property var mainAppIconSource: claudeShown ? ClaudeWindows.iconFor(biggestWindow) : Quickshell.iconPath(AppSearch.guessIcon(biggestWindow?.class), "image-missing")

                    AppIcon {
                        id: appIcon
                        property real cornerMargin: (!root.superPressAndHeld && Config.options?.bar.workspaces.showAppIcons && wsApp.biggestWindow) ? (root.workspaceButtonWidth - root.workspaceIconSize) / 2 : root.workspaceIconMarginShrinked
                        anchors {
                            bottom: parent.bottom
                            right: parent.right
                            bottomMargin: (parent.implicitHeight - root.workspaceButtonWidth) / 2 + cornerMargin
                            rightMargin: (parent.implicitWidth - root.workspaceButtonWidth) / 2 + cornerMargin
                        }

                        animated: !wsApp.biggestWindow // Prevent the "image-missing" icon
                        visible: false // Prevent dupe: the colorizer already copies the icon

                        source: wsApp.mainAppIconSource
                        implicitSize: Math.round(NumberUtils.roundToEven(root.workspaceIconSize) * root.dpr) / root.dpr

                        Behavior on opacity {
                            animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                        }
                        Behavior on cornerMargin {
                            animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
                        }
                    }

                    Circle {
                        id: iconMask
                        visible: false
                        layer.enabled: true
                        layer.textureSize: appIconTexture.textureSize
                        layer.smooth: appIconTexture.smooth
                        diameter: appIcon.implicitSize
                    }

                    // Pixel-exact texture sampled without filtering at rest, so fractional scales don't blur the icon
                    ShaderEffectSource {
                        id: appIconTexture
                        visible: false
                        sourceItem: appIcon
                        textureSize: Qt.size(Math.round(appIcon.width * root.dpr), Math.round(appIcon.height * root.dpr))
                        smooth: colorizer.rotation !== 0 || colorizer.item?.scale !== 1
                    }

                    Loader { // Somehow putting this multieffect in a loader prevents it from not showing up
                        id: colorizer
                        anchors.fill: appIcon
                        rotation: 0
                        RotationAnimation on rotation {
                            readonly property bool mainRunning: wsApp.claudeState === "running" && wsApp.agent === "claude"
                            running: mainRunning || (wsApp.subagents > 0 && wsApp.claudeState !== "waiting")
                            from: 0
                            to: 360
                            duration: mainRunning ? 3000 : 9000
                            loops: Animation.Infinite
                            onRunningChanged: if (!running) colorizer.rotation = 0
                            onDurationChanged: if (running) restart()
                        }
                        sourceComponent: Colorizer {
                            implicitWidth: appIcon.implicitWidth
                            implicitHeight: appIcon.implicitHeight
                            colorizationColor: Appearance.m3colors.darkmode ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnPrimary
                            colorization: Config.options.bar.workspaces.monochromeIcons ? 0.8 : 0.5
                            brightness: 0
                            source: appIconTexture

                            opacity: !Config.options?.bar.workspaces.showAppIcons ? 0 : (wsApp.biggestWindow && !root.superPressAndHeld && Config.options?.bar.workspaces.showAppIcons) ? 1 : wsApp.biggestWindow ? root.workspaceIconOpacityShrinked : 0
                            visible: opacity > 0
                            scale: ((!root.superPressAndHeld && Config.options?.bar.workspaces.showAppIcons) ? root.workspaceIconSize : root.workspaceIconSizeShrinked) / root.workspaceIconSize

                            Behavior on opacity {
                                animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                            }
                            Behavior on scale {
                                animation: Appearance.animation.elementMoveSmall.numberAnimation.createObject(this)
                            }

                            maskEnabled: true
                            maskSource: iconMask
                            maskThresholdMin: 0.5
                            maskSpreadAtMin: 1
                        }
                    }

                    Item {
                        id: piOrbit
                        anchors.centerIn: appIcon
                        width: appIcon.implicitSize + 6
                        height: width
                        visible: wsApp.agentWorking && wsApp.agent === "pi"
                        rotation: 0
                        RotationAnimation on rotation {
                            running: piOrbit.visible
                            from: 0
                            to: 360
                            duration: 1100
                            loops: Animation.Infinite
                        }
                        Repeater {
                            model: 3
                            delegate: Rectangle {
                                required property int index
                                readonly property real angle: -index * 22 * Math.PI / 180
                                readonly property real r: piOrbit.width / 2
                                width: 4 - index
                                height: width
                                radius: width / 2
                                x: piOrbit.width / 2 + r * Math.sin(angle) - width / 2
                                y: piOrbit.height / 2 - r * Math.cos(angle) - height / 2
                                color: Appearance.colors.colPrimary
                                opacity: 1 - index * 0.3
                            }
                        }
                    }

                    Rectangle {
                        id: codexRipple
                        property real spread: 1
                        anchors.centerIn: appIcon
                        width: appIcon.implicitSize * spread
                        height: width
                        radius: width / 2
                        color: "transparent"
                        border.width: 1.5
                        border.color: Appearance.colors.colPrimary
                        visible: wsApp.agentWorking && wsApp.agent === "codex"
                        SequentialAnimation {
                            running: codexRipple.visible
                            loops: Animation.Infinite
                            ParallelAnimation {
                                NumberAnimation { target: codexRipple; property: "spread"; from: 0.9; to: 1.7; duration: 1300; easing.type: Easing.OutCubic }
                                NumberAnimation { target: codexRipple; property: "opacity"; from: 0.9; to: 0; duration: 1300; easing.type: Easing.OutCubic }
                            }
                            PauseAnimation { duration: 200 }
                        }
                    }

                    Rectangle {
                        id: claudeBadge
                        readonly property bool waiting: wsApp.claudeState === "waiting"
                        readonly property bool counting: !waiting && wsApp.unread > 0
                        visible: wsApp.iconsShown && (waiting || counting || wsApp.claudeState === "done")
                        anchors {
                            right: appIcon.right
                            bottom: appIcon.bottom
                            rightMargin: -3
                            bottomMargin: -3
                        }
                        width: 10
                        height: 10
                        radius: 5
                        color: waiting ? Appearance.colors.colError : counting ? Appearance.m3colors.m3primary : Appearance.m3colors.m3success
                        border.width: 1
                        border.color: Appearance.colors.colLayer1

                        StyledText {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            visible: claudeBadge.counting
                            text: Math.min(wsApp.unread, 9)
                            font.pixelSize: 8
                            font.weight: Font.Normal
                            color: Appearance.m3colors.m3onPrimary
                        }

                        MaterialSymbol {
                            anchors.centerIn: parent
                            visible: !claudeBadge.counting
                            text: claudeBadge.waiting ? "priority_high" : "check"
                            iconSize: 8
                            fill: 1
                            color: claudeBadge.waiting ? Appearance.m3colors.m3onError : Appearance.m3colors.m3onSuccess
                        }

                        SequentialAnimation on opacity {
                            running: claudeBadge.waiting && claudeBadge.visible
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.35; duration: 600 }
                            NumberAnimation { to: 1; duration: 600 }
                            onRunningChanged: if (!running) claudeBadge.opacity = 1
                        }
                    }

                    Rectangle {
                        id: subagentBadge
                        property real snapX: 0
                        property real snapY: 0
                        // À l'échelle 1,25 un chiffre tombe entre deux pixels et paraît plus ou moins gras : on cale la pastille sur un pixel entier.
                        function caler() {
                            const g = mapToItem(null, 0, 0);
                            snapX += Math.round(g.x * root.dpr) / root.dpr - g.x;
                            snapY += Math.round(g.y * root.dpr) / root.dpr - g.y;
                        }
                        onXChanged: Qt.callLater(caler)
                        onYChanged: Qt.callLater(caler)
                        onVisibleChanged: if (visible) Qt.callLater(caler)
                        Component.onCompleted: Qt.callLater(caler)
                        Timer {
                            interval: 250
                            repeat: true
                            running: parent.visible
                            onTriggered: parent.caler()
                        }
                        visible: wsApp.iconsShown && wsApp.subagents > 0
                        anchors {
                            left: appIcon.left
                            bottom: appIcon.bottom
                            leftMargin: -3 + snapX
                            bottomMargin: -3 - snapY
                        }
                        width: 10
                        height: 10
                        radius: 5
                        color: "transparent"

                        StyledText {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            text: Math.min(wsApp.subagents, 9)
                            font.pixelSize: 10
                            font.weight: Font.Normal
                            color: Appearance.m3colors.m3onSecondaryContainer
                            style: Text.Outline
                            styleColor: Appearance.colors.colLayer1
                        }
                    }
                }
            }
        }
    }

    FadeLoader {
        anchors.centerIn: parent
        shown: wsModel.specialWorkspaceActive
        scale: 0.8 + 0.2 * root.specialBlur

        opacity: root.specialBlur
        Behavior on opacity {} // Don't animate, as specialBlur is already animated

        sourceComponent: Pill {
            anchors.centerIn: parent
            property real undirectionalWidth: root.activeWorkspaceSize
            property real undirectionalLength: {
                const base = root.workspaceButtonWidth * Math.min(1.35, wsModel.shownCount); // Who tf only configures only 2 workspaces shown anyway?
                if (root.vertical)
                    return base;
                return specialWsText.implicitWidth + undirectionalWidth;
            }
            color: Appearance.colors.colPrimary

            implicitWidth: root.vertical ? undirectionalWidth : undirectionalLength
            implicitHeight: root.vertical ? undirectionalLength : undirectionalWidth

            StyledText {
                id: specialWsText
                anchors.centerIn: parent
                text: (!root.vertical ? wsModel.specialWorkspaceName : "S")
                color: Appearance.colors.colOnPrimary
                font.pixelSize: root.specialTextSize
            }

            Behavior on undirectionalLength {
                animation: Appearance.animation.elementMoveEnter.numberAnimation.createObject(this)
            }
        }
    }

    /////////////////// Super key press handling ///////////////////
    Timer {
        id: superPressAndHeldTimer
        interval: (Config?.options.bar.autoHide.showWhenPressingSuper.delay ?? 100)
        repeat: false
        onTriggered: {
            root.superPressAndHeld = true;
        }
    }
    Connections {
        target: GlobalStates
        function onSuperDownChanged() {
            if (!Config?.options.bar.autoHide.showWhenPressingSuper.enable)
                return;
            if (GlobalStates.superDown)
                superPressAndHeldTimer.restart();
            else {
                superPressAndHeldTimer.stop();
                root.superPressAndHeld = false;
            }
        }
        function onSuperReleaseMightTriggerChanged() {
            superPressAndHeldTimer.stop();
        }
    }

    component WorkspaceLayout: Box {
        anchors {
            top: !root.vertical ? parent.top : undefined
            bottom: !root.vertical ? parent.bottom : undefined
            left: root.vertical ? parent.left : undefined
            right: root.vertical ? parent.right : undefined
        }

        rowSpacing: 0
        columnSpacing: 0
        vertical: root.vertical
    }

    component WorkspaceItem: Item {
        required property int index
        readonly property int wsId: wsModel.getWorkspaceIdAt(index)
        implicitWidth: root.vertical ? root.barThickness : root.workspaceButtonWidth
        implicitHeight: root.vertical ? root.workspaceButtonWidth : root.barThickness
    }

    component NumberWorkspaceItem: WorkspaceItem {
        id: wsNum
        property bool hasBiggestWindow: !!wsModel.biggestWindow[index]
        property bool openLogo: hasBiggestWindow && !root.superPressAndHeld && Config.options?.bar.workspaces.showAppIcons
            && ClaudeWindows.stateFor(wsModel.biggestWindow[index]) !== ""
        property int wsId: wsModel.getWorkspaceIdAt(index)
        property color contentColor: (wsModel.occupied[wsNum.index] && wsId !== wsModel.fakeWorkspace) ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer1Inactive
        property bool showingNumbers: {
            if (root.superPressAndHeld)
                return true;
            if (GlobalStates.screenLocked)
                return false;
            if (Config.options?.bar.workspaces.alwaysShowNumbers && (!Config.options?.bar.workspaces.showAppIcons || !wsNum.hasBiggestWindow))
                return true;
            return false;
        }

        FadeLoader {
            shown: !wsNum.showingNumbers && !wsNum.openLogo
            anchors.centerIn: parent
            Circle {
                anchors.centerIn: parent
                diameter: root.workspaceButtonWidth * 0.18
                color: wsNum.contentColor
            }
        }
        FadeLoader {
            shown: wsNum.showingNumbers
            anchors.centerIn: parent
            StyledText {
                anchors.centerIn: parent
                font {
                    pixelSize: Appearance.font.pixelSize.small - ((text.length - 1) * (text !== "10") * 2)
                    family: Config.options?.bar.workspaces.useNerdFont ? Appearance.font.family.iconNerd : defaultFont
                }
                color: wsNum.contentColor
                text: Config.options?.bar.workspaces.numberMap[wsNum.wsId - 1] || wsNum.wsId
            }
        }
    }

    component TrailingIndicator: Item {
        id: trailingIndicator
        anchors.fill: parent
        required property int index
        property alias indicatorRectangle: indicatorRect
        property alias color: indicatorRect.color

        property var indexPair: AnimatedTabIndexPair {
            id: idxPair
            index: trailingIndicator.index
        }

        StyledRectangle {
            id: indicatorRect

            anchors {
                verticalCenter: root.vertical ? undefined : parent.verticalCenter
                horizontalCenter: root.vertical ? parent.horizontalCenter : undefined
            }

            property real indicatorPosition: Math.min(idxPair.idx1, idxPair.idx2) * root.workspaceButtonWidth + root.activeWorkspaceMargin
            property real indicatorLength: Math.abs(idxPair.idx1 - idxPair.idx2) * root.workspaceButtonWidth + root.activeWorkspaceSize
            property real indicatorThickness: root.activeWorkspaceSize

            contentLayer: StyledRectangle.ContentLayer.Group
            radius: indicatorThickness / 2
            color: Appearance.colors.colPrimary

            x: root.vertical ? null : indicatorPosition
            y: root.vertical ? indicatorPosition : null
            implicitWidth: root.vertical ? indicatorThickness : indicatorLength
            implicitHeight: root.vertical ? indicatorLength : indicatorThickness
        }
    }
}
