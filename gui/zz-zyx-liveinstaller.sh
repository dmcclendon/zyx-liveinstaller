#!/bin/sh
# Set up a launcher on the desktop for the live installer if we're on
# a live CD

if [ -b /dev/mapper/zyx-liveos-rw ]; then
    test -f ${XDG_CONFIG_HOME:-~/.config}/user-dirs.dirs && source ${XDG_CONFIG_HOME:-~/.config}/user-dirs.dirs
    cp /usr/share/applications/zyx-liveinstaller.desktop ${XDG_DESKTOP_DIR:-$HOME/Desktop}
fi

