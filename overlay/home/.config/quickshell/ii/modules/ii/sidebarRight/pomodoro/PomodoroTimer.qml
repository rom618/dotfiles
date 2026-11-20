import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

Item {
    id: root

    property bool editing: false

    implicitHeight: contentColumn.implicitHeight
    implicitWidth: contentColumn.implicitWidth

    /// Accepts "10" (minutes), "1:30", "1:00:00", "45s", "2m", "1h30m"; returns seconds or NaN.
    function parseDuration(input) {
        const text = input.trim().toLowerCase().replace(/\s+/g, "");
        if (/^\d+(\.\d+)?$/.test(text))
            return Math.round(parseFloat(text) * 60);
        if (/^\d+(:\d{1,2}){1,2}$/.test(text))
            return text.split(":").reduce((total, part) => total * 60 + parseInt(part), 0);
        const match = text.match(/^(?:(\d+)h)?(?:(\d+)m(?:in)?)?(?:(\d+)s)?$/);
        if (!match || text === "")
            return NaN;
        return (parseInt(match[1] ?? 0) * 3600) + (parseInt(match[2] ?? 0) * 60) + parseInt(match[3] ?? 0);
    }

    function startEditing() {
        timeInput.text = TimerService.formatDuration(TimerService.countdownSecondsLeft);
        root.editing = true;
        timeInput.selectAll();
        timeInput.forceActiveFocus();
    }

    function finishEditing(apply) {
        if (!root.editing)
            return;
        root.editing = false;
        const seconds = parseDuration(timeInput.text);
        if (apply && seconds > 0)
            TimerService.countdownSet(seconds);
        root.forceActiveFocus();
    }

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        spacing: 0

        CircularProgress {
            Layout.alignment: Qt.AlignHCenter
            lineWidth: 8
            value: TimerService.countdownDuration > 0 ? TimerService.countdownSecondsLeft / TimerService.countdownDuration : 0
            implicitSize: 200
            enableAnimation: true

            MouseArea {
                anchors.fill: parent
                enabled: !root.editing
                cursorShape: Qt.PointingHandCursor
                onClicked: root.startEditing()
                onWheel: wheel => TimerService.countdownAdd(wheel.angleDelta.y > 0 ? 60 : -60)
            }

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 0

                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    visible: !root.editing
                    text: TimerService.formatDuration(TimerService.countdownSecondsLeft)
                    font.pixelSize: 40
                    color: Appearance.m3colors.m3onSurface
                }
                StyledTextInput {
                    id: timeInput
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 150
                    visible: root.editing
                    horizontalAlignment: TextInput.AlignHCenter
                    font.pixelSize: 40
                    color: Appearance.m3colors.m3onSurface
                    onAccepted: root.finishEditing(true)
                    onActiveFocusChanged: if (!activeFocus) root.finishEditing(true)
                    Keys.onEscapePressed: root.finishEditing(false)
                }
                StyledText {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.editing ? Translation.tr("e.g. 10, 1:30, 45s") : TimerService.countdownSecondsLeft === 0 ? Translation.tr("Time's up") : Translation.tr("Timer")
                    font.pixelSize: Appearance.font.pixelSize.normal
                    color: Appearance.colors.colSubtext
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 8
            spacing: 6

            Repeater {
                model: [
                    { "label": "−1m", "delta": -60 },
                    { "label": "+1m", "delta": 60 },
                    { "label": "+5m", "delta": 300 }
                ]
                delegate: RippleButton {
                    required property var modelData
                    implicitHeight: 30
                    implicitWidth: 56
                    buttonRadius: Appearance.rounding.full
                    colBackground: Appearance.colors.colLayer2
                    colBackgroundHover: Appearance.colors.colLayer2Hover
                    colRipple: Appearance.colors.colLayer2Active
                    enabled: modelData.delta > 0 || TimerService.countdownSecondsLeft > 0
                    onClicked: TimerService.countdownAdd(modelData.delta)
                    contentItem: StyledText {
                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        text: modelData.label
                        color: Appearance.colors.colOnLayer2
                    }
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            RippleButton {
                contentItem: StyledText {
                    anchors.centerIn: parent
                    horizontalAlignment: Text.AlignHCenter
                    text: TimerService.countdownRunning ? Translation.tr("Pause") : (TimerService.countdownSecondsLeft === TimerService.countdownDuration || TimerService.countdownSecondsLeft === 0) ? Translation.tr("Start") : Translation.tr("Resume")
                    color: TimerService.countdownRunning ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnPrimary
                }
                implicitHeight: 35
                implicitWidth: 90
                font.pixelSize: Appearance.font.pixelSize.larger
                onClicked: TimerService.toggleCountdown()
                colBackground: TimerService.countdownRunning ? Appearance.colors.colSecondaryContainer : Appearance.colors.colPrimary
                colBackgroundHover: TimerService.countdownRunning ? Appearance.colors.colSecondaryContainer : Appearance.colors.colPrimary
            }

            RippleButton {
                implicitHeight: 35
                implicitWidth: 90

                onClicked: TimerService.resetCountdown()
                enabled: TimerService.countdownRunning || TimerService.countdownSecondsLeft !== TimerService.countdownDuration

                font.pixelSize: Appearance.font.pixelSize.larger
                colBackground: Appearance.colors.colErrorContainer
                colBackgroundHover: Appearance.colors.colErrorContainerHover
                colRipple: Appearance.colors.colErrorContainerActive

                contentItem: StyledText {
                    anchors.centerIn: parent
                    horizontalAlignment: Text.AlignHCenter
                    text: Translation.tr("Reset")
                    color: Appearance.colors.colOnErrorContainer
                }
            }
        }
    }
}
