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

    readonly property string script: Quickshell.shellPath("scripts/tools/dictionary.py")
    readonly property var langs: [
        { code: "", name: "Auto" },
        { code: "en", name: "English" },
        { code: "fr", name: "French" },
        { code: "es", name: "Spanish" },
        { code: "ja", name: "Japanese" },
        { code: "zh", name: "Chinese" }
    ]
    property string lang: ""
    property string query: ""
    property var result: null
    property var history: []
    property bool busy: false
    property bool slow: false

    function langName(code) {
        const l = tool.langs.find(x => x.code === code);
        return l ? l.name : code;
    }

    function persist() {
        host.store.dictionary = { lang: tool.lang, query: tool.query, result: tool.result, history: tool.history };
    }

    function lookup(q) {
        q = (q || "").trim();
        if (q === "")
            return;
        tool.query = q;
        input.text = q;
        tool.result = null;
        tool.busy = true;
        tool.slow = false;
        slowTimer.restart();
        proc.running = false;
        proc.command = tool.lang === "" ? ["python3", tool.script, q] : ["python3", tool.script, "--lang", tool.lang, q];
        proc.running = true;
        tool.persist();
    }

    function setLang(code) {
        if (tool.lang === code)
            return;
        tool.lang = code;
        tool.persist();
        if (tool.query !== "" && (tool.busy || tool.result !== null))
            tool.lookup(tool.query);
    }

    function openUrl(url) {
        if (!url)
            return;
        Quickshell.execDetached(["firefox", url]);
        host.menuOpen = false;
    }

    Component.onCompleted: {
        const s = host.store.dictionary;
        if (s) {
            tool.lang = s.lang ?? "";
            tool.query = s.query ?? "";
            tool.result = s.result ?? null;
            tool.history = s.history ?? [];
        }
        input.text = tool.query;
        input.forceActiveFocus();
        input.selectAll();
        historyProc.running = true;
    }

    Timer {
        id: slowTimer
        interval: 1000
        onTriggered: tool.slow = tool.busy
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
                tool.result = { ok: false, query: tool.query, error: "The dictionary tool stopped (" + code + ")", retry: true };
            }
        }
    }

    Process {
        id: historyProc
        command: ["python3", tool.script, "--history"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    tool.history = JSON.parse(data).history ?? [];
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
        Repeater {
            model: tool.langs
            delegate: Chip {
                required property var modelData
                label: modelData.name
                toggled: tool.lang === modelData.code
                onClicked: tool.setLang(modelData.code)
            }
        }
        Item { Layout.fillWidth: true }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        MaterialTextField {
            id: input
            Layout.fillWidth: true
            placeholderText: "A word in English, French, Spanish, Japanese or Chinese"
            focus: true
            Keys.onReturnPressed: tool.lookup(text)
            Keys.onEnterPressed: tool.lookup(text)
            Keys.onEscapePressed: host.menuOpen = false
        }
        RippleButton {
            implicitWidth: 40
            implicitHeight: 40
            buttonRadius: 20
            colBackground: Appearance.colors.colLayer2
            onClicked: tool.lookup(input.text)
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
                    text: "search"
                    iconSize: 20
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
    }

    StyledText {
        visible: tool.busy && tool.slow
        Layout.fillWidth: true
        font.pixelSize: Appearance.font.pixelSize.small
        color: Appearance.colors.colSubtext
        text: "Still waiting for Wiktionary..."
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

            StyledText {
                visible: !!tool.result && !tool.result.ok
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tool.result?.error ?? ""
                color: tool.result?.retry ? Appearance.colors.colError : Appearance.colors.colOnLayer2
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
                    spacing: 10

                    Repeater {
                        model: tool.result?.sections ?? []
                        delegate: ColumnLayout {
                            id: section
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 4

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                StyledText {
                                    text: section.modelData.language
                                    font.pixelSize: Appearance.font.pixelSize.normal
                                    font.weight: Font.DemiBold
                                    color: Appearance.colors.colOnLayer2
                                }
                                StyledText {
                                    visible: section.modelData.reading !== ""
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    text: section.modelData.reading
                                    font.pixelSize: Appearance.font.pixelSize.large
                                    color: Appearance.colors.colPrimary
                                }
                                Item {
                                    visible: section.modelData.reading === ""
                                    Layout.fillWidth: true
                                }
                                RippleButton {
                                    implicitHeight: 22
                                    implicitWidth: srcLabel.implicitWidth + 16
                                    buttonRadius: 11
                                    colBackground: Appearance.colors.colSecondaryContainer
                                    onClicked: tool.openUrl(section.modelData.url)
                                    StyledToolTip {
                                        text: "Open the full page"
                                    }
                                    contentItem: StyledText {
                                        id: srcLabel
                                        text: section.modelData.source
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pixelSize: Appearance.font.pixelSize.smallest
                                        color: Appearance.colors.colOnSecondaryContainer
                                    }
                                }
                            }

                            StyledText {
                                visible: (section.modelData.note ?? "") !== ""
                                text: section.modelData.note ?? ""
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                color: Appearance.colors.colSubtext
                            }

                            Repeater {
                                model: section.modelData.entries
                                delegate: ColumnLayout {
                                    id: entry
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 3
                                    StyledText {
                                        text: entry.modelData.pos
                                        font.pixelSize: Appearance.font.pixelSize.smaller
                                        font.italic: true
                                        color: Appearance.colors.colSubtext
                                    }
                                    Repeater {
                                        model: entry.modelData.senses
                                        delegate: ColumnLayout {
                                            id: sense
                                            required property var modelData
                                            required property int index
                                            Layout.fillWidth: true
                                            spacing: 1
                                            TextEdit {
                                                Layout.fillWidth: true
                                                readOnly: true
                                                selectByMouse: true
                                                wrapMode: TextEdit.Wrap
                                                text: (sense.index + 1) + ". " + sense.modelData.text
                                                color: Appearance.colors.colOnLayer2
                                                selectionColor: Appearance.colors.colSecondaryContainer
                                                selectedTextColor: Appearance.colors.colOnSecondaryContainer
                                                font.family: Appearance.font.family.main
                                                font.pixelSize: Appearance.font.pixelSize.small
                                            }
                                            Repeater {
                                                model: sense.index < 4 ? sense.modelData.examples : []
                                                delegate: StyledText {
                                                    required property var modelData
                                                    Layout.fillWidth: true
                                                    Layout.leftMargin: 18
                                                    wrapMode: Text.Wrap
                                                    text: modelData.text + (modelData.translation ? "  -  " + modelData.translation : "")
                                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                                    font.italic: true
                                                    color: Appearance.colors.colSubtext
                                                }
                                            }
                                        }
                                    }
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
                    onClicked: tool.lookup(tool.query)
                }
                Repeater {
                    model: tool.result?.others ?? []
                    delegate: Chip {
                        required property var modelData
                        small: true
                        label: "In " + tool.langName(modelData)
                        onClicked: tool.setLang(modelData)
                    }
                }
                Item { Layout.fillWidth: true }
                RippleButtonWithIcon {
                    visible: (tool.result?.url ?? "") !== ""
                    materialIcon: "open_in_new"
                    mainText: "Wiktionary"
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
                onClicked: tool.lookup(modelData.query)
            }
        }
    }
}
