import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts

StyledPopup {
    id: root

    // Dividing by 1024*1024 (binary) makes this GiB, not GB - label it as such
    function formatKB(kb) {
        return (kb / (1024 * 1024)).toFixed(1) + " GiB";
    }

    function formatTemp(c) {
        return Math.round(c) + String.fromCharCode(176) + "C";
    }

    Row {
        anchors.centerIn: parent
        spacing: 12

        Column {
            anchors.top: parent.top
            spacing: 8

            StyledPopupHeaderRow {
                icon: "memory"
                label: "RAM"
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    icon: "clock_loader_60"
                    label: Translation.tr("Used:")
                    value: root.formatKB(ResourceUsage.memoryUsed)
                }
                StyledPopupValueRow {
                    icon: "check_circle"
                    label: Translation.tr("Free:")
                    value: root.formatKB(ResourceUsage.memoryFree)
                }
                StyledPopupValueRow {
                    icon: "empty_dashboard"
                    label: Translation.tr("Total:")
                    value: root.formatKB(ResourceUsage.memoryTotal)
                }
            }
        }

        Column {
            visible: ResourceUsage.swapTotal > 0
            anchors.top: parent.top
            spacing: 8

            StyledPopupHeaderRow {
                icon: "swap_horiz"
                label: "Swap"
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    icon: "clock_loader_60"
                    label: Translation.tr("Used:")
                    value: root.formatKB(ResourceUsage.swapUsed)
                }
                StyledPopupValueRow {
                    icon: "check_circle"
                    label: Translation.tr("Free:")
                    value: root.formatKB(ResourceUsage.swapFree)
                }
                StyledPopupValueRow {
                    icon: "empty_dashboard"
                    label: Translation.tr("Total:")
                    value: root.formatKB(ResourceUsage.swapTotal)
                }
            }
        }

        Column {
            anchors.top: parent.top
            spacing: 8

            StyledPopupHeaderRow {
                icon: "planner_review"
                label: "CPU"
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    icon: "bolt"
                    label: Translation.tr("Load:")
                    value: `${Math.round(ResourceUsage.cpuUsage * 100)}%`
                }
                StyledPopupValueRow {
                    visible: !isNaN(ResourceUsage.cpuTemp)
                    icon: "thermostat"
                    label: Translation.tr("Temp:")
                    value: root.formatTemp(ResourceUsage.cpuTemp)
                }
                StyledPopupValueRow {
                    visible: !isNaN(ResourceUsage.cpuHottestCore)
                    icon: "local_fire_department"
                    label: Translation.tr("Hottest core:")
                    value: root.formatTemp(ResourceUsage.cpuHottestCore)
                }
                StyledPopupValueRow {
                    visible: !isNaN(ResourceUsage.cpuFan)
                    icon: "mode_fan"
                    label: Translation.tr("Fan:")
                    value: `${Math.round(ResourceUsage.cpuFan)} RPM`
                }
            }
        }

        Column {
            visible: ResourceUsage.gpuAvailable
            anchors.top: parent.top
            spacing: 8

            StyledPopupHeaderRow {
                icon: "developer_board"
                label: "GPU"
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    icon: "bolt"
                    label: Translation.tr("Load:")
                    value: `${Math.round(ResourceUsage.gpuUsage * 100)}%`
                }
                StyledPopupValueRow {
                    visible: !isNaN(ResourceUsage.gpuFan)
                    icon: "mode_fan"
                    label: Translation.tr("Fan:")
                    value: `${Math.round(ResourceUsage.gpuFan)} RPM`
                }
            }
        }

        Column {
            anchors.top: parent.top
            spacing: 8

            StyledPopupHeaderRow {
                icon: "hard_drive"
                label: "Disk"
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    icon: "clock_loader_60"
                    label: Translation.tr("Used:")
                    value: root.formatKB(ResourceUsage.combinedDiskUsed)
                }
                StyledPopupValueRow {
                    icon: "check_circle"
                    label: Translation.tr("Free:")
                    value: root.formatKB(ResourceUsage.combinedDiskFree)
                }
                StyledPopupValueRow {
                    icon: "empty_dashboard"
                    label: Translation.tr("Total:")
                    value: root.formatKB(ResourceUsage.combinedDiskTotal)
                }
                StyledPopupValueRow {
                    visible: !isNaN(ResourceUsage.diskTemp)
                    icon: "thermostat"
                    label: Translation.tr("Temp:")
                    value: root.formatTemp(ResourceUsage.diskTemp)
                }
            }
        }

    }
}
