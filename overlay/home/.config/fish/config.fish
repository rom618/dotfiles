# Commands to run in interactive sessions can go here
if status is-interactive
    # No greeting
    set fish_greeting

    # Use starship
    function starship_transient_prompt_func
        starship module character
    end
    if test "$TERM" != "linux"
        starship init fish | source
        enable_transience
    end
    
    # Colors
    if test -f ~/.local/state/quickshell/user/generated/terminal/sequences.txt
        cat ~/.local/state/quickshell/user/generated/terminal/sequences.txt
    end

    # share:begin fish-aliases
    # Aliases, kept sorted alphabetically
    # share:else
    #     # Aliases
    #     # kitty doesn't clear properly so we need to do this weird printing
    #     alias clear "printf '\033[2J\033[3J\033[1;1H'"
    # share:end
    # share:begin ai-sidebar-extras
    alias aiconfig="python3 ~/.config/hypr/custom/scripts/ai-config.py"
    # share:end
    # share:begin fish-aliases
    # kitty doesn't clear properly so we need to do this weird printing;
    # celar/claer are deliberate typo-catches for clear, not deprecated
    # share:end
    alias celar "printf '\033[2J\033[3J\033[1;1H'"
    alias claer "printf '\033[2J\033[3J\033[1;1H'"
    # share:begin fish-aliases
    alias clear "printf '\033[2J\033[3J\033[1;1H'"
    # share:end
    # share:begin nvim-vim
    alias fishrc="nv ~/.config/fish/config.fish"
    alias keybinds="nv ~/.config/hypr/custom/keybinds.lua"
    # share:end
    # share:begin fish-aliases
    alias ll='lsl'
    alias lla='lsl -a'
    alias ls='eza --icons=auto --tree --level=1 --follow-symlinks --no-quotes '
    alias lsa='ls -a'
    alias lsl='eza --icons=auto --long --header --group -M'
    # share:end
    # share:begin nvim-vim
    alias nv="nvim"
    # share:end
    alias pamcan pacman
    alias q 'qs -c ii'
    # share:begin fish-aliases
    alias reload="exec fish"
    alias renametab="kitten @ set-window-title --"
    alias rot13="tr 'A-Za-z' 'N-ZA-Mn-za-m'"
    alias tree='eza --icons=auto --tree --level=3 --follow-symlinks --no-quotes'
    # if test "$TERM" != "linux"
    #     alias ls 'eza --icons=auto'
    # end
    # share:else
    #     if test "$TERM" != "linux"
    #         alias ls 'eza --icons=auto'
    #     end
    # share:end
    if test "$TERM" = "xterm-kitty"
        alias ssh 'kitten ssh'
    end
end
# share:begin fish-aliases

# Created by `pipx` on 2026-07-01 19:12:24
# share:end
# share:begin nvim-vim
set -x SUDO_EDITOR nvim
# share:end
# share:begin fish-aliases
fish_add_path $HOME/.local/bin
# share:end
