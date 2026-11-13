import QtQuick

ApiStrategy {
    property bool isReasoning: false
    property bool thinkingEnabled: true
    property var pendingToolCall: null

    function buildEndpoint(model: AiModel): string {
        // console.log("[AI] Endpoint: " + model.endpoint);
        return model.endpoint;
    }

    function buildRequestData(model: AiModel, messages, systemPrompt: string, temperature: real, tools: list<var>, filePath: string, thinkingEnabled: bool) {
        let baseData = {
            "model": model.model,
            "messages": [
                {role: "system", content: systemPrompt},
                ...messages.map(message => {
                    return {
                        "role": message.role,
                        "content": message.rawContent,
                    }
                }),
            ],
            "stream": true,
            "tools": tools,
            "temperature": temperature,
        };
        // "think" is an Ollama-only extension, harmless elsewhere but only
        // meaningful for local models, so only send it for those. Note:
        // Ollama's "keep_alive" field is NOT honored on this OpenAI-compat
        // endpoint (confirmed empirically - only /api/chat respects it), so
        // idle-unload timing is instead handled with an explicit "ollama
        // stop" timer in Ai.qml.
        if (model.endpoint?.includes("localhost") && !thinkingEnabled) {
            baseData["think"] = false;
        }
        return model.extraParams ? Object.assign({}, baseData, model.extraParams) : baseData;
    }

    function buildAuthorizationHeader(apiKeyEnvVarName: string): string {
        return `-H "Authorization: Bearer \$\{${apiKeyEnvVarName}\}"`;
    }

    function parseResponseLine(line, message) {
        // Remove 'data: ' prefix if present and trim whitespace
        let cleanData = line.trim();
        if (cleanData.startsWith("data:")) {
            cleanData = cleanData.slice(5).trim();
        }

        // console.log("[AI] OpenAI: Data:", cleanData);
        
        // Handle special cases
        if (!cleanData || cleanData.startsWith(":")) return {};
        if (cleanData === "[DONE]") {
            return { finished: true };
        }
        
        // Real stuff
        try {
            const dataJson = JSON.parse(cleanData);

            // Error response handling
            if (dataJson.error) {
                const errorMsg = `**Error**: ${dataJson.error.message || JSON.stringify(dataJson.error)}`;
                message.rawContent += errorMsg;
                message.content += errorMsg;
                return { finished: true };
            }

            let newContent = "";

            const toolCallDeltas = dataJson.choices[0]?.delta?.tool_calls;
            if (toolCallDeltas && toolCallDeltas.length > 0) {
                const call = toolCallDeltas[0];
                if (!pendingToolCall || (call.id && call.id !== pendingToolCall.id)) {
                    pendingToolCall = { id: call.id ?? "", name: "", arguments: "" };
                }
                if (call.function?.name) pendingToolCall.name += call.function.name;
                if (call.function?.arguments) pendingToolCall.arguments += call.function.arguments;
            }

            const finishReason = dataJson.choices[0]?.finish_reason;
            if (finishReason === "tool_calls" && pendingToolCall) {
                const finishedCall = pendingToolCall;
                pendingToolCall = null;
                let args = {};
                try {
                    args = JSON.parse(finishedCall.arguments || "{}");
                } catch (e) {
                    console.log("[AI] OpenAI: Could not parse tool call arguments: ", e);
                }
                return { functionCall: { name: finishedCall.name, args: args } };
            }

            const responseContent = dataJson.choices[0]?.delta?.content || dataJson.message?.content;
            const responseReasoning = thinkingEnabled ?
                (dataJson.choices[0]?.delta?.reasoning || dataJson.choices[0]?.delta?.reasoning_content) : "";

            if (responseContent && responseContent.length > 0) {
                if (isReasoning) {
                    isReasoning = false;
                    const endBlock = "\n\n</think>\n\n";
                    message.content += endBlock;
                    message.rawContent += endBlock;
                }
                newContent = responseContent;
            } else if (responseReasoning && responseReasoning.length > 0) {
                if (!isReasoning) {
                    isReasoning = true;
                    const startBlock = "\n\n<think>\n\n";
                    message.rawContent += startBlock;
                    message.content += startBlock;
                }
                newContent = responseReasoning;
            }

            message.content += newContent;
            message.rawContent += newContent;

            // Usage metadata
            if (dataJson.usage) {
                return {
                    tokenUsage: {
                        input: dataJson.usage.prompt_tokens ?? -1,
                        output: dataJson.usage.completion_tokens ?? -1,
                        total: dataJson.usage.total_tokens ?? -1
                    }
                };
            }

            if (dataJson.done) {
                return { finished: true };
            }
            
        } catch (e) {
            console.log("[AI] OpenAI: Could not parse line: ", e);
            message.rawContent += line;
            message.content += line;
        }
        
        return {};
    }
    
    function onRequestFinished(message) {
        // OpenAI format doesn't need special finish handling
        return {};
    }
    
    function reset(thinkingEnabled: bool) {
        isReasoning = false;
        this.thinkingEnabled = thinkingEnabled ?? true;
        pendingToolCall = null;
    }

}
