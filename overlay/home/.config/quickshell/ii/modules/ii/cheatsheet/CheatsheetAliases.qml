pragma ComponentBehavior: Bound

import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import Quickshell

Item {
    id: root
    property real padding: 4
    implicitWidth: QsWindow?.window?.screen.width * 0.7 ?? 0
    implicitHeight: QsWindow?.window?.screen.height * 0.7 ?? 0

    StyledFlickable {
        id: flickable
        clip: true
        anchors.fill: parent
        anchors.margins: Appearance.rounding.small
        contentHeight: column.implicitHeight
        contentWidth: width

        Column {
            id: column
            width: flickable.width
            spacing: 4

            Repeater {
                model: FishAliases.aliases
                delegate: RowLayout {
                    id: aliasRow
                    required property var modelData
                    width: column.width
                    spacing: 16

                    KeyboardKey {
                        Layout.alignment: Qt.AlignVCenter
                        key: aliasRow.modelData.name
                    }
                    StyledText {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        font.family: Appearance.font.family.monospace
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.colors.colOnSurfaceVariant
                        elide: Text.ElideRight
                        text: aliasRow.modelData.command
                    }
                }
            }

            StyledText {
                visible: FishAliases.functions.length > 0
                topPadding: 8
                font.pixelSize: Appearance.font.pixelSize.title
                text: Translation.tr("Commands")
            }

            Repeater {
                model: FishAliases.functions
                delegate: RowLayout {
                    id: functionRow
                    required property var modelData
                    width: column.width
                    spacing: 16

                    KeyboardKey {
                        Layout.alignment: Qt.AlignVCenter
                        keyColor: Appearance.m3colors.m3secondaryContainer
                        key: functionRow.modelData.name
                    }
                    StyledText {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.colors.colOnSurfaceVariant
                        elide: Text.ElideRight
                        text: functionRow.modelData.command
                    }
                }
            }
        }
    }

    ScrollEdgeFade {
        target: flickable
        vertical: false
        color: Appearance.colors.colLayer0Base
    }
}
