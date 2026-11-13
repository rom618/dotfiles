#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "illogical-impulse" / "config.json"
STATE_PATH = Path.home() / ".local" / "state" / "quickshell" / "states.json"


def load(path):
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=4))
    tmp.replace(path)


def cmd_prompt():
    config = load(CONFIG_PATH)
    current = config.get("ai", {}).get("systemPrompt", "")
    editor = os.environ.get("EDITOR", "nvim")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(current)
        tmp_path = f.name
    try:
        subprocess.run([editor, tmp_path], check=True)
        new_text = Path(tmp_path).read_text()
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if new_text == current:
        print("No changes.")
        return
    config.setdefault("ai", {})["systemPrompt"] = new_text
    save(CONFIG_PATH, config)
    print("Persona updated. Reopen the AI chat sidebar to see it take effect.")


def safe_model_name(name):
    return name.replace(":", "_").replace(" ", "-").replace("/", "-")


def list_ollama_models():
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return []
    lines = out.stdout.strip().splitlines()[1:]
    return [line.split()[0] for line in lines if line.strip()]


def cmd_model(name):
    models = list_ollama_models()
    if name is None:
        if not models:
            print("No local Ollama models found. Pull one with: ollama pull <model>")
            return
        state = load(STATE_PATH)
        current = state.get("ai", {}).get("model", "")
        print("Installed Ollama models:")
        for m in models:
            marker = " (current)" if safe_model_name(m) == current else ""
            print(f"  {m}{marker}")
        print("Set one with: aiconfig model <name>")
        return
    if models and name not in models:
        print(f"Warning: '{name}' is not in `ollama list`. Setting it anyway.", file=sys.stderr)
    state = load(STATE_PATH)
    state.setdefault("ai", {})["model"] = safe_model_name(name)
    save(STATE_PATH, state)
    print(f"Model set to {name}. Reopen the AI chat sidebar to see it take effect.")


SETTABLE_FIELDS = ("tool", "characterName", "avatarIcon")


def cmd_show():
    config = load(CONFIG_PATH)
    state = load(STATE_PATH)
    ai_config = config.get("ai", {})
    print("Current model:", state.get("ai", {}).get("model", "(default)"))
    print("Tool mode (ai.tool):", ai_config.get("tool", "(default)"))
    print("Character name (ai.characterName):", ai_config.get("characterName") or "(none, shows model name)")
    print("Avatar icon (ai.avatarIcon):", ai_config.get("avatarIcon") or "(default)")
    print()
    print("Current persona (ai.systemPrompt):")
    print(ai_config.get("systemPrompt", "(none)"))


def cmd_set(field, value):
    if field not in SETTABLE_FIELDS:
        print(f"Unknown field '{field}'. Settable fields: {', '.join(SETTABLE_FIELDS)}", file=sys.stderr)
        print("(use 'aiconfig prompt' for systemPrompt, 'aiconfig model' for the model)", file=sys.stderr)
        sys.exit(1)
    config = load(CONFIG_PATH)
    config.setdefault("ai", {})[field] = value
    save(CONFIG_PATH, config)
    print(f"ai.{field} set to: {value}")
    print("Reopen the AI chat sidebar to see it take effect.")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "prompt":
        cmd_prompt()
    elif args[0] == "model":
        cmd_model(args[1] if len(args) > 1 else None)
    elif args[0] == "show":
        cmd_show()
    elif args[0] == "set":
        if len(args) < 3:
            print("Usage: aiconfig set <field> <value>", file=sys.stderr)
            print(f"Settable fields: {', '.join(SETTABLE_FIELDS)}", file=sys.stderr)
            sys.exit(1)
        cmd_set(args[1], " ".join(args[2:]))
    else:
        print("Usage: aiconfig [prompt|model [name]|show|set <field> <value>]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
