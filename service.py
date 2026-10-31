# -*- coding: utf-8 -*-
"""Kodi subtitle entry point (Kodi 19+, Python 3)."""
import os
import sys
import tempfile
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
sys.path.insert(0, xbmcvfs.translatePath(os.path.join(
    ADDON.getAddonInfo('path'), 'resources', 'lib')))
from thunder import SubtitleError, cid_hash, search_subtitles, download_subtitles


def notify(message_id):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo('name'),
                                ADDON.getLocalizedString(message_id),
                                xbmcgui.NOTIFICATION_INFO)


def search(handle):
    path = xbmc.Player().getPlayingFile()
    if path.startswith('stack://'):
        path = path[8:].split(' , ')[0]
    # Preserve percent escapes: the VFS owns URI decoding, including SMB URLs.
    with xbmcvfs.File(path, 'rb') as stream:
        cid = cid_hash(stream)
    subtitles = search_subtitles(cid, monitor=xbmc.Monitor())
    if not subtitles:
        notify(32010)
    for sub in subtitles:
        item = xbmcgui.ListItem(label='Chinese', label2=sub['sname'])
        item.setArt({'icon': '0', 'thumb': 'zh'})
        item.setProperty('sync', 'true')
        item.setProperty('hearing_imp', 'false')
        query = urlencode({'action': 'download', 'filename': sub['surl'],
                           'name': sub['sname']})
        xbmcplugin.addDirectoryItem(handle, 'plugin://{}/?{}'.format(
            ADDON.getAddonInfo('id'), query), item, False)


def download(handle, params):
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    os.makedirs(profile, exist_ok=True)
    # Each download owns its directory; searching never deletes an active subtitle.
    with tempfile.TemporaryDirectory(prefix='thunder-', dir=profile) as temp:
        paths = download_subtitles(params.get('filename', ''), temp,
                                   params.get('name', ''))
        if len(paths) > 1:
            choice = xbmcgui.Dialog().select(ADDON.getLocalizedString(32006),
                                             [os.path.basename(p) for p in paths])
            if choice < 0:
                return
            path = paths[choice]
        else:
            path = paths[0]
        if ADDON.getSetting('transUTF8') == 'true':
            from thunder import convert_encoding
            convert_encoding(path, ADDON.getSetting('transJianFan'))
        # Keep the chosen file available after the invocation returns.
        import shutil
        import uuid
        destination = os.path.join(profile, uuid.uuid4().hex + os.path.splitext(path)[1])
        shutil.copyfile(path, destination)
    item = xbmcgui.ListItem(label=destination)
    xbmcplugin.addDirectoryItem(handle, destination, item, False)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) < 2:
        return
    handle = int(argv[1])
    success = True
    try:
        params = dict(parse_qsl(argv[2].lstrip('?'), keep_blank_values=True)) if len(argv) > 2 else {}
        action = params.get('action')
        if action == 'search':
            search(handle)
        elif action == 'manualsearch':
            # Thunder's CID endpoint cannot search by title.
            notify(32011)
            search(handle)
        elif action == 'download':
            download(handle, params)
    except Exception as exc:
        success = False
        # Exception messages may contain media credentials or signed download URLs.
        xbmc.log('{}: {} ({})'.format(ADDON.getAddonInfo('id'),
                 'subtitle operation failed', type(exc).__name__), xbmc.LOGERROR)
        notify(exc.message_id if isinstance(exc, SubtitleError) else 32012)
    finally:
        xbmcplugin.endOfDirectory(handle, succeeded=success)


if __name__ == '__main__':
    main()
