pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io

/**
 * Simple polled resource usage service with RAM, Swap, and CPU usage.
 */
Singleton {
    id: root
	property real memoryTotal: 1
	property real memoryFree: 0
	property real memoryUsed: memoryTotal - memoryFree
    property real memoryUsedPercentage: memoryUsed / memoryTotal
    property real swapTotal: 1
	property real swapFree: 0
	property real swapUsed: swapTotal - swapFree
    property real swapUsedPercentage: swapTotal > 0 ? (swapUsed / swapTotal) : 0
    property real cpuUsage: 0
    property var previousCpuStats

    property bool gpuAvailable: false
    property real gpuUsage: 0

    property real diskTotal: 1
	property real diskFree: 0
	property real diskUsed: diskTotal - diskFree
    property real diskUsedPercentage: diskUsed / diskTotal

    property bool homeIsSeparateDisk: false
    property real homeDiskTotal: 1
	property real homeDiskFree: 0
	property real homeDiskUsed: homeDiskTotal - homeDiskFree
    property real homeDiskUsedPercentage: homeDiskUsed / homeDiskTotal

    property real combinedDiskTotal: diskTotal + (homeIsSeparateDisk ? homeDiskTotal : 0)
    property real combinedDiskFree: diskFree + (homeIsSeparateDisk ? homeDiskFree : 0)
    property real combinedDiskUsed: combinedDiskTotal - combinedDiskFree
    property real combinedDiskUsedPercentage: combinedDiskUsed / combinedDiskTotal

    property string diskDevice: ""
    property real diskReadRate: 0
    property real diskWriteRate: 0
    property real diskBusy: 0
    property var previousDiskStats
    property var diskHealth: null
    readonly property string diskKind: ({ "0": "SSD", "1": "HDD" })[fileDiskRotational.text().trim()] ?? ""

    property string maxAvailableMemoryString: kbToGbString(ResourceUsage.memoryTotal)
    property string maxAvailableSwapString: kbToGbString(ResourceUsage.swapTotal)
    property string maxAvailableCpuString: "--"

    readonly property int historyLength: Config?.options.resources.historyLength ?? 60
    property list<real> cpuUsageHistory: []
    property list<real> memoryUsageHistory: []
    property list<real> swapUsageHistory: []

    function kbToGbString(kb) {
        // Dividing by 1024*1024 (binary) makes this GiB, not GB - label it as such
        return (kb / (1024 * 1024)).toFixed(1) + " GiB";
    }

    function updateMemoryUsageHistory() {
        memoryUsageHistory = [...memoryUsageHistory, memoryUsedPercentage]
        if (memoryUsageHistory.length > historyLength) {
            memoryUsageHistory.shift()
        }
    }
    function updateSwapUsageHistory() {
        swapUsageHistory = [...swapUsageHistory, swapUsedPercentage]
        if (swapUsageHistory.length > historyLength) {
            swapUsageHistory.shift()
        }
    }
    function updateCpuUsageHistory() {
        cpuUsageHistory = [...cpuUsageHistory, cpuUsage]
        if (cpuUsageHistory.length > historyLength) {
            cpuUsageHistory.shift()
        }
    }
    function updateHistories() {
        updateMemoryUsageHistory()
        updateSwapUsageHistory()
        updateCpuUsageHistory()
    }

	Timer {
		interval: 1
        running: true 
        repeat: true
		onTriggered: {
            // Reload files
            fileMeminfo.reload()
            fileStat.reload()

            // Parse memory and swap usage
            const textMeminfo = fileMeminfo.text()
            memoryTotal = Number(textMeminfo.match(/MemTotal: *(\d+)/)?.[1] ?? 1)
            memoryFree = Number(textMeminfo.match(/MemAvailable: *(\d+)/)?.[1] ?? 0)
            swapTotal = Number(textMeminfo.match(/SwapTotal: *(\d+)/)?.[1] ?? 1)
            swapFree = Number(textMeminfo.match(/SwapFree: *(\d+)/)?.[1] ?? 0)

            // Parse CPU usage
            const textStat = fileStat.text()
            const cpuLine = textStat.match(/^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)/)
            if (cpuLine) {
                const stats = cpuLine.slice(1).map(Number)
                const total = stats.reduce((a, b) => a + b, 0)
                const idle = stats[3]

                if (previousCpuStats) {
                    const totalDiff = total - previousCpuStats.total
                    const idleDiff = idle - previousCpuStats.idle
                    cpuUsage = totalDiff > 0 ? (1 - idleDiff / totalDiff) : 0
                }

                previousCpuStats = { total, idle }
            }

            root.updateDiskIo()
            root.updateHistories()
            root.updateSensors()
            interval = Config.options?.resources?.updateInterval ?? 3000
        }
	}

    property var sensorPaths: ({})
    property real cpuTemp: NaN
    property real cpuHottestCore: NaN
    property real diskTemp: NaN
    property real cpuFan: NaN
    property real gpuFan: NaN

    function sensorValue(view, scale) {
        if (!view.path)
            return NaN;
        view.reload();
        const v = parseFloat(view.text());
        return isNaN(v) ? NaN : v / scale;
    }

    function updateDiskIo() {
        if (!root.diskDevice)
            return;
        fileDiskStat.reload();
        const f = fileDiskStat.text().trim().split(/\s+/).map(Number);
        const now = Date.now();
        const stats = { time: now, read: f[2] * 512, written: f[6] * 512, busy: f[9] };
        const prev = root.previousDiskStats;
        if (prev) {
            const dt = (now - prev.time) / 1000;
            root.diskReadRate = (stats.read - prev.read) / dt;
            root.diskWriteRate = (stats.written - prev.written) / dt;
            root.diskBusy = Math.min(1, (stats.busy - prev.busy) / (dt * 1000));
        }
        root.previousDiskStats = stats;
    }

    function updateSensors() {
        root.cpuTemp = sensorValue(fileCpuTemp, 1000);
        root.diskTemp = sensorValue(fileDiskTemp, 1000);
        root.cpuFan = sensorValue(fileCpuFan, 1);
        root.gpuFan = sensorValue(fileGpuFan, 1);
        let hottest = NaN;
        for (let i = 0; i < coreViews.count; i++) {
            const v = sensorValue(coreViews.objectAt(i), 1000);
            if (!isNaN(v) && (isNaN(hottest) || v > hottest))
                hottest = v;
        }
        root.cpuHottestCore = hottest;
    }

    Process {
        id: sensorScanProc
        running: true
        command: ["bash", "-c", "for h in /sys/class/hwmon/hwmon*; do n=$(cat $h/name 2>/dev/null); for l in $h/temp*_label $h/fan*_label; do [ -f \"$l\" ] && printf '%s\\t%s\\t%s\\n' \"$n\" \"$(cat $l)\" \"${l%_label}_input\"; done; [ -f $h/temp1_input ] && printf '%s\\t\\t%s\\n' \"$n\" \"$h/temp1_input\"; done"]
        stdout: StdioCollector {
            onStreamFinished: {
                const found = { cores: [] };
                for (const line of text.split("\n")) {
                    const [name, label, path] = line.split("\t");
                    if (!path)
                        continue;
                    if (name === "coretemp" && label === "Package id 0")
                        found.cpu = path;
                    else if (name === "coretemp" && label.startsWith("Core "))
                        found.cores.push(path);
                    else if (name === "k10temp" && label === "Tctl" && !found.cpu)
                        found.cpu = path;
                    else if (name === "nvme" && (label === "Composite" || label === "") && !found.disk)
                        found.disk = path;
                    else if (label === "cpu_fan")
                        found.cpuFan = path;
                    else if (label === "gpu_fan")
                        found.gpuFan = path;
                }
                root.sensorPaths = found;
            }
        }
    }

    FileView { id: fileCpuTemp; path: root.sensorPaths.cpu ?? ""; printErrors: false }
    FileView { id: fileDiskTemp; path: root.sensorPaths.disk ?? ""; printErrors: false }
    FileView { id: fileCpuFan; path: root.sensorPaths.cpuFan ?? ""; printErrors: false }
    FileView { id: fileGpuFan; path: root.sensorPaths.gpuFan ?? ""; printErrors: false }
    Instantiator {
        id: coreViews
        model: root.sensorPaths.cores ?? []
        delegate: FileView {
            required property string modelData
            path: modelData
            printErrors: false
        }
    }

	FileView { id: fileMeminfo; path: "/proc/meminfo" }
    FileView { id: fileDiskStat; path: root.diskDevice ? `/sys/block/${root.diskDevice}/stat` : "" }
    FileView { id: fileDiskRotational; path: root.diskDevice ? `/sys/block/${root.diskDevice}/queue/rotational` : ""; blockLoading: true }

    Process {
        id: diskDeviceProc
        running: true
        command: ["bash", "-c", "lsblk -rsno NAME,TYPE \"$(findmnt -nvo SOURCE /)\" | awk '$2==\"disk\"{print $1; exit}'"]
        stdout: StdioCollector {
            onStreamFinished: root.diskDevice = text.trim()
        }
    }

    onDiskDeviceChanged: diskHealthProc.exec([Quickshell.shellPath("scripts/disk/disk-health.py"), root.diskDevice])

    Process {
        id: diskHealthProc
        stdout: StdioCollector {
            onStreamFinished: root.diskHealth = JSON.parse(text)
        }
    }
    FileView { id: fileStat; path: "/proc/stat" }

    Timer {
        interval: Config.options?.resources?.diskUpdateInterval ?? 60000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            diskUsageProc.running = true;
            if (root.diskDevice)
                diskHealthProc.exec([Quickshell.shellPath("scripts/disk/disk-health.py"), root.diskDevice]);
        }
    }

    Process {
        id: diskUsageProc
        command: ["bash", "-c", "df -k --output=target,size,avail / \"$HOME\" | tail -n +2"]
        stdout: StdioCollector {
            onStreamFinished: {
                const lines = text.trim().split("\n").filter(l => l.length > 0)
                if (lines.length === 0) return
                const rootParts = lines[0].trim().split(/\s+/)
                if (rootParts.length === 3) {
                    root.diskTotal = Number(rootParts[1])
                    root.diskFree = Number(rootParts[2])
                }
                if (lines.length > 1) {
                    const homeParts = lines[1].trim().split(/\s+/)
                    root.homeIsSeparateDisk = homeParts[0] !== rootParts[0]
                    if (root.homeIsSeparateDisk && homeParts.length === 3) {
                        root.homeDiskTotal = Number(homeParts[1])
                        root.homeDiskFree = Number(homeParts[2])
                    }
                } else {
                    root.homeIsSeparateDisk = false
                }
            }
        }
    }

    Process {
        id: findCpuMaxFreqProc
        environment: ({
            LANG: "C",
            LC_ALL: "C"
        })
        command: ["bash", "-c", "lscpu | grep 'CPU max MHz' | awk '{print $4}'"]
        running: true
        stdout: StdioCollector {
            id: outputCollector
            onStreamFinished: {
                root.maxAvailableCpuString = (parseFloat(outputCollector.text) / 1000).toFixed(0) + " GHz"
            }
        }
    }

    readonly property string gpuScriptPath: `${FileUtils.trimFileProtocol(Directories.home)}/.config/hypr/custom/scripts/gpu-usage.py`

    Process {
        id: checkGpuToolProc
        command: ["bash", "-c", `command -v python3 >/dev/null 2>&1 && test -f "${root.gpuScriptPath}"`]
        running: true
        onExited: (exitCode, exitStatus) => {
            root.gpuAvailable = (exitCode === 0)
        }
    }

    Timer {
        interval: Config.options?.resources?.updateInterval ?? 3000
        running: root.gpuAvailable
        repeat: true
        triggeredOnStart: true
        onTriggered: gpuUsageProc.running = true
    }

    Process {
        id: gpuUsageProc
        // Reads /proc/*/fdinfo drm-cycles-rcs counters (xe/amdgpu), diffed
        // over a short delay - see config/hypr/custom/scripts/gpu-usage.py. Verified live
        // against this machine's Intel Xe iGPU.
        command: ["python3", root.gpuScriptPath]
        stdout: StdioCollector {
            onStreamFinished: {
                const value = parseFloat(text)
                root.gpuUsage = isNaN(value) ? 0 : (value / 100)
            }
        }
    }
}
