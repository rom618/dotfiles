#!/usr/bin/env bash
# SSH_ASKPASS helper: prints the passphrase of the key file named in ssh-add's prompt, from the
# login keyring (secret-tool attributes dotfiles=ssh-key path=<key file>).
f="$(printf '%s' "${1:-}" | grep -oE '/[^ :()]+' | head -n 1)"
[ -n "$f" ] || exit 1
exec secret-tool lookup dotfiles ssh-key path "$f"
