"""Run the official checks using a Kodi HTTPS mirror for repository metadata."""
import sys
from kodi_addon_checker import check_addon
from kodi_addon_checker.__main__ import main

# Checker 0.0.36 uses HTTP for mirrors.kodi.tv. Only the transport changes;
# all repository, schema, dependency and PR checks remain enabled. This is a
# mirror returned by mirrors.kodi.tv, with indexes for every checker branch.
check_addon.ROOT_URL = 'https://ftp.fau.de/xbmc/addons/{branch}/addons.xml.gz'

if __name__ == '__main__':
    if '--branch' not in sys.argv:
        sys.argv[1:1] = ['--branch', 'matrix', '--PR']
    if '--reporter' not in sys.argv:
        sys.argv[1:1] = ['--reporter', 'console', '--reporter', 'log']
    main()
