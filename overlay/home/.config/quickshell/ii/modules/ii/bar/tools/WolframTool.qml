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

    MaterialTextField {
        id: input
        Layout.fillWidth: true
        placeholderText: "Math, units, conversions, facts..."
        text: host.query
        wrapMode: TextEdit.NoWrap
        focus: true
        Component.onCompleted: { forceActiveFocus(); selectAll(); }
        Keys.onReturnPressed: host.ask(text)
        Keys.onEnterPressed: host.ask(text)
        Keys.onEscapePressed: host.menuOpen = false
    }

    RowLayout {
        visible: host.busy
        Layout.fillWidth: true
        spacing: 10
        MaterialLoadingIndicator {
            implicitSize: 28
            loading: host.busy
        }
        StyledText {
            text: host.slow ? "Still waiting for Wolfram Alpha..." : "Asking..."
            color: Appearance.colors.colSubtext
            Layout.fillWidth: true
        }
    }

    Rectangle {
        visible: !host.busy && host.result !== null
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

            TextEdit {
                Layout.fillWidth: true
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.Wrap
                text: host.result ? (host.result.ok ? (host.showingDecimal ? "\u2248 " + host.decimalText : host.result.answer) : host.result.error) : ""
                color: host.result && !host.result.ok ? Appearance.colors.colError : Appearance.colors.colOnLayer2
                selectionColor: Appearance.colors.colSecondaryContainer
                selectedTextColor: Appearance.colors.colOnSecondaryContainer
                font.family: Appearance.font.family.main
                font.pixelSize: host.result && host.result.ok ? Appearance.font.pixelSize.larger : Appearance.font.pixelSize.normal
            }

            Flickable {
                visible: !!host.result?.ok && (host.result?.detail ?? "") !== ""
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(detail.implicitHeight, 220)
                contentHeight: detail.implicitHeight
                clip: true
                TextEdit {
                    id: detail
                    width: parent.width
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.Wrap
                    text: host.result?.detail ?? ""
                    color: Appearance.colors.colSubtext
                    font.family: Appearance.font.family.main
                    font.pixelSize: Appearance.font.pixelSize.small
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                RippleButtonWithIcon {
                    visible: host.result?.ok ?? false
                    materialIcon: "content_copy"
                    mainText: "Copy"
                    onClicked: Quickshell.execDetached(["wl-copy", host.showingDecimal ? host.decimalText : host.result.answer])
                }
                Repeater {
                    model: host.exactAnswer ? [{ dec: false, name: "Exact" }, { dec: true, name: "Decimal" }] : []
                    delegate: RippleButton {
                        id: modeButton
                        required property var modelData
                        implicitHeight: 30
                        implicitWidth: modeText.implicitWidth + 24
                        buttonRadius: 15
                        toggled: host.preferDecimal === modelData.dec
                        colBackgroundToggled: Appearance.colors.colSecondaryContainer
                        onClicked: host.wantDecimal(modelData.dec)
                        contentItem: RowLayout {
                            spacing: 4
                            MaterialLoadingIndicator {
                                visible: modeButton.modelData.dec && host.decimalBusy
                                implicitSize: 16
                                loading: visible
                            }
                            StyledText {
                                id: modeText
                                text: modeButton.modelData.name
                                Layout.alignment: Qt.AlignHCenter
                                font.pixelSize: Appearance.font.pixelSize.small
                                color: modeButton.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer2
                            }
                        }
                    }
                }
                RippleButtonWithIcon {
                    visible: host.result?.retry ?? false
                    materialIcon: "refresh"
                    mainText: "Retry"
                    onClicked: host.ask(host.query)
                }
                Item { Layout.fillWidth: true }
                RippleButtonWithIcon {
                    materialIcon: "open_in_new"
                    mainText: "Full page"
                    onClicked: {
                        Quickshell.execDetached(["firefox", host.result.url]);
                        host.menuOpen = false;
                    }
                }
            }
        }
    }

    StyledText {
        visible: host.history.length > 0
        text: "Recent"
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
    }

    Flow {
        visible: host.history.length > 0
        Layout.fillWidth: true
        spacing: 6
        Repeater {
            model: host.history.slice(0, 8)
            delegate: RippleButton {
                id: chip
                required property var modelData
                implicitHeight: 28
                implicitWidth: Math.min(240, chipText.implicitWidth + 20)
                buttonRadius: 14
                colBackground: Appearance.colors.colLayer2
                onClicked: host.ask(modelData.query)
                contentItem: StyledText {
                    id: chipText
                    text: chip.modelData.query
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
    }
}
