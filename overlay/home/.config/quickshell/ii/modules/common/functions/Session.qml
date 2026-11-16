pragma Singleton
import Quickshell
import qs.services
import qs.modules.common

Singleton {
    id: root

    // Chrome needs time after SIGTERM to record a clean exit, or it offers "Restore pages?" next login
    function closeAllWindowsThen(command) {
        const pids = HyprlandData.windowList.map(w => w.pid).join(" ");
        Quickshell.execDetached(["bash", "-c", `systemctl --user stop hypr-session-save.timer; kill ${pids}; for i in $(seq 100); do alive=; for p in ${pids}; do kill -0 $p 2>/dev/null && alive=1; done; [ -z "$alive" ] && break; sleep 0.1; done; ${command}`]);
    }

    function changePassword() {
        Quickshell.execDetached(["bash", "-c", `${Config.options.apps.changePassword}`]);
    }

    function lock() {
        Quickshell.execDetached(["loginctl", "lock-session"]);
    }

    function suspend() {
        Quickshell.execDetached(["bash", "-c", "systemctl suspend || loginctl suspend"]);
    }

    function logout() {
        closeAllWindowsThen("pkill -i Hyprland");
    }

    function launchTaskManager() {
        Quickshell.execDetached(["bash", "-c", `${Config.options.apps.taskManager}`]);
    }

    function hibernate() {
        Quickshell.execDetached(["bash", "-c", `systemctl hibernate || loginctl hibernate`]);
    }

    function poweroff() {
        closeAllWindowsThen("systemctl poweroff || loginctl poweroff");
    }

    function reboot() {
        closeAllWindowsThen("reboot || loginctl reboot");
    }

    function rebootToFirmware() {
        closeAllWindowsThen("systemctl reboot --firmware-setup || loginctl reboot --firmware-setup");
    }
}
