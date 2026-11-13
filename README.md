# dotfiles

A modular layer on top of [end-4's dots-hyprland](https://github.com/end-4/dots-hyprland)
(illogical-impulse: Hyprland and a quickshell bar). The installer sets up end-4 at a pinned
commit, then adds the modules you pick. Every module is optional, and you can add or remove one
later without touching the rest.

Works on Arch and on Ubuntu 26.04 or newer. On Ubuntu 24.04 only the terminal modules install
(its Qt is too old for quickshell).

## Install

    git clone https://github.com/rom618/dotfiles ~/.local/share/dotfiles/repo
    cd ~/.local/share/dotfiles/repo
    ./install.sh                            # pick modules in a checklist, then install

The checklist shows every module with its description, grouped (Desktop, Terminal, System),
defaults ticked; on a later run, your current choice is ticked. Space ticks, Enter installs,
`d` resets to the defaults, `q` quits without changing anything. Modules your system cannot run
are greyed out.

Without the checklist (scripts, agents):

    ./install.sh list                       # the modules, defaults marked
    ./install.sh install --dry-run --yes    # what would happen, changes nothing
    ./install.sh install --yes              # end-4 + the default modules

    ./install.sh install --modules kitty,fish-aliases,bar-docker
    ./install.sh install --add nvim-vim --remove bar-layout
    ./install.sh install --all

The choice is remembered: the next `install` or `update` keeps it. Modules marked `sudo` change
system files and ask for your password.

## Update

    ./install.sh update             # pull this repo, then apply it
    ./install.sh timer on           # daily automatic update (off by default)
    ./install.sh timer off
    ./install.sh status             # modules, files you changed, waiting new versions

## Your own changes

Edit any installed file as you like. An update never overwrites a file you changed: the new
version is written next to it as `<name>.dotfiles-new`, and `status` lists them. Merge what you
want, then delete the `.dotfiles-new` file. A file that existed before the first install is
backed up to `~/.local/state/dotfiles/backup/` before it is replaced.

Some modules also set a few shell settings in `~/.config/illogical-impulse/config.json` (for
example which bar buttons show). The same rule applies per setting: the installer only changes a
setting that is still at end-4's default or at the value it set itself. A setting you changed is
kept (the installer says so once) and is never touched again; removing the module puts its
unchanged settings back to end-4's defaults.

end-4's own files follow end-4's rules: its installer may overwrite them when the pinned end-4
commit changes.

The installer never writes agent or ssh configuration (`~/.claude`, `~/.codex`, `~/.agents`,
`~/.ssh/config`, `~/.config/environment.d`): tools that manage those keep them.

## For agents

Everything is non-interactive with `--yes`; `--dry-run` shows the plan. Module metadata is in
`modules.toml`; installed state is `~/.local/state/dotfiles/state.json`.

## Several accounts on one machine

The `multi-user` module shares one checkout between accounts: clone it outside the homes (for
example `/srv/dotfiles`), then run `./install.sh install --add multi-user --group dotfiles` once.
It creates the group, gives it write access to the checkout and adds you. Add each other account
with `sudo usermod -aG dotfiles NAME`; that account then runs `./install.sh install` itself and
picks its own modules.

## License

GPL-3.0, like end-4's dots-hyprland, which this builds on.
