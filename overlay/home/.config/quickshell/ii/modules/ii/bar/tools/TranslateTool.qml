import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.modules.common
import qs.modules.common.widgets

ColumnLayout {
    id: tool
    required property var host
    spacing: 10

    readonly property string script: Quickshell.shellPath("scripts/tools/translate.py")
    readonly property var langs: [
        { code: "en", name: "English" },
        { code: "fr", name: "French" },
        { code: "es", name: "Spanish" },
        { code: "ja", name: "Japanese" },
        { code: "zh", name: "Chinese" }
    ]
    property string target: "fr"
    property string query: ""
    property var result: null
    property var history: []
    property bool busy: false
    property bool slow: false
    property bool llmStage: false
    property bool waking: false
    property string llmName: "the AI model"
    property string copied: ""

    function langName(code) {
        const l = tool.langs.find(x => x.code === code);
        return l ? l.name : (code || "?");
    }

    function persist() {
        host.store.translate = { target: tool.target, query: tool.query, result: tool.result, history: tool.history };
    }

    function translate(q) {
        q = (q || "").trim();
        if (q === "")
            return;
        tool.query = q;
        input.text = q;
        tool.result = null;
        tool.busy = true;
        tool.slow = false;
        tool.llmStage = false;
        tool.waking = false;
        slowTimer.restart();
        wakeTimer.stop();
        proc.running = false;
        proc.command = ["python3", tool.script, "--to", tool.target, q];
        proc.running = true;
        tool.persist();
    }

    function setTarget(code) {
        if (tool.target === code)
            return;
        tool.target = code;
        tool.persist();
        if (tool.query !== "" && (tool.busy || tool.result !== null))
            tool.translate(tool.query);
    }

    function mainTranslation() {
        const r = tool.result;
        if (!r || !r.ok)
            return "";
        if (r.engine === "llm" || r.engine === "qwen")
            return r.translation;
        for (const e of r.entries ?? []) {
            if (e.main.length > 0)
                return e.main[0].text;
            if (e.less.length > 0)
                return e.less[0].text;
        }
        return "";
    }

    readonly property bool canSwap: !tool.busy && !!tool.result?.ok && tool.langs.some(l => l.code === tool.result.src) && tool.result.src !== tool.result.dst && tool.mainTranslation() !== ""

    function swap() {
        if (!tool.canSwap)
            return;
        const back = tool.result.src;
        const text = tool.mainTranslation();
        tool.target = back;
        tool.translate(text);
    }

    function copy(text) {
        if (!text)
            return;
        Quickshell.execDetached(["wl-copy", text]);
        tool.copied = text;
        copiedTimer.restart();
    }

    function openUrl(url) {
        if (!url)
            return;
        Quickshell.execDetached(["firefox", url]);
        host.menuOpen = false;
    }

    Component.onCompleted: {
        const s = host.store.translate;
        if (s) {
            tool.target = s.target ?? "fr";
            tool.query = s.query ?? "";
            tool.result = s.result ?? null;
            tool.history = s.history ?? [];
        }
        input.text = tool.query;
        input.forceActiveFocus();
        input.selectAll();
        stateProc.running = true;
    }

    Timer {
        id: slowTimer
        interval: 1000
        onTriggered: tool.slow = tool.busy
    }

    Timer {
        id: wakeTimer
        interval: 2000
        onTriggered: tool.waking = tool.busy && tool.llmStage
    }

    Timer {
        id: copiedTimer
        interval: 1400
        onTriggered: tool.copied = ""
    }

    Process {
        id: proc
        stdout: SplitParser {
            onRead: data => {
                let r = null;
                try {
                    r = JSON.parse(data);
                } catch (e) {
                    return;
                }
                if (r.query !== tool.query)
                    return;
                if (r.stage === "llm") {
                    tool.llmStage = true;
                    tool.llmName = r.name ?? "the AI model";
                    wakeTimer.restart();
                    return;
                }
                if (r.history)
                    tool.history = r.history;
                tool.result = r;
                tool.busy = false;
                tool.persist();
            }
        }
        onExited: (code, status) => {
            if (tool.busy) {
                tool.busy = false;
                tool.result = { ok: false, query: tool.query, error: "The translate tool stopped (" + code + ")", retry: true };
            }
        }
    }

    Process {
        id: stateProc
        command: ["python3", tool.script, "--state"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    const s = JSON.parse(data);
                    tool.history = s.history ?? [];
                    if (!host.store.translate && s.target)
                        tool.target = s.target;
                    tool.persist();
                } catch (e) {}
            }
        }
    }

    component Chip: RippleButton {
        id: chip
        property string label
        property bool small: false
        implicitHeight: small ? 26 : 30
        implicitWidth: Math.min(240, chipLabel.implicitWidth + 22)
        buttonRadius: implicitHeight / 2
        colBackground: Appearance.colors.colLayer2
        colBackgroundToggled: Appearance.colors.colSecondaryContainer
        contentItem: StyledText {
            id: chipLabel
            text: chip.label
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: Appearance.font.pixelSize.small
            color: chip.toggled ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer2
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        StyledText {
            text: "To"
            font.pixelSize: Appearance.font.pixelSize.small
            color: Appearance.colors.colSubtext
        }
        Repeater {
            model: tool.langs
            delegate: Chip {
                required property var modelData
                label: modelData.name
                toggled: tool.target === modelData.code
                onClicked: tool.setTarget(modelData.code)
            }
        }
        Item { Layout.fillWidth: true }
        RippleButton {
            implicitWidth: 30
            implicitHeight: 30
            buttonRadius: 15
            enabled: tool.canSwap
            opacity: enabled ? 1 : 0.4
            onClicked: tool.swap()
            StyledToolTip {
                text: "Swap: translate the result back"
            }
            contentItem: MaterialSymbol {
                text: "swap_horiz"
                iconSize: 18
                horizontalAlignment: Text.AlignHCenter
                color: Appearance.colors.colOnLayer1
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        MaterialTextField {
            id: input
            Layout.fillWidth: true
            placeholderText: "Word, phrase or sentence (any of the five languages)"
            focus: true
            Keys.onReturnPressed: tool.translate(text)
            Keys.onEnterPressed: tool.translate(text)
            Keys.onEscapePressed: host.menuOpen = false
        }
        RippleButton {
            implicitWidth: 40
            implicitHeight: 40
            buttonRadius: 20
            colBackground: Appearance.colors.colLayer2
            onClicked: tool.translate(input.text)
            contentItem: Item {
                MaterialLoadingIndicator {
                    anchors.centerIn: parent
                    visible: tool.busy
                    implicitSize: 26
                    loading: tool.busy
                }
                MaterialSymbol {
                    anchors.centerIn: parent
                    visible: !tool.busy
                    text: "translate"
                    iconSize: 20
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
    }

    StyledText {
        visible: tool.busy && (tool.slow || tool.llmStage)
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
        text: tool.waking ? "Waking up " + tool.llmName + "... (the first call can take a while)" : tool.llmStage ? "Asking " + tool.llmName + "..." : "Still waiting for Linguee..."
    }

    Rectangle {
        visible: !tool.busy && tool.result !== null
        Layout.fillWidth: true
        implicitHeight: resultCol.implicitHeight + 24
        radius: Appearance.rounding.small
        color: Appearance.colors.colLayer2

        ColumnLayout {
            id: resultCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 12
            spacing: 8

            RowLayout {
                visible: !!tool.result?.ok
                Layout.fillWidth: true
                spacing: 6
                StyledText {
                    text: tool.langName(tool.result?.src) + "  >  " + tool.langName(tool.result?.dst)
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                }
                Item { Layout.fillWidth: true }
                StyledText {
                    visible: tool.copied !== ""
                    text: "Copied"
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colPrimary
                }
                Rectangle {
                    implicitHeight: 20
                    implicitWidth: sourceLabel.implicitWidth + 14
                    radius: 10
                    color: Appearance.colors.colSecondaryContainer
                    StyledText {
                        id: sourceLabel
                        anchors.centerIn: parent
                        text: (tool.result?.engine === "linguee" || !tool.result?.engine ? "Linguee" : (tool.result?.engineName ?? "AI model")) + (tool.result?.cached ? " (cached)" : "")
                        font.pixelSize: Appearance.font.pixelSize.smallest
                        color: Appearance.colors.colOnSecondaryContainer
                    }
                }
            }

            StyledText {
                visible: !!tool.result && !tool.result.ok
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tool.result?.error ?? ""
                color: Appearance.colors.colError
            }

            StyledFlickable {
                visible: !!tool.result?.ok
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(body.implicitHeight, 360)
                contentHeight: body.implicitHeight
                clip: true

                ColumnLayout {
                    id: body
                    width: parent.width
                    spacing: 8

                    ColumnLayout {
                        visible: tool.result?.engine === "llm" || tool.result?.engine === "qwen"
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            TextEdit {
                                Layout.fillWidth: true
                                readOnly: true
                                selectByMouse: true
                                wrapMode: TextEdit.Wrap
                                text: tool.result?.translation ?? ""
                                color: Appearance.colors.colOnLayer2
                                selectionColor: Appearance.colors.colSecondaryContainer
                                selectedTextColor: Appearance.colors.colOnSecondaryContainer
                                font.family: Appearance.font.family.main
                                font.pixelSize: Appearance.font.pixelSize.larger
                            }
                            CopyButton {
                                copyText: tool.result?.translation ?? ""
                            }
                        }
                        StyledText {
                            visible: (tool.result?.reading ?? "") !== ""
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            text: (tool.result?.reading ?? "") + "  (reading by the AI model, may be off)"
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.colors.colSubtext
                        }
                        StyledText {
                            visible: (tool.result?.meaning ?? "") !== ""
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            text: "Understood as: " + (tool.result?.meaning ?? "")
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            font.italic: true
                            color: Appearance.colors.colSubtext
                        }
                    }

                    Repeater {
                        model: tool.result?.engine === "linguee" ? tool.result.entries : []
                        delegate: ColumnLayout {
                            id: entry
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 2
                            StyledText {
                                Layout.fillWidth: true
                                text: entry.modelData.word + (entry.modelData.pos ? "  -  " + entry.modelData.pos : "")
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: Appearance.colors.colSubtext
                            }
                            Repeater {
                                model: entry.modelData.main
                                delegate: RowLayout {
                                    id: line
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 6
                                    StyledText {
                                        text: line.modelData.text
                                        font.pixelSize: Appearance.font.pixelSize.large
                                        color: Appearance.colors.colOnLayer2
                                        Layout.maximumWidth: 330
                                        wrapMode: Text.Wrap
                                    }
                                    StyledText {
                                        visible: line.modelData.type !== ""
                                        text: line.modelData.type
                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                        color: Appearance.colors.colSubtext
                                    }
                                    Item { Layout.fillWidth: true }
                                    CopyButton {
                                        copyText: line.modelData.text
                                    }
                                }
                            }
                            Flow {
                                visible: entry.modelData.less.length > 0
                                Layout.fillWidth: true
                                spacing: 4
                                StyledText {
                                    height: 26
                                    verticalAlignment: Text.AlignVCenter
                                    text: "Less common:"
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    color: Appearance.colors.colSubtext
                                }
                                Repeater {
                                    model: entry.modelData.less
                                    delegate: Chip {
                                        required property var modelData
                                        small: true
                                        label: modelData.text
                                        colBackground: Appearance.colors.colLayer3
                                        onClicked: tool.copy(modelData.text)
                                    }
                                }
                            }
                        }
                    }

                    StyledText {
                        visible: (tool.result?.examples ?? []).length > 0
                        text: "Examples (click to copy)"
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.colors.colSubtext
                    }

                    Repeater {
                        model: tool.result?.examples ?? []
                        delegate: RippleButton {
                            id: ex
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: exCol.implicitHeight + 12
                            buttonRadius: Appearance.rounding.small
                            colBackground: Appearance.colors.colLayer3
                            onClicked: tool.copy(ex.modelData.t)
                            contentItem: ColumnLayout {
                                id: exCol
                                spacing: 2
                                StyledText {
                                    Layout.fillWidth: true
                                    Layout.leftMargin: 4
                                    wrapMode: Text.Wrap
                                    text: ex.modelData.s
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                    color: Appearance.colors.colSubtext
                                }
                                StyledText {
                                    Layout.fillWidth: true
                                    Layout.leftMargin: 4
                                    wrapMode: Text.Wrap
                                    text: ex.modelData.t
                                    font.pixelSize: Appearance.font.pixelSize.small
                                    color: Appearance.colors.colOnLayer2
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                RippleButtonWithIcon {
                    visible: tool.result?.retry ?? false
                    materialIcon: "refresh"
                    mainText: "Retry"
                    onClicked: tool.translate(tool.query)
                }
                Item { Layout.fillWidth: true }
                RippleButtonWithIcon {
                    visible: (tool.result?.url ?? "") !== ""
                    materialIcon: "open_in_new"
                    mainText: tool.result?.urlLabel ?? "Open in Linguee"
                    onClicked: tool.openUrl(tool.result.url)
                }
            }
        }
    }

    StyledText {
        visible: tool.history.length > 0
        text: "Recent"
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
    }

    Flow {
        visible: tool.history.length > 0
        Layout.fillWidth: true
        spacing: 6
        Repeater {
            model: tool.history.slice(0, 8)
            delegate: Chip {
                required property var modelData
                small: true
                label: modelData.query
                onClicked: tool.translate(modelData.query)
            }
        }
    }

    component CopyButton: RippleButton {
        id: copyButton
        property string copyText
        implicitWidth: 28
        implicitHeight: 28
        buttonRadius: 14
        onClicked: tool.copy(copyButton.copyText)
        contentItem: MaterialSymbol {
            text: tool.copied !== "" && tool.copied === copyButton.copyText ? "check" : "content_copy"
            iconSize: 16
            horizontalAlignment: Text.AlignHCenter
            color: Appearance.colors.colOnLayer2
        }
    }
}
