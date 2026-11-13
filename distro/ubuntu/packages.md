# illogical-impulse dependencies on Ubuntu

Mapping of end-4's Arch dependency lists (`sdata/dist-arch/illogical-impulse-*/PKGBUILD` at
dots-hyprland commit `42d0aae17b744a38cd05c9044c189bfc9b13869a`) to Ubuntu 26.04 LTS
(resolute) and 26.10 (stonking). `deps.sh` in this folder installs all of it.

Supported releases:

| Release | Hyprland source | Qt | Notes |
|---|---|---|---|
| 26.04 LTS | `ppa:cppiber/hyprland` (0.57.2 on 2026-11-13; Ubuntu ships 0.53.3, too old for the Lua config) | 6.10 | cpptrace vendored into the quickshell build; uv from upstream |
| 26.10 | Ubuntu universe (0.56.2) | 6.11 | everything else from the archive |
| 24.04 and older | refused | 6.4 | quickshell needs Qt 6.6+ |

Legend for "How": `apt` = Ubuntu archive, `ppa` = Launchpad PPA (key pinned by fingerprint),
`release` = upstream release file with a pinned sha256, `git` = upstream source at a pinned
commit, `build` = compiled by `deps.sh`.

## audio

| Arch | Ubuntu | How |
|---|---|---|
| cava | cava | apt |
| pavucontrol-qt | pavucontrol-qt | apt |
| wireplumber | wireplumber | apt |
| pipewire-pulse | pipewire-pulse | apt |
| libdbusmenu-gtk3 | libdbusmenu-gtk3-4 | apt |
| playerctl | playerctl | apt |
| (used by the config) | pulseaudio-utils (`pactl`), sound-theme-freedesktop | apt |

## backlight

| Arch | Ubuntu | How |
|---|---|---|
| geoclue | geoclue-2.0 | apt |
| brightnessctl | brightnessctl | apt |
| ddcutil | ddcutil | apt |

## basic

| Arch | Ubuntu | How |
|---|---|---|
| bc, coreutils, cmake, curl, wget, ripgrep, jq, xdg-user-dirs, rsync | same names | apt |
| cliphist | cliphist | apt |
| go-yq | mikefarah yq 4.54.1 to `/usr/local/bin/yq` | release (Ubuntu's `yq` is the Python one) |

## fonts-themes

| Arch | Ubuntu | How |
|---|---|---|
| adw-gtk-theme-git | adw-gtk3 v6.5 to `/usr/share/themes` | release |
| breeze | breeze, breeze-icon-theme | apt |
| breeze-plus | breeze-plus 6.28.0 to `/usr/share/icons` | release (source tarball) |
| darkly-bin | Darkly v0.5.42, Qt6 style only, no KWin decoration | build |
| eza, fish, fontconfig, kitty, starship | same names | apt |
| matugen | matugen 4.2.0 binary to `/usr/local/bin` | release |
| otf-space-grotesk | Space Grotesk 2.0.0 OTF | release |
| ttf-jetbrains-mono-nerd | JetBrainsMono Nerd Font 3.5.1 | release |
| ttf-material-symbols-variable-git | Material Symbols Rounded/Outlined/Sharp variable, google/material-design-icons `10ecc14` | git (raw files, sha256) |
| ttf-readex-pro | Readex Pro variable, ThomasJockin/readexpro `563dfbb` | git (raw file, sha256) |
| ttf-rubik-vf | Rubik variable, googlefonts/rubik `e337a5f` (same commit as end-4's Gentoo port) | git (raw files, sha256) |
| ttf-twemoji | **replaced** by fonts-noto-color-emoji | apt |
| (not in Arch list, used as the main UI font) | Google Sans Flex variable, google/fonts `bd8f81d` | git (raw file, sha256) |

Fonts go to `/usr/local/share/fonts/illogical-impulse/`.

## hyprland

| Arch | Ubuntu | How |
|---|---|---|
| hyprland | hyprland | 26.04: ppa, 26.10: apt |
| hyprsunset | hyprsunset | 26.04: ppa, 26.10: apt |
| wl-clipboard | wl-clipboard | apt |
| (pulled in by Arch's hyprland) | hyprland-guiutils | 26.04: ppa, 26.10: apt |

## kde

| Arch | Ubuntu | How |
|---|---|---|
| bluedevil, gnome-keyring, plasma-nm, dolphin, systemsettings | same names | apt |
| networkmanager | network-manager | apt |
| polkit-kde-agent | polkit-kde-agent-1 | apt |
| (used by the setup step: `kwriteconfig6`) | libkf6config-bin | apt |

## microtex-git

| Arch | Ubuntu | How |
|---|---|---|
| illogical-impulse-microtex-git | end-4/MicroTeX `0e3707f` to `/opt/MicroTeX` | build |
| tinyxml2, gtkmm3, gtksourceviewmm, cairomm | libtinyxml2-dev, libgtkmm-3.0-dev, libgtksourceviewmm-3.0-dev, libcairomm-1.0-dev | apt |

Arch patches gtksourceviewmm-3.0 to 4.0; Ubuntu still has 3.0, so no patch.
`--no-microtex` skips it (LaTeX rendering in the sidebar then does not work).

## portal

| Arch | Ubuntu | How |
|---|---|---|
| xdg-desktop-portal, -kde, -gtk | same names | apt |
| xdg-desktop-portal-hyprland | same name | 26.04: ppa, 26.10: apt |

## python

| Arch | Ubuntu | How |
|---|---|---|
| clang | clang | apt |
| uv | 26.04: uv 0.13.6 to `/usr/local/bin`; 26.10: uv | release / apt |
| gtk4, libadwaita, libsoup3, libportal-gtk4, gobject-introspection | libgtk-4-dev, libadwaita-1-dev, libsoup-3.0-dev, libportal-gtk4-dev, gobject-introspection, libgirepository-2.0-dev, libgirepository1.0-dev, libcairo2-dev, python3-dev | apt |

The venv itself (`sdata/uv/requirements.txt`, Python 3.12) is created by end-4's setup step;
Ubuntu has no python3.12, uv downloads a managed CPython 3.12.

## quickshell-git

| Arch | Ubuntu | How |
|---|---|---|
| quickshell `4f508be500dea6e5732cc3d50382a0048b17e7b1 (v0.3.2, what Arch ships)` | same commit, end-4's cmake flags, prefix `/usr/local` | build (git.outfoxxed.me, fallback github mirror) |
| cpptrace | 26.10: libcpptrace-dev; 26.04: `-DVENDOR_CPPTRACE=ON` (libunwind-dev, libdwarf-dev, libzstd-dev) | apt / build |
| jemalloc, libdrm, libpipewire, libxcb, wayland, mesa | libjemalloc-dev, libdrm-dev, libpipewire-0.3-dev, libxcb1-dev, libwayland-dev, libgbm-dev, libegl-dev | apt |
| qt6-base, qt6-declarative, qt6-svg, qt6-wayland | qt6-base(-private)-dev, qt6-declarative(-private)-dev, qt6-svg-dev, qt6-svg-plugins, qt6-wayland(-dev) | apt |
| qt6-5compat | qml6-module-qt5compat-graphicaleffects | apt |
| qt6-avif-image-plugin, qt6-imageformats | kimageformat6-plugins, qt6-image-formats-plugins | apt |
| qt6-multimedia | qml6-module-qtmultimedia | apt |
| qt6-positioning | qml6-module-qtpositioning | apt |
| qt6-quicktimeline | qml6-module-qtquick-timeline | apt |
| qt6-sensors | qml6-module-qtsensors | apt |
| qt6-tools | qdbus-qt6 | apt |
| qt6-translations | qt6-translations-l10n | apt |
| qt6-virtualkeyboard | qt6-virtualkeyboard-plugin, qml6-module-qtquick-virtualkeyboard | apt |
| kirigami | qml6-module-org-kde-kirigami | apt |
| kdialog | kdialog | apt |
| syntax-highlighting | qml6-module-org-kde-syntaxhighlighting | apt |
| (part of Arch's qt6-declarative) | qml6-module-qtquick{,-layouts,-controls,-templates,-effects,-shapes,-window}, qml6-module-qtqml{,-models,-workerscript}, qml6-module-qtcore, qml6-module-qt-labs-{folderlistmodel,synchronizer} | apt |
| makedepends cli11, ninja, qt6-shadertools, spirv-tools, vulkan-headers, wayland-protocols | libcli11-dev, ninja-build, qt6-shadertools-dev, spirv-tools, libvulkan-dev, wayland-protocols | apt |
| (PAM, polkit services) | libpam0g-dev, libpolkit-agent-1-dev, libglib2.0-dev | apt |

quickshell links Qt private API: after an apt upgrade of Qt, rerun `deps.sh`; it notices the new
Qt version and rebuilds quickshell and Darkly.

## screencapture

| Arch | Ubuntu | How |
|---|---|---|
| hyprshot | Hyprshot 1.3.0 script to `/usr/local/bin` | release |
| slurp, swappy, wf-recorder | same names | apt |
| tesseract, tesseract-data-eng | tesseract-ocr, tesseract-ocr-eng | apt |
| (hyprshot and the config) | grim, libnotify-bin, ffmpeg | apt |

## toolkit

| Arch | Ubuntu | How |
|---|---|---|
| upower, wtype, ydotool | same names | apt |

Ubuntu's ydotool ships `/usr/lib/systemd/user/ydotool.service` (end-4's setup step enables
it); `deps.sh` only adds one if a future package drops it.

## widgets

| Arch | Ubuntu | How |
|---|---|---|
| fuzzel, imagemagick, hypridle, hyprlock, hyprpicker, translate-shell, wlogout | same names | apt (hypr* from the ppa on 26.04) |
| glib2 | libglib2.0-bin | apt |
| songrec | songrec | ppa:marin-m/songrec (upstream author) |
| libqalculate | qalc | apt |

## bibata-modern-classic-bin

| Arch | Ubuntu | How |
|---|---|---|
| Bibata Modern Classic 2.0.6 | Bibata Modern Classic 2.0.7 to `/usr/share/icons` | release |

## Missing or different

- ttf-twemoji: no packaged twemoji font; Noto Color Emoji replaces it.
- mpvpaper (video wallpapers; Fedora installs it, Arch lists it nowhere): not in Ubuntu, not installed.
- Darkly is built without its KWin window decoration (not used under Hyprland).
- 26.04: the PPA only keeps its newest Hyprland, so the version cannot be pinned there
  (0.57.2 at the time of writing, newer than the 0.56.2 of 26.10).
- `QtQuick.Controls.FluentWinUI3`: Ubuntu's qml6-module-qtquick-controls does not ship this
  style, and end-4's `shell.qml` always loads the "waffle" family that imports it, so without it
  the whole bar fails to load. deps.sh installs a stub module that maps it to the Basic style
  (container test 2026-11-13: the config then loads with exactly end-4's own warnings).
- Hyprland in Ubuntu carries `cap_sys_nice` as a file capability; inside Docker (default
  capability set) running `/usr/bin/Hyprland` fails with "Operation not permitted". Not an
  issue on a real install.

## Running end-4's setup after deps.sh

end-4's setup script maps Ubuntu (`ID_LIKE=debian`) to its unsupported Nix path. With
`--skip-alldeps` that still breaks two things: the Python venv step calls `nix-shell` and
installs nothing, and the files step installs `dots-extra/via-nix/hypridle.conf` (swaylock,
pre-Lua dispatch syntax) instead of the normal one; it also skips enabling the ydotool user
service. end-4's `sdata/lib/dist-determine.sh` honours an `os-release` file at the repo root, so
this makes it take the Arch path without patching anything (the Arch dependency step is skipped):

    printf 'ID=ubuntu\nID_LIKE=arch\n' > dots-hyprland/os-release
    yes i | ./setup install --skip-alldeps --skip-allgreeting -f

`-f` removes the confirmations; `yes i` answers "ignore" if a command fails (end-4's `x` helper
otherwise loops on "repeat" when stdin is not a terminal). Tested in containers on 26.04 and
26.10: exit 0, the venv imports gi, cairo, PIL, cv2, numpy, materialyoucolor and pywayland, and
the normal hypridle.conf is installed.
