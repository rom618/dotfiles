pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property var aliases: []
    property var functions: []

    function unquote(text) {
        const trimmed = text.trim()
        if ((trimmed.startsWith("'") && trimmed.endsWith("'")) ||
            (trimmed.startsWith('"') && trimmed.endsWith('"'))) {
            return trimmed.slice(1, -1)
        }
        return trimmed
    }

    function parse(text) {
        const lines = text.split("\n")
        const aliasPattern = /^\s*alias\s+([^\s=]+)=?\s*(.+)$/
        const functionPattern = /^\s*function\s+(\S+)(.*)$/
        const descriptionPattern = /--description[= ]\s*(".*?"|'.*?'|\S+)/
        const newAliases = []
        const newFunctions = []
        for (const line of lines) {
            const trimmed = line.trim()
            if (trimmed.startsWith("#")) continue

            const aliasMatch = trimmed.match(aliasPattern)
            if (aliasMatch) {
                newAliases.push({ name: aliasMatch[1], command: root.unquote(aliasMatch[2]) })
                continue
            }

            const functionMatch = trimmed.match(functionPattern)
            if (functionMatch) {
                const rest = functionMatch[2]
                const descMatch = rest.match(descriptionPattern)
                // Only list functions that bothered to set --description; internal helpers
                // (e.g. starship's prompt callback) don't, and shouldn't show up here
                if (descMatch) {
                    newFunctions.push({ name: functionMatch[1], command: root.unquote(descMatch[1]) })
                }
            }
        }
        newAliases.sort((a, b) => a.name.localeCompare(b.name))
        newFunctions.sort((a, b) => a.name.localeCompare(b.name))
        root.aliases = newAliases
        root.functions = newFunctions
    }

    Timer {
        interval: 60000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: fishConfigProc.running = true
    }

    Process {
        id: fishConfigProc
        command: ["bash", "-c", `cat ${FileUtils.trimFileProtocol(Directories.config)}/fish/config.fish ${FileUtils.trimFileProtocol(Directories.config)}/fish/conf.d/*.fish 2>/dev/null`]
        stdout: StdioCollector {
            onStreamFinished: root.parse(text)
        }
    }
}
