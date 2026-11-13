#!/usr/bin/env bash
# At login: load this user's ssh keys into the agent, each passphrase read from the login keyring
# (secret-tool attributes dotfiles=ssh-key path=<key file>).
# Keys without such an entry are left alone. No-op without the keyring or the agent.
set -u
export SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/ssh-agent.socket}"
command -v secret-tool >/dev/null || exit 0
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

for _ in $(seq 1 20); do
    [ -S "$SSH_AUTH_SOCK" ] && break
    sleep 0.5
done
[ -S "$SSH_AUTH_SOCK" ] || exit 0

for f in "$HOME"/.ssh/id_*; do
    case "$f" in *.pub) continue ;; esac
    [ -f "$f" ] || continue
    secret-tool lookup dotfiles ssh-key path "$f" >/dev/null 2>&1 || continue
    SSH_ASKPASS="$here/ssh-askpass-keyring.sh" SSH_ASKPASS_REQUIRE=force ssh-add -q "$f" </dev/null
done
