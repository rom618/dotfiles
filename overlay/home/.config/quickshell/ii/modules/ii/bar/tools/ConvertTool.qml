import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.modules.common
import qs.modules.common.widgets
import qs.services

ColumnLayout {
    id: tool
    required property var host
    spacing: 10

    readonly property var res: UnitConverter.result
    readonly property bool hasResult: !!res && res.ok && UnitConverter.query.trim() !== ""
    property string copied: ""
    readonly property var examples: ["5 ft to cm", "100 usd in eur", "30 C to F", "2 cups to ml", "70 kg", "60 mph"]
    readonly property var kindNames: ({ length: "Length", mass: "Mass", temperature: "Temperature", volume: "Volume", area: "Area", speed: "Speed", time: "Time", data: "Data", energy: "Energy", power: "Power", pressure: "Pressure", currency: "Currency" })

    function copy(text) {
        Quickshell.execDetached(["wl-copy", "--", text]);
        tool.copied = text;
        copiedTimer.restart();
    }

    function setTarget(unit) {
        const expr = tool.res?.expr ?? UnitConverter.query;
        const m = expr.match(/^(.*\S)\s+to\s+\S.*$/i);
        input.text = (m ? m[1] : expr) + " to " + unit;
        input.forceActiveFocus();
    }

    Component.onCompleted: UnitConverter.warm()

    Timer {
        id: copiedTimer
        interval: 1500
        onTriggered: tool.copied = ""
    }

    MaterialTextField {
        id: input
        Layout.fillWidth: true
        placeholderText: "5 ft to cm, 100 usd in eur, 30 C to F..."
        text: UnitConverter.query
        wrapMode: TextEdit.NoWrap
        focus: true
        Component.onCompleted: { forceActiveFocus(); selectAll(); }
        onTextChanged: if (text !== UnitConverter.query) UnitConverter.convert(text)
        Keys.onReturnPressed: if (tool.hasResult) tool.copy(tool.res.main)
        Keys.onEnterPressed: if (tool.hasResult) tool.copy(tool.res.main)
        Keys.onEscapePressed: host.menuOpen = false
    }

    Rectangle {
        visible: UnitConverter.query.trim() !== "" && (UnitConverter.result !== null || UnitConverter.busy)
        Layout.fillWidth: true
        implicitHeight: answerCol.implicitHeight + 24
        radius: Appearance.rounding.small
        color: Appearance.colors.colLayer2

        ColumnLayout {
            id: answerCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 12
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                StyledText {
                    Layout.fillWidth: true
                    text: tool.hasResult ? (tool.kindNames[tool.res.kind] ?? "Result") : (tool.res && !tool.res.ok ? "No conversion" : "Converting...")
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                }
                MaterialLoadingIndicator {
                    implicitSize: 18
                    loading: UnitConverter.busy
                    visible: UnitConverter.busy
                }
                StyledText {
                    visible: UnitConverter.slow
                    text: "Waiting for the converter..."
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                TextEdit {
                    Layout.fillWidth: true
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.Wrap
                    opacity: UnitConverter.busy ? 0.6 : 1
                    text: tool.hasResult ? tool.res.main : (tool.res && !tool.res.ok ? tool.res.error : "")
                    color: tool.res && !tool.res.ok ? Appearance.colors.colError : Appearance.colors.colOnLayer2
                    selectionColor: Appearance.colors.colSecondaryContainer
                    selectedTextColor: Appearance.colors.colOnSecondaryContainer
                    font.family: Appearance.font.family.main
                    font.pixelSize: tool.hasResult ? Appearance.font.pixelSize.huge * 1.3 : Appearance.font.pixelSize.normal
                }
                RippleButtonWithIcon {
                    visible: tool.hasResult
                    materialIcon: tool.copied !== "" && tool.copied === tool.res?.main ? "check" : "content_copy"
                    mainText: tool.copied !== "" && tool.copied === tool.res?.main ? "Copied" : "Copy"
                    onClicked: tool.copy(tool.res.main)
                }
            }

            Repeater {
                model: tool.hasResult ? tool.res.related : []
                delegate: RippleButton {
                    id: rel
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 32
                    buttonRadius: Appearance.rounding.verysmall
                    colBackground: Appearance.colors.colLayer2
                    colBackgroundHover: Appearance.colors.colLayer2Hover
                    onClicked: tool.setTarget(modelData.unit)
                    StyledToolTip {
                        text: "Convert to " + rel.modelData.unit
                    }
                    contentItem: RowLayout {
                        spacing: 6
                        StyledText {
                            Layout.fillWidth: true
                            Layout.leftMargin: 4
                            text: rel.modelData.text
                            elide: Text.ElideRight
                            opacity: UnitConverter.busy ? 0.6 : 1
                            color: Appearance.colors.colOnLayer2
                        }
                        RippleButton {
                            implicitWidth: 28
                            implicitHeight: 28
                            buttonRadius: 14
                            colBackground: "transparent"
                            onClicked: tool.copy(rel.modelData.text)
                            contentItem: MaterialSymbol {
                                text: tool.copied === rel.modelData.text ? "check" : "content_copy"
                                iconSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                color: Appearance.colors.colSubtext
                            }
                        }
                    }
                }
            }

            StyledText {
                visible: tool.hasResult && tool.res.kind === "currency" && UnitConverter.rates !== ""
                text: "ECB rates of " + UnitConverter.rates
                font.pixelSize: Appearance.font.pixelSize.smaller
                color: Appearance.colors.colSubtext
            }
        }
    }

    StyledText {
        visible: UnitConverter.query.trim() === ""
        text: "Try"
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
    }

    Flow {
        visible: UnitConverter.query.trim() === ""
        Layout.fillWidth: true
        spacing: 6
        Repeater {
            model: tool.examples
            delegate: RippleButton {
                id: chip
                required property var modelData
                implicitHeight: 28
                implicitWidth: chipText.implicitWidth + 20
                buttonRadius: 14
                colBackground: Appearance.colors.colLayer2
                onClicked: {
                    input.text = modelData;
                    input.forceActiveFocus();
                }
                contentItem: StyledText {
                    id: chipText
                    text: chip.modelData
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
    }
}
