import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts

StyledPopup {
    id: root

    Column {
        anchors.centerIn: parent
        spacing: 8

        StyledPopupHeaderRow {
            icon: "deployed_code"
            label: "Docker"
        }

        StyledText {
            visible: Docker.count === 0
            color: Appearance.colors.colOnSurfaceVariant
            text: Translation.tr("No running containers")
        }

        Column {
            spacing: 4
            Repeater {
                model: Docker.containers
                delegate: StyledPopupValueRow {
                    required property var modelData
                    icon: "package_2"
                    label: modelData.Names ?? ""
                    value: modelData.Status ?? ""
                }
            }
        }
    }
}
