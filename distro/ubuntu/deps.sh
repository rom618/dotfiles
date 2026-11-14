#!/bin/bash
set -euo pipefail

QS_COMMIT=9b0f339b19057f4731bf3b48293307d7ef241671
QS_REPOS=(https://git.outfoxxed.me/quickshell/quickshell.git https://github.com/quickshell-mirror/quickshell.git)
MICROTEX_COMMIT=0e3707f6dafebb121d98b53c64364d16fefe481d
MICROTEX_REPO=https://github.com/end-4/MicroTeX.git

DARKLY_VERSION=0.5.42
DARKLY_URL=https://github.com/Bali10050/Darkly/archive/refs/tags/v${DARKLY_VERSION}.tar.gz
DARKLY_SHA=96bdc7bca88de2071345b118e51f530123983e7b38256a160cd233f925e83732

MATUGEN_VERSION=4.2.0
MATUGEN_URL=https://github.com/InioX/matugen/releases/download/v${MATUGEN_VERSION}/matugen-${MATUGEN_VERSION}-x86_64.tar.gz
MATUGEN_SHA=a2e3b50e49ed6439999ba3c252ed04fabd98ee4e9d12e5e5dff2e66370569751

YQ_VERSION=4.54.1
YQ_URL=https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64
YQ_SHA=8e34fc298390875de416e6a4afcb8cabeceb25d9aa8506c1a2f9353cf702ea5f

UV_VERSION=0.13.6
UV_URL=https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz
UV_SHA=f29c3e94ffabd7e6f3ba521dba169a9b7ec12100bf3257087f0f24f6123f3645

HYPRSHOT_VERSION=1.3.0
HYPRSHOT_URL=https://github.com/Gustash/Hyprshot/archive/refs/tags/${HYPRSHOT_VERSION}.tar.gz
HYPRSHOT_SHA=315bdbe66ee473d811b9af8447bd32124e84d873396ef8ab5ac3f040294f6739

BIBATA_VERSION=2.0.7
BIBATA_URL=https://github.com/ful1e5/Bibata_Cursor/releases/download/v${BIBATA_VERSION}/Bibata-Modern-Classic.tar.xz
BIBATA_SHA=7d3495864e5bbef02f5e77de760b2905903b63c71495a78ef6306d19a3b556d8

ADW_GTK3_VERSION=6.5
ADW_GTK3_URL=https://github.com/lassekongo83/adw-gtk3/releases/download/v${ADW_GTK3_VERSION}/adw-gtk3v${ADW_GTK3_VERSION}.tar.xz
ADW_GTK3_SHA=a81780fadfc432be0fc3d89c4ebb41aa28e4f032d42c36f9789c57dd10cfa41c

BREEZE_PLUS_VERSION=6.28.0
BREEZE_PLUS_URL=https://github.com/mjkim0727/breeze-plus/archive/refs/tags/${BREEZE_PLUS_VERSION}.tar.gz
BREEZE_PLUS_SHA=2462371450507e224aa04404666919e16dcebc4ef120b1349f21cef316d21a73

NERD_FONTS_VERSION=3.5.1
JBM_NERD_URL=https://github.com/ryanoasis/nerd-fonts/releases/download/v${NERD_FONTS_VERSION}/JetBrainsMono.tar.xz
JBM_NERD_SHA=04d5e8f903693f9dd13e16f867e994834e681eb3c72c0d337a770dcda09010cf

SPACE_GROTESK_VERSION=2.0.0
SPACE_GROTESK_URL=https://github.com/floriankarsten/space-grotesk/releases/download/${SPACE_GROTESK_VERSION}/SpaceGrotesk-${SPACE_GROTESK_VERSION}.zip
SPACE_GROTESK_SHA=53b415577d4139248555300710bea0d268c7a5be67b93de53b716a9736cabffd

MSYM_COMMIT=10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7
MSYM_BASE=https://raw.githubusercontent.com/google/material-design-icons/${MSYM_COMMIT}/variablefont
RUBIK_COMMIT=e337a5f69a9bea30e58d05bd40184d79cc099628
RUBIK_BASE=https://raw.githubusercontent.com/googlefonts/rubik/${RUBIK_COMMIT}/fonts/variable
READEX_COMMIT=563dfbb36ae45e52ec50829b016ce724ac2fca70
READEX_BASE=https://raw.githubusercontent.com/ThomasJockin/readexpro/${READEX_COMMIT}/fonts/variable
GSANS_COMMIT=bd8f81ddb5c74d5c8897b36ad88b440266245103
GSANS_BASE=https://raw.githubusercontent.com/google/fonts/${GSANS_COMMIT}/ofl/googlesansflex

FONT_FILES=(
  "material-symbols|${MSYM_BASE}/MaterialSymbolsRounded%5BFILL,GRAD,opsz,wght%5D.ttf|MaterialSymbolsRounded.ttf|7e74e36533ccee12c2b81e75bfcf3ccf123d3bb7e7e46d65d94445f23db0c97c"
  "material-symbols|${MSYM_BASE}/MaterialSymbolsOutlined%5BFILL,GRAD,opsz,wght%5D.ttf|MaterialSymbolsOutlined.ttf|f7837ba8573d9a7a74931618ced8307bc81f96d49af296bf6c8052c772ed5282"
  "material-symbols|${MSYM_BASE}/MaterialSymbolsSharp%5BFILL,GRAD,opsz,wght%5D.ttf|MaterialSymbolsSharp.ttf|1fd72f99ec1f44ec461c74f99341c1dcfa8c140d7087a2902e747d4ee01e379b"
  "rubik|${RUBIK_BASE}/Rubik%5Bwght%5D.ttf|Rubik-VF.ttf|1b3a7437ba2af80e465e773ed60c5036d1ba6ace492d89046dbcf18fb31e4e88"
  "rubik|${RUBIK_BASE}/Rubik-Italic%5Bwght%5D.ttf|Rubik-Italic-VF.ttf|08c6c4018a5ada8b517407b46897e46cf6ebb106853fbd3e89addb51d3b59c62"
  "readex-pro|${READEX_BASE}/Readexpro%5BHEXP,wght%5D.ttf|ReadexPro-VF.ttf|268bba7e1e8f3b14d798b3fb0e40ebaa3fc39308c9ac0020e2faf6df181cc30e"
  "google-sans-flex|${GSANS_BASE}/GoogleSansFlex%5BROND,opsz,slnt,wdth,wght%5D.ttf|GoogleSansFlex-VF.ttf|a9ac770798857d5e8ac593ced42b22e40a7c08cec98319f92b0eccc2783a77ba"
)

PPA_HYPRLAND_FPR=A54D23B62FF3FCC76EFF71E8FDBAAA1CF0CCF48E
PPA_SONGREC_FPR=86A389B4B401FAB17A0168506888550B2FC77D09

PREFIX=/usr/local
FONT_DIR=/usr/local/share/fonts/illogical-impulse
STATE_DIR=/usr/local/share/illogical-impulse-ubuntu
WORK_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/illogical-impulse-ubuntu"
OS_RELEASE_FILE="${II_OS_RELEASE:-/etc/os-release}"

DRY_RUN=0
JOBS=$(nproc 2>/dev/null || echo 2)
WITH_MICROTEX=1

PKGS_BASE=(
  ca-certificates curl wget git gnupg xz-utils unzip zstd rsync bc coreutils jq ripgrep
  xdg-user-dirs xdg-utils cliphist cmake ninja-build pkg-config build-essential
)
PKGS_AUDIO=(cava pavucontrol-qt wireplumber pipewire-pulse libdbusmenu-gtk3-4 playerctl pulseaudio-utils sound-theme-freedesktop)
PKGS_BACKLIGHT=(geoclue-2.0 brightnessctl ddcutil)
PKGS_FONTS_THEMES=(breeze breeze-icon-theme eza fish fontconfig kitty starship fonts-noto-color-emoji)
PKGS_HYPRLAND=(hyprland hyprsunset hyprland-guiutils wl-clipboard)
PKGS_KDE=(bluedevil gnome-keyring network-manager plasma-nm polkit-kde-agent-1 dolphin systemsettings libkf6config-bin)
PKGS_PORTAL=(xdg-desktop-portal xdg-desktop-portal-kde xdg-desktop-portal-gtk xdg-desktop-portal-hyprland)
PKGS_PYTHON=(
  clang python3-dev libgtk-4-dev libadwaita-1-dev libsoup-3.0-dev libportal-gtk4-dev
  gobject-introspection libgirepository-2.0-dev libgirepository1.0-dev libcairo2-dev
)
PKGS_QS_RUNTIME=(
  libjemalloc2 qt6-wayland qt6-svg-plugins qt6-image-formats-plugins kimageformat6-plugins
  qt6-translations-l10n qt6-virtualkeyboard-plugin qdbus-qt6 kdialog
  qml6-module-qtquick qml6-module-qtquick-layouts qml6-module-qtquick-controls
  qml6-module-qtquick-templates qml6-module-qtquick-effects qml6-module-qtquick-shapes
  qml6-module-qtquick-window qml6-module-qtquick-timeline qml6-module-qtquick-virtualkeyboard
  qml6-module-qtqml qml6-module-qtqml-models qml6-module-qtqml-workerscript qml6-module-qtcore
  qml6-module-qt-labs-folderlistmodel qml6-module-qt-labs-synchronizer
  qml6-module-qt5compat-graphicaleffects qml6-module-qtmultimedia qml6-module-qtpositioning
  qml6-module-qtsensors qml6-module-org-kde-kirigami qml6-module-org-kde-syntaxhighlighting
)
PKGS_QS_BUILD=(
  qt6-base-dev qt6-base-private-dev qt6-declarative-dev qt6-declarative-private-dev
  qt6-shadertools-dev qt6-svg-dev qt6-wayland-dev libcli11-dev spirv-tools libvulkan-dev
  libwayland-dev wayland-protocols libjemalloc-dev libpipewire-0.3-dev libxcb1-dev libdrm-dev
  libgbm-dev libegl-dev libpam0g-dev libpolkit-agent-1-dev libglib2.0-dev
)
PKGS_SCREENCAPTURE=(grim slurp swappy tesseract-ocr tesseract-ocr-eng wf-recorder libnotify-bin ffmpeg)
PKGS_TOOLKIT=(upower wtype ydotool)
PKGS_WIDGETS=(fuzzel libglib2.0-bin imagemagick hypridle hyprlock hyprpicker songrec translate-shell wlogout qalc)
PKGS_DARKLY_BUILD=(
  extra-cmake-modules qt6-tools-dev libkf6config-dev libkf6coreaddons-dev libkf6guiaddons-dev
  libkf6i18n-dev libkf6iconthemes-dev libkf6windowsystem-dev libkf6colorscheme-dev
  libkf6kcmutils-dev libkirigami-dev frameworkintegration6
)
PKGS_MICROTEX_BUILD=(libtinyxml2-dev libgtkmm-3.0-dev libgtksourceviewmm-3.0-dev libcairomm-1.0-dev libfontconfig-dev)

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

show() {
  local out="" a
  for a in "$@"; do out+="$(printf '%q' "$a") "; done
  printf '    + %s\n' "${out% }"
}

plan() {
  printf '    + %s\n' "$*"
}

run() {
  show "$@"
  [ "$DRY_RUN" = 1 ] && return 0
  "$@"
}

root() {
  if [ "$(id -u)" -eq 0 ]; then run "$@"; else run sudo "$@"; fi
}

root_write() {
  local file=$1 content=$2
  if [ -f "$file" ] && [ "$(cat "$file")" = "$content" ]; then return 1; fi
  plan "write $file"
  [ "$DRY_RUN" = 1 ] && return 0
  if [ "$(id -u)" -eq 0 ]; then
    printf '%s\n' "$content" > "$file"
  else
    printf '%s\n' "$content" | sudo tee "$file" > /dev/null
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--jobs N] [--no-microtex]

Installs the dependencies of end-4's illogical-impulse (Hyprland + quickshell)
on Ubuntu 26.04 LTS and 26.10. Run it as your user; it calls sudo itself.

  --dry-run      print the plan, change nothing
  --jobs N       parallel build jobs (default: $JOBS)
  --no-microtex  skip building MicroTeX (LaTeX rendering in the sidebar)
  -h, --help     this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run|-n) DRY_RUN=1 ;;
    --jobs|-j) shift; JOBS=${1:?--jobs needs a number} ;;
    --no-microtex) WITH_MICROTEX=0 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
  shift
done

os_field() {
  local key=$1
  (
    set +u
    . "$OS_RELEASE_FILE"
    eval "printf '%s' \"\${$key:-}\""
  )
}

detect_release() {
  [ -r "$OS_RELEASE_FILE" ] || die "cannot read $OS_RELEASE_FILE"
  local id id_like codename version pretty
  id=$(os_field ID)
  id_like=$(os_field ID_LIKE)
  codename=$(os_field UBUNTU_CODENAME)
  [ -n "$codename" ] || codename=$(os_field VERSION_CODENAME)
  version=$(os_field VERSION_ID)
  pretty=$(os_field PRETTY_NAME)
  if [ "$id" != ubuntu ] && [[ " $id_like " != *" ubuntu "* ]]; then
    die "this installer is for Ubuntu; detected: ${pretty:-$id}"
  fi
  case "$codename" in
    resolute) RELEASE=26.04; HYPR_SOURCE=ppa ;;
    stonking) RELEASE=26.10; HYPR_SOURCE=archive ;;
    noble)
      die "${pretty:-Ubuntu 24.04} cannot run illogical-impulse: it ships Qt 6.4, quickshell needs Qt 6.6 or newer, and its Hyprland is far older than the 0.55+ this config needs. Upgrade to Ubuntu 26.04 LTS (or 26.10) first." ;;
    focal|jammy|mantic|lunar|kinetic|oracular|plucky|questing)
      die "${pretty:-Ubuntu $codename} is not supported: its Qt and Hyprland are too old for illogical-impulse. Supported: Ubuntu 26.04 LTS and 26.10." ;;
    *)
      if [ "$id" = ubuntu ] && [ -n "$version" ] && [ "$(printf '%s\n%s\n' 26.10 "$version" | sort -V | head -1)" = 26.10 ]; then
        RELEASE=$version; HYPR_SOURCE=archive
        warn "Ubuntu $version ($codename) is newer than the tested releases (26.04, 26.10); treating it like 26.10"
      else
        die "unsupported release: ${pretty:-$id $version} (codename '$codename'). Supported: Ubuntu 26.04 LTS and 26.10."
      fi ;;
  esac
  [ "$(uname -m)" = x86_64 ] || die "only x86_64 is supported (prebuilt matugen, yq and uv are pinned for x86_64)"
  say "Detected ${pretty:-Ubuntu $RELEASE} ($codename): Hyprland from $([ "$HYPR_SOURCE" = ppa ] && echo 'ppa:cppiber/hyprland' || echo 'the Ubuntu archive')"
}

preflight() {
  if [ "$(id -u)" -eq 0 ]; then
    warn "running as root: build caches go to $WORK_DIR; normally run this as your user"
  elif [ "$DRY_RUN" = 0 ]; then
    command -v sudo > /dev/null || die "sudo is required"
    sudo -v || die "sudo failed"
  fi
  run mkdir -p "$WORK_DIR/dl" "$WORK_DIR/src"
}

pkg_installed() {
  dpkg-query -W -f='${db:Status-Abbrev}' "$1" 2> /dev/null | grep -q '^ii'
}

APT_UPDATED=0
apt_update() {
  if [ "$APT_UPDATED" = 0 ] || [ "${1:-}" = force ]; then
    root env DEBIAN_FRONTEND=noninteractive apt-get update
    APT_UPDATED=1
  fi
}

apt_install() {
  local missing=() p
  for p in "$@"; do pkg_installed "$p" || missing+=("$p"); done
  if [ ${#missing[@]} -eq 0 ]; then
    note "all ${#} packages already installed"
    return 0
  fi
  note "${#missing[@]} to install: ${missing[*]}"
  apt_update
  root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
}

add_ppa() {
  local name=$1 owner=$2 archive=$3 fpr=$4 codename keyring sources tmp got
  codename=$(os_field UBUNTU_CODENAME)
  [ -n "$codename" ] || codename=$(os_field VERSION_CODENAME)
  keyring=/etc/apt/keyrings/$name.gpg
  sources=/etc/apt/sources.list.d/$name.sources
  if [ ! -f "$keyring" ]; then
    say "Adding signing key for ppa:$owner/$archive ($fpr)"
    if [ "$DRY_RUN" = 1 ]; then
      plan "curl keyserver.ubuntu.com 0x$fpr | gpg --dearmor > $keyring"
    else
      tmp=$(mktemp -d "$WORK_DIR/gpg.XXXXXX")
      curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$fpr" -o "$tmp/key.asc"
      gpg --homedir "$tmp" --batch --dearmor -o "$tmp/key.gpg" "$tmp/key.asc"
      got=$(gpg --homedir "$tmp" --batch --show-keys --with-colons "$tmp/key.gpg" | awk -F: '/^fpr/{print $10; exit}')
      [ "$got" = "$fpr" ] || { rm -rf "$tmp"; die "key fingerprint mismatch for ppa:$owner/$archive: got '$got'"; }
      root install -D -m 644 "$tmp/key.gpg" "$keyring"
      rm -rf "$tmp"
    fi
  fi
  if root_write "$sources" "Types: deb
URIs: https://ppa.launchpadcontent.net/$owner/$archive/ubuntu/
Suites: $codename
Components: main
Signed-By: $keyring"; then
    say "Added ppa:$owner/$archive"
    APT_UPDATED=0
  else
    note "ppa:$owner/$archive already configured"
  fi
}

fetch() {
  local url=$1 sum=$2 out=$WORK_DIR/dl/$3
  if [ -f "$out" ] && printf '%s  %s\n' "$sum" "$out" | sha256sum -c --quiet - > /dev/null 2>&1; then
    return 0
  fi
  plan "download $url"
  [ "$DRY_RUN" = 1 ] && return 0
  curl -fL --retry 3 --proto '=https' -s -S -o "$out.part" "$url"
  if ! printf '%s  %s\n' "$sum" "$out.part" | sha256sum -c --quiet - > /dev/null 2>&1; then
    rm -f "$out.part"
    die "sha256 mismatch for $url"
  fi
  mv "$out.part" "$out"
}

stamp_ok() {
  local name=$1 key=$2 path=${3:-}
  [ "$(cat "$STATE_DIR/$name" 2> /dev/null)" = "$key" ] || return 1
  [ -z "$path" ] || [ -e "$path" ]
}

stamp_set() {
  root mkdir -p "$STATE_DIR"
  root_write "$STATE_DIR/$1" "$2" || true
}

component() {
  local name=$1 key=$2 path=$3 fn=$4
  if stamp_ok "$name" "$key" "$path"; then
    note "$name $key: already installed"
    return 0
  fi
  say "Installing $name ($key)"
  "$fn"
  stamp_set "$name" "$key"
}

git_checkout() {
  local dir=$1 commit=$2; shift 2
  local url
  if [ ! -d "$dir/.git" ]; then
    for url in "$@"; do
      if run git clone --filter=blob:none "$url" "$dir"; then break; fi
      [ "$DRY_RUN" = 1 ] || rm -rf "$dir"
    done
    [ "$DRY_RUN" = 1 ] || [ -d "$dir/.git" ] || die "could not clone any of: $*"
  fi
  if [ "$DRY_RUN" = 0 ] && ! git -C "$dir" cat-file -e "$commit^{commit}" 2> /dev/null; then
    run git -C "$dir" fetch origin "$commit" || run git -C "$dir" fetch origin
  fi
  run git -C "$dir" checkout -q --detach "$commit"
  if [ "$DRY_RUN" = 0 ] && [ "$(git -C "$dir" rev-parse HEAD)" != "$commit" ]; then
    die "$dir is not at $commit"
  fi
}

qt_version() {
  dpkg-query -W -f='${Version}' qt6-base-dev 2> /dev/null || echo unknown
}

install_quickshell() {
  local src=$WORK_DIR/src/quickshell extra=()
  git_checkout "$src" "$QS_COMMIT" "${QS_REPOS[@]}"
  if [ "$HYPR_SOURCE" = ppa ] && ! pkg_installed libcpptrace-dev; then
    extra+=(-DVENDOR_CPPTRACE=ON)
  fi
  run rm -rf "$src/build"
  run cmake -GNinja -S "$src" -B "$src/build" \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DDISTRIBUTOR="dotfiles ubuntu deps.sh (illogical-impulse pin)" \
    -DDISTRIBUTOR_DEBUGINFO_AVAILABLE=NO \
    -DINSTALL_QML_PREFIX=lib/qt6/qml \
    "${extra[@]}"
  run cmake --build "$src/build" -j "$JOBS"
  root cmake --install "$src/build"
  root install -D -m 644 "$src/build/install_manifest.txt" "$STATE_DIR/quickshell.manifest"
}

qml_dir() {
  local d
  d=$(qtpaths6 -query QT_INSTALL_QML 2> /dev/null || true)
  [ -n "$d" ] || d=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/qt6/qml
  echo "$d"
}

install_fluent_stub() {
  local dir
  dir="$(qml_dir)/QtQuick/Controls/FluentWinUI3"
  printf 'module QtQuick.Controls.FluentWinUI3\nimport QtQuick.Controls.Basic auto\n' > "$WORK_DIR/fluent-qmldir"
  root install -D -m 644 "$WORK_DIR/fluent-qmldir" "$dir/qmldir"
}

install_darkly() {
  local src=$WORK_DIR/src/Darkly-$DARKLY_VERSION
  fetch "$DARKLY_URL" "$DARKLY_SHA" "darkly-$DARKLY_VERSION.tar.gz"
  run rm -rf "$src"
  run tar -xzf "$WORK_DIR/dl/darkly-$DARKLY_VERSION.tar.gz" -C "$WORK_DIR/src"
  run cmake -GNinja -S "$src" -B "$src/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DBUILD_TESTING=OFF \
    -DBUILD_QT5=OFF \
    -DBUILD_QT6=ON \
    -DWITH_DECORATIONS=OFF
  run cmake --build "$src/build" -j "$JOBS"
  root cmake --install "$src/build"
  root install -D -m 644 "$src/build/install_manifest.txt" "$STATE_DIR/darkly.manifest"
}

install_microtex() {
  local src=$WORK_DIR/src/MicroTeX
  git_checkout "$src" "$MICROTEX_COMMIT" "$MICROTEX_REPO"
  run rm -rf "$src/build"
  run cmake -GNinja -S "$src" -B "$src/build" -DCMAKE_BUILD_TYPE=Release
  run cmake --build "$src/build" -j "$JOBS"
  root rm -rf /opt/MicroTeX
  root install -D -m 755 "$src/build/LaTeX" /opt/MicroTeX/LaTeX
  root cp -r "$src/build/res" /opt/MicroTeX/
}

install_matugen() {
  local tmp=$WORK_DIR/src/matugen
  fetch "$MATUGEN_URL" "$MATUGEN_SHA" "matugen-$MATUGEN_VERSION.tar.gz"
  run rm -rf "$tmp"
  run mkdir -p "$tmp"
  run tar -xzf "$WORK_DIR/dl/matugen-$MATUGEN_VERSION.tar.gz" -C "$tmp"
  root install -D -m 755 "$tmp/matugen" "$PREFIX/bin/matugen"
}

install_yq() {
  fetch "$YQ_URL" "$YQ_SHA" "yq-$YQ_VERSION"
  root install -D -m 755 "$WORK_DIR/dl/yq-$YQ_VERSION" "$PREFIX/bin/yq"
}

install_uv() {
  local tmp=$WORK_DIR/src/uv
  fetch "$UV_URL" "$UV_SHA" "uv-$UV_VERSION.tar.gz"
  run rm -rf "$tmp"
  run mkdir -p "$tmp"
  run tar -xzf "$WORK_DIR/dl/uv-$UV_VERSION.tar.gz" -C "$tmp" --strip-components=1
  root install -D -m 755 "$tmp/uv" "$PREFIX/bin/uv"
  root install -D -m 755 "$tmp/uvx" "$PREFIX/bin/uvx"
}

install_hyprshot() {
  local tmp=$WORK_DIR/src/hyprshot
  fetch "$HYPRSHOT_URL" "$HYPRSHOT_SHA" "hyprshot-$HYPRSHOT_VERSION.tar.gz"
  run rm -rf "$tmp"
  run mkdir -p "$tmp"
  run tar -xzf "$WORK_DIR/dl/hyprshot-$HYPRSHOT_VERSION.tar.gz" -C "$tmp" --strip-components=1
  root install -D -m 755 "$tmp/hyprshot" "$PREFIX/bin/hyprshot"
}

install_bibata() {
  fetch "$BIBATA_URL" "$BIBATA_SHA" "bibata-$BIBATA_VERSION.tar.xz"
  root rm -rf /usr/share/icons/Bibata-Modern-Classic
  root tar -xJf "$WORK_DIR/dl/bibata-$BIBATA_VERSION.tar.xz" -C /usr/share/icons --no-same-owner
}

install_adw_gtk3() {
  fetch "$ADW_GTK3_URL" "$ADW_GTK3_SHA" "adw-gtk3-$ADW_GTK3_VERSION.tar.xz"
  root rm -rf /usr/share/themes/adw-gtk3 /usr/share/themes/adw-gtk3-dark
  root mkdir -p /usr/share/themes
  root tar -xJf "$WORK_DIR/dl/adw-gtk3-$ADW_GTK3_VERSION.tar.xz" -C /usr/share/themes --no-same-owner
}

install_breeze_plus() {
  local tmp=$WORK_DIR/src/breeze-plus
  fetch "$BREEZE_PLUS_URL" "$BREEZE_PLUS_SHA" "breeze-plus-$BREEZE_PLUS_VERSION.tar.gz"
  run rm -rf "$tmp"
  run mkdir -p "$tmp"
  run tar -xzf "$WORK_DIR/dl/breeze-plus-$BREEZE_PLUS_VERSION.tar.gz" -C "$tmp" --strip-components=1
  root rm -rf /usr/share/icons/breeze-plus /usr/share/icons/breeze-plus-dark
  root cp -r "$tmp/src/breeze-plus" "$tmp/src/breeze-plus-dark" /usr/share/icons/
  if command -v gtk-update-icon-cache > /dev/null; then
    root gtk-update-icon-cache -q -f /usr/share/icons/breeze-plus || true
    root gtk-update-icon-cache -q -f /usr/share/icons/breeze-plus-dark || true
  fi
}

install_fonts() {
  local entry family url file sum tmp
  for entry in "${FONT_FILES[@]}"; do
    IFS='|' read -r family url file sum <<< "$entry"
    fetch "$url" "$sum" "$file"
    root install -D -m 644 "$WORK_DIR/dl/$file" "$FONT_DIR/$family/$file"
  done
  fetch "$JBM_NERD_URL" "$JBM_NERD_SHA" "JetBrainsMonoNerd-$NERD_FONTS_VERSION.tar.xz"
  tmp=$WORK_DIR/src/jbm-nerd
  run rm -rf "$tmp"
  run mkdir -p "$tmp"
  run tar -xJf "$WORK_DIR/dl/JetBrainsMonoNerd-$NERD_FONTS_VERSION.tar.xz" -C "$tmp"
  root rm -rf "$FONT_DIR/jetbrains-mono-nerd"
  root mkdir -p "$FONT_DIR/jetbrains-mono-nerd"
  if [ "$DRY_RUN" = 1 ]; then
    plan "install $tmp/*.ttf $FONT_DIR/jetbrains-mono-nerd/"
  else
    root install -m 644 "$tmp"/*.ttf "$FONT_DIR/jetbrains-mono-nerd/"
  fi
  fetch "$SPACE_GROTESK_URL" "$SPACE_GROTESK_SHA" "SpaceGrotesk-$SPACE_GROTESK_VERSION.zip"
  tmp=$WORK_DIR/src/space-grotesk
  run rm -rf "$tmp"
  run unzip -q -o "$WORK_DIR/dl/SpaceGrotesk-$SPACE_GROTESK_VERSION.zip" -x '__MACOSX/*' -d "$tmp"
  root rm -rf "$FONT_DIR/space-grotesk"
  root mkdir -p "$FONT_DIR/space-grotesk"
  if [ "$DRY_RUN" = 1 ]; then
    plan "install $tmp/SpaceGrotesk-$SPACE_GROTESK_VERSION/otf/*.otf $FONT_DIR/space-grotesk/"
  else
    root install -m 644 "$tmp/SpaceGrotesk-$SPACE_GROTESK_VERSION"/otf/*.otf "$FONT_DIR/space-grotesk/"
  fi
  root fc-cache -f "$FONT_DIR"
}

fonts_key() {
  printf 'msym-%s rubik-%s readex-%s gsans-%s nerd-%s sg-%s' \
    "${MSYM_COMMIT:0:7}" "${RUBIK_COMMIT:0:7}" "${READEX_COMMIT:0:7}" "${GSANS_COMMIT:0:7}" \
    "$NERD_FONTS_VERSION" "$SPACE_GROTESK_VERSION"
}

install_ydotool_user_unit() {
  local unit=/usr/lib/systemd/user/ydotool.service
  if [ -e "$unit" ]; then
    note "ydotool user unit present"
    return 0
  fi
  if [ -e /usr/lib/systemd/system/ydotool.service ]; then
    root mkdir -p /usr/lib/systemd/user
    root ln -sf ../system/ydotool.service "$unit"
    return 0
  fi
  root mkdir -p /usr/lib/systemd/user
  root_write "$unit" "[Unit]
Description=Starts ydotoold service

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/ydotoold
ExecReload=/usr/bin/kill -HUP \$MAINPID
KillMode=process
TimeoutSec=180

[Install]
WantedBy=default.target" || true
}

verify() {
  local fail=0 v fam
  say "Verifying"
  if [ "$DRY_RUN" = 1 ]; then
    note "skipped in dry run"
    return 0
  fi
  v=$(dpkg-query -W -f='${Version}' hyprland 2> /dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
  if [ -z "$v" ] || [ ! -x /usr/bin/Hyprland ]; then
    warn "Hyprland is not installed"; fail=1
  elif [ "$(printf '%s\n%s\n' 0.55.0 "$v" | sort -V | head -1)" != 0.55.0 ]; then
    warn "Hyprland $v is older than 0.55 (the config uses the Lua format)"; fail=1
  else
    note "Hyprland $v"
  fi
  if v=$(qs --version 2> /dev/null | head -1); then note "$v"; else warn "quickshell (qs) does not run"; fail=1; fi
  for v in matugen yq uv hyprshot hypridle hyprlock hyprpicker hyprsunset songrec fuzzel cliphist wlogout; do
    command -v "$v" > /dev/null || { warn "$v missing"; fail=1; }
  done
  local families
  families=$(fc-list : family)
  for fam in "Material Symbols Rounded" "Material Symbols Outlined" "Rubik" "Readex Pro" "Space Grotesk" "JetBrainsMono Nerd Font" "Google Sans Flex"; do
    grep -qiF "$fam" <<< "$families" || { warn "font missing: $fam"; fail=1; }
  done
  [ "$WITH_MICROTEX" = 0 ] || [ -x /opt/MicroTeX/LaTeX ] || { warn "MicroTeX missing"; fail=1; }
  if [ "$fail" = 0 ]; then
    say "All dependencies are in place."
  else
    die "some dependencies are missing (see warnings above)"
  fi
}

main() {
  detect_release
  [ "$DRY_RUN" = 0 ] || say "Dry run: nothing will be changed"
  preflight

  say "Package sources"
  apt_install ca-certificates curl gnupg
  if [ "$HYPR_SOURCE" = ppa ]; then
    add_ppa illogical-impulse-hyprland cppiber hyprland "$PPA_HYPRLAND_FPR"
  fi
  add_ppa illogical-impulse-songrec marin-m songrec "$PPA_SONGREC_FPR"

  local pkgs=(
    "${PKGS_BASE[@]}" "${PKGS_AUDIO[@]}" "${PKGS_BACKLIGHT[@]}" "${PKGS_FONTS_THEMES[@]}"
    "${PKGS_HYPRLAND[@]}" "${PKGS_KDE[@]}" "${PKGS_PORTAL[@]}" "${PKGS_PYTHON[@]}"
    "${PKGS_QS_RUNTIME[@]}" "${PKGS_QS_BUILD[@]}" "${PKGS_SCREENCAPTURE[@]}"
    "${PKGS_TOOLKIT[@]}" "${PKGS_WIDGETS[@]}" "${PKGS_DARKLY_BUILD[@]}"
  )
  if [ "$HYPR_SOURCE" = ppa ]; then
    pkgs+=(libunwind-dev libdwarf-dev libzstd-dev)
  else
    pkgs+=(libcpptrace-dev uv)
  fi
  [ "$WITH_MICROTEX" = 0 ] || pkgs+=("${PKGS_MICROTEX_BUILD[@]}")
  say "Ubuntu packages"
  apt_install "${pkgs[@]}"

  say "Components not packaged in Ubuntu"
  component quickshell "$QS_COMMIT qt-$(qt_version)" "$PREFIX/bin/qs" install_quickshell
  component darkly "$DARKLY_VERSION qt-$(qt_version)" "$STATE_DIR/darkly.manifest" install_darkly
  component fluent-stub "1 qt-$(qt_version)" "$(qml_dir)/QtQuick/Controls/FluentWinUI3/qmldir" install_fluent_stub
  [ "$WITH_MICROTEX" = 0 ] || component microtex "$MICROTEX_COMMIT" /opt/MicroTeX/LaTeX install_microtex
  component matugen "$MATUGEN_VERSION" "$PREFIX/bin/matugen" install_matugen
  component yq "$YQ_VERSION" "$PREFIX/bin/yq" install_yq
  if [ "$HYPR_SOURCE" = ppa ]; then
    component uv "$UV_VERSION" "$PREFIX/bin/uv" install_uv
  fi
  component hyprshot "$HYPRSHOT_VERSION" "$PREFIX/bin/hyprshot" install_hyprshot
  component bibata "$BIBATA_VERSION" /usr/share/icons/Bibata-Modern-Classic install_bibata
  component adw-gtk3 "$ADW_GTK3_VERSION" /usr/share/themes/adw-gtk3 install_adw_gtk3
  component breeze-plus "$BREEZE_PLUS_VERSION" /usr/share/icons/breeze-plus install_breeze_plus
  component fonts "$(fonts_key)" "$FONT_DIR" install_fonts

  say "ydotool user service"
  install_ydotool_user_unit

  verify
}

main
