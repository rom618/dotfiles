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

    function formatBytes(n, suffix) {
        const units = ["B", "KB", "MB", "GB", "TB", "PB"];
        let i = 0;
        while (n >= 1000 && i < units.length - 1) {
            n /= 1000;
            i++;
        }
        return (i === 0 ? Math.round(n) : n.toFixed(1)) + " " + units[i] + suffix;
    }

    function formatHealth(h) {
        if (h.health === "good")
            return h.worn === null ? Translation.tr("Good") : Translation.tr("Good · %1% worn").arg(h.worn);
        return (h.health === "failing" ? Translation.tr("Failing") : Translation.tr("Warning")) + " · " + h.problems.join(", ");
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
                label: ResourceUsage.diskKind || "Disk"
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

        Column {
            anchors.top: parent.top
            spacing: 8
            visible: ResourceUsage.diskDevice !== ""

            StyledPopupHeaderRow {
                opacity: 0
                icon: "hard_drive"
                label: ""
            }
            Column {
                spacing: 4
                StyledPopupValueRow {
                    visible: ResourceUsage.diskHealth !== null
                    icon: "health_and_safety"
                    label: Translation.tr("Health:")
                    value: ResourceUsage.diskHealth ? root.formatHealth(ResourceUsage.diskHealth) : ""
                    valueColor: ResourceUsage.diskHealth?.health === "good" ? Appearance.colors.colOnSurfaceVariant : Appearance.colors.colError
                }
                StyledPopupValueRow {
                    visible: ResourceUsage.diskHealth !== null
                    icon: "edit_note"
                    label: Translation.tr("Written:")
                    value: ResourceUsage.diskHealth ? (ResourceUsage.diskHealth.written === null ? "" : root.formatBytes(ResourceUsage.diskHealth.written, "") + " · ") + Translation.tr("%1 h on").arg(ResourceUsage.diskHealth.hours.toLocaleString(Qt.locale("en_US"), "f", 0)) : ""
                }
                StyledPopupValueRow {
                    visible: ResourceUsage.diskDevice !== ""
                    icon: "swap_vert"
                    label: Translation.tr("I/O:")
                    value: "R " + root.formatBytes(ResourceUsage.diskReadRate, "/s") + " · W " + root.formatBytes(ResourceUsage.diskWriteRate, "/s")
                }
                StyledPopupValueRow {
                    visible: ResourceUsage.diskDevice !== ""
                    icon: "speed"
                    label: Translation.tr("Busy:")
                    value: Math.round(ResourceUsage.diskBusy * 100) + "%"
                }
            }
        }

    }
}
