import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions
import qs.services

ColumnLayout {
    id: tool
    required property var host
    spacing: 10

    readonly property string script: Quickshell.shellPath("scripts/tools/colors.py")
    readonly property string filePath: FileUtils.trimFileProtocol(Directories.genericCache) + "/quickshell/colors.json"
    property var colorData: host.store.colors ?? { current: "", history: [] }
    readonly property string hex: colorData.current ?? ""
    readonly property var rgb: hexToRgb(hex)
    property string copied: ""
    property string inputError: ""

    function hexToRgb(h) {
        const m = /^#?([0-9a-fA-F]{6})$/.exec(h || "");
        if (!m)
            return null;
        const n = parseInt(m[1], 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }

    function toHex(r, g, b) {
        return "#" + [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("").toUpperCase();
    }

    function hsl(c) {
        const r = c[0] / 255, g = c[1] / 255, b = c[2] / 255;
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
        const l = (mx + mn) / 2;
        let h = 0, s = 0;
        if (mx !== mn) {
            const d = mx - mn;
            s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
            if (mx === r)
                h = (g - b) / d + (g < b ? 6 : 0);
            else if (mx === g)
                h = (b - r) / d + 2;
            else
                h = (r - g) / d + 4;
            h *= 60;
        }
        return [Math.round(h), Math.round(s * 100), Math.round(l * 100)];
    }

    function hslToRgb(h, s, l) {
        s /= 100;
        l /= 100;
        const k = n => (n + h / 30) % 12;
        const a = s * Math.min(l, 1 - l);
        const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
        return [f(0) * 255, f(8) * 255, f(4) * 255];
    }

    function oklch(c) {
        const lin = v => {
            v /= 255;
            return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        };
        const r = lin(c[0]), g = lin(c[1]), b = lin(c[2]);
        const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
        const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
        const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
        const L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s;
        const A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s;
        const B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s;
        const C = Math.sqrt(A * A + B * B);
        let H = Math.atan2(B, A) * 180 / Math.PI;
        if (H < 0)
            H += 360;
        return [L * 100, C, C < 0.0005 ? 0 : H];
    }

    function luminance(c) {
        return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255;
    }

    function parseColor(t) {
        t = (t || "").trim();
        let m = /^#?([0-9a-fA-F]{3})$/.exec(t);
        if (m)
            return "#" + m[1].split("").map(x => x + x).join("").toUpperCase();
        m = /^(?:#|0x)?([0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?$/.exec(t);
        if (m)
            return "#" + m[1].toUpperCase();
        m = /^rgba?\(?\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/i.exec(t);
        if (m)
            return toHex(+m[1], +m[2], +m[3]);
        m = /^hsla?\(?\s*(\d+(?:\.\d+)?)(?:deg)?[\s,]+(\d+(?:\.\d+)?)%?[\s,]+(\d+(?:\.\d+)?)%?/i.exec(t);
        if (m) {
            const c = hslToRgb(+m[1], +m[2], +m[3]);
            return toHex(c[0], c[1], c[2]);
        }
        return "";
    }

    readonly property var formats: {
        if (!rgb)
            return [];
        const h = hsl(rgb), o = oklch(rgb);
        const ok = `oklch(${o[0].toFixed(1)}% ${o[1].toFixed(4)} ${o[2].toFixed(1)})`;
        return [
            { name: "HEX", value: hex },
            { name: "RGB", value: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})` },
            { name: "HSL", value: `hsl(${h[0]}, ${h[1]}%, ${h[2]}%)` },
            { name: "OKLCH", value: ok }
        ];
    }

    readonly property var copyAs: {
        if (!rgb)
            return [];
        return [
            { name: "hex no #", value: hex.slice(1) },
            { name: "lowercase", value: hex.toLowerCase() },
            { name: "0xRRGGBB", value: "0x" + hex.slice(1) },
            { name: "rgb 0-1", value: rgb.map(v => (v / 255).toFixed(3)).join(", ") },
            { name: "r g b", value: rgb.join(" ") },
            { name: "Qt.rgba", value: `Qt.rgba(${rgb.map(v => (v / 255).toFixed(3)).join(", ")}, 1)` }
        ];
    }

    function setData(d) {
        host.store.colors = d;
        tool.colorData = d;
        file.setText(JSON.stringify(d));
    }

    function show(c) {
        const hist = [c].concat((colorData.history ?? []).filter(x => x !== c)).slice(0, 16);
        setData({ current: c, history: hist });
    }

    function remove(c) {
        const hist = (colorData.history ?? []).filter(x => x !== c);
        setData({ current: colorData.current === c ? (hist[0] ?? "") : colorData.current, history: hist });
    }

    function copy(v) {
        Quickshell.execDetached(["wl-copy", "--", v]);
        tool.copied = v;
        copiedTimer.restart();
    }

    function pick() {
        host.menuOpen = false;
        Quickshell.execDetached(["python3", tool.script, "--pick"]);
    }

    function submit(t) {
        const c = parseColor(t);
        if (c === "") {
            tool.inputError = t.trim() === "" ? "" : "Type a color like #3A86FF, rgb(58, 134, 255) or hsl(217, 100%, 61%)";
            return;
        }
        tool.inputError = "";
        show(c);
        input.text = "";
    }

    Timer {
        id: copiedTimer
        interval: 1500
        onTriggered: tool.copied = ""
    }

    FileView {
        id: file
        path: tool.filePath
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                const d = JSON.parse(text());
                if (d && Array.isArray(d.history)) {
                    host.store.colors = d;
                    tool.colorData = d;
                }
            } catch (e) {}
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        MaterialTextField {
            id: input
            Layout.fillWidth: true
            placeholderText: "Paste a color: #3A86FF, rgb(...), hsl(...)"
            wrapMode: TextEdit.NoWrap
            focus: true
            Component.onCompleted: forceActiveFocus()
            onTextChanged: tool.inputError = ""
            Keys.onReturnPressed: tool.submit(text)
            Keys.onEnterPressed: tool.submit(text)
            Keys.onEscapePressed: host.menuOpen = false
        }
        RippleButtonWithIcon {
            implicitHeight: 44
            materialIcon: "colorize"
            mainText: "Pick from screen"
            colBackground: Appearance.colors.colPrimaryContainer
            colBackgroundHover: Appearance.colors.colPrimaryContainerHover
            colRipple: Appearance.colors.colPrimaryContainerActive
            onClicked: tool.pick()
        }
    }

    StyledText {
        visible: tool.inputError !== ""
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        text: tool.inputError
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colError
    }

    Rectangle {
        visible: tool.rgb !== null
        Layout.fillWidth: true
        implicitHeight: colorRow.implicitHeight + 24
        radius: Appearance.rounding.small
        color: Appearance.colors.colLayer2

        RowLayout {
            id: colorRow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 12
            spacing: 12

            Rectangle {
                Layout.alignment: Qt.AlignTop
                implicitWidth: 112
                implicitHeight: 112
                radius: Appearance.rounding.normal
                color: tool.hex !== "" ? tool.hex : "transparent"
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant
                StyledText {
                    anchors.centerIn: parent
                    text: tool.hex
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: tool.rgb && tool.luminance(tool.rgb) > 0.55 ? "#000000" : "#FFFFFF"
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Repeater {
                    model: tool.formats
                    delegate: RippleButton {
                        id: fmt
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 28
                        buttonRadius: Appearance.rounding.verysmall
                        colBackground: Appearance.colors.colLayer2
                        colBackgroundHover: Appearance.colors.colLayer2Hover
                        onClicked: tool.copy(modelData.value)
                        contentItem: RowLayout {
                            spacing: 8
                            StyledText {
                                Layout.preferredWidth: 52
                                Layout.leftMargin: 4
                                text: fmt.modelData.name
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: Appearance.colors.colSubtext
                            }
                            StyledText {
                                Layout.fillWidth: true
                                text: fmt.modelData.value
                                elide: Text.ElideRight
                                font.family: Appearance.font.family.monospace
                                font.pixelSize: Appearance.font.pixelSize.small
                                color: Appearance.colors.colOnLayer2
                            }
                            MaterialSymbol {
                                Layout.rightMargin: 4
                                text: tool.copied === fmt.modelData.value ? "check" : "content_copy"
                                iconSize: 16
                                color: Appearance.colors.colSubtext
                            }
                        }
                    }
                }
            }
        }
    }

    Flow {
        visible: tool.rgb !== null
        Layout.fillWidth: true
        spacing: 6
        StyledText {
            height: 28
            verticalAlignment: Text.AlignVCenter
            text: "Copy as"
            font.pixelSize: Appearance.font.pixelSize.small
            color: Appearance.colors.colSubtext
        }
        Repeater {
            model: tool.copyAs
            delegate: RippleButton {
                id: chip
                required property var modelData
                implicitHeight: 28
                implicitWidth: chipText.implicitWidth + 20
                buttonRadius: 14
                colBackground: Appearance.colors.colLayer2
                onClicked: tool.copy(modelData.value)
                StyledToolTip {
                    text: chip.modelData.value
                }
                contentItem: StyledText {
                    id: chipText
                    text: tool.copied === chip.modelData.value ? "Copied" : chip.modelData.name
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
    }

    StyledText {
        visible: tool.rgb === null
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.bottomMargin: 6
        horizontalAlignment: Text.AlignHCenter
        text: "Pick a color from the screen or paste one"
        color: Appearance.colors.colSubtext
    }

    StyledText {
        visible: (tool.colorData.history ?? []).length > 0
        text: "Recent"
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
    }

    Flow {
        visible: (tool.colorData.history ?? []).length > 0
        Layout.fillWidth: true
        spacing: 6
        Repeater {
            model: tool.colorData.history ?? []
            delegate: Item {
                id: sw
                required property string modelData
                width: 48
                height: 32
                RippleButton {
                    anchors.fill: parent
                    buttonRadius: Appearance.rounding.verysmall
                    colBackground: sw.modelData
                    colBackgroundHover: sw.modelData
                    colRipple: tool.luminance(tool.hexToRgb(sw.modelData) ?? [0, 0, 0]) > 0.55 ? "#40000000" : "#40FFFFFF"
                    onClicked: tool.show(sw.modelData)
                    altAction: () => tool.remove(sw.modelData)
                    StyledToolTip {
                        text: sw.modelData + "  (right click removes)"
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    radius: Appearance.rounding.verysmall
                    border.width: sw.modelData === tool.hex ? 2 : 1
                    border.color: sw.modelData === tool.hex ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                }
                RippleButton {
                    visible: hover.hovered
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: -4
                    implicitWidth: 18
                    implicitHeight: 18
                    buttonRadius: 9
                    colBackground: Appearance.colors.colLayer3
                    colBackgroundHover: Appearance.colors.colLayer3Hover
                    onClicked: tool.remove(sw.modelData)
                    contentItem: MaterialSymbol {
                        text: "close"
                        iconSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        color: Appearance.colors.colOnLayer2
                    }
                }
                HoverHandler {
                    id: hover
                }
            }
        }
    }
}
