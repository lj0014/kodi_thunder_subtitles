"""Exercise the actual entry point with Kodi modules replaced at the boundary."""
import importlib.util
import runpy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch
from urllib.parse import urlencode, parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'resources/lib'))


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.modules = {name: Mock() for name in ('xbmc', 'xbmcaddon', 'xbmcgui', 'xbmcplugin', 'xbmcvfs')}
        addon = self.modules['xbmcaddon'].Addon.return_value
        addon.getAddonInfo.side_effect = lambda key: {'path': str(ROOT), 'profile': self.temp.name, 'id': 'service.subtitles.thunder', 'name': 'Thunder'}.get(key, '')
        addon.getSetting.return_value = 'false'
        self.modules['xbmcvfs'].translatePath.side_effect = lambda path: path
        self.modules['xbmcvfs'].File = MagicMock()
        self.modules['xbmc'].Monitor.return_value.abortRequested.return_value = False
        self.patcher = patch.dict(sys.modules, self.modules)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        spec = importlib.util.spec_from_file_location('test_service_entry', ROOT / 'resources/lib/kodi_service.py')
        self.service = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.service)

    def test_entry_point_initialises_library_path_and_dispatches(self):
        entry_module = Mock()
        with patch.dict(sys.modules, {'kodi_service': entry_module}), patch.object(sys, 'path', sys.path[:]):
            runpy.run_path(str(ROOT / 'service.py'), run_name='__main__')
            self.assertEqual(Path(sys.path[0]), ROOT / 'resources/lib')
        entry_module.main.assert_called_once_with()

    def test_missing_action_finishes_without_crashing(self):
        self.service.main(['plugin://thunder', '1', ''])
        self.modules['xbmcplugin'].endOfDirectory.assert_called_once_with(1, succeeded=True)

    def test_signed_download_url_round_trip_and_persistence(self):
        url = 'https://example.com/a.srt?key=a+b==&name=x%20y'
        def download(received, directory, name):
            self.assertEqual(received, url)
            path = Path(directory) / 'a.srt'
            path.write_text('hello', encoding='utf-8')
            return [str(path)]
        with patch.object(self.service, 'download_subtitles', side_effect=download):
            self.service.main(['plugin://thunder', '1', '?' + urlencode({'action': 'download', 'filename': url})])
        destination = self.modules['xbmcplugin'].addDirectoryItem.call_args.args[1]
        self.assertEqual(Path(destination).read_text(), 'hello')

    def test_search_encodes_result_url_and_preserves_media_path(self):
        media = 'smb://server/a%20b.mkv'
        self.modules['xbmc'].Player.return_value.getPlayingFile.return_value = media
        url = 'https://example.com/a?key=a+b==&x=1'
        with patch.object(self.service, 'cid_hash', return_value='A' * 40), patch.object(self.service, 'search_all_subtitles', return_value=[{'surl': url, 'sname': '测试'}]):
            self.service.main(['plugin://thunder', '1', '?action=search'])
        self.modules['xbmcvfs'].File.assert_called_once_with(media, 'rb')
        query = self.modules['xbmcplugin'].addDirectoryItem.call_args.args[1]
        self.assertEqual(parse_qs(urlsplit(query).query)['filename'], [url])

    def test_failure_finishes_and_does_not_log_url(self):
        with patch.object(self.service, 'download_subtitles', side_effect=OSError('https://user:secret@server')):
            self.service.main(['plugin://thunder', '1', '?action=download&filename=x'])
        self.modules['xbmcplugin'].endOfDirectory.assert_called_once_with(1, succeeded=False)
        self.assertNotIn('secret', str(self.modules['xbmc'].log.call_args))

    def test_cancel_archive_selection_returns_no_file(self):
        self.modules['xbmcgui'].Dialog.return_value.select.return_value = -1
        with patch.object(self.service, 'download_subtitles', return_value=['one.srt', 'two.ass']):
            self.service.main(['plugin://thunder', '1', '?action=download&filename=x'])
        self.modules['xbmcplugin'].addDirectoryItem.assert_not_called()

    def test_unreadable_video_falls_back_to_basename_and_original_title(self):
        self.modules['xbmc'].Player.return_value.getPlayingFile.return_value = 'smb://user:password@server/films/Spider-Man.2.2004%20sample.mkv'
        labels = {'VideoPlayer.OriginalTitle': 'Spider-Man 2', 'VideoPlayer.Year': '2004'}
        self.modules['xbmc'].getInfoLabel.side_effect = lambda key: labels.get(key, '')
        self.modules['xbmcvfs'].File.side_effect = OSError('unreadable')
        with patch.object(self.service, 'search_all_subtitles', return_value=[]) as query:
            self.service.main(['plugin://thunder', '1', '?action=search'])
        self.assertIsNone(query.call_args.args[0])
        self.assertEqual(query.call_args.args[1], ['Spider-Man.2.2004 sample.mkv', 'Spider-Man 2 2004'])
        self.assertNotIn('password', str(query.call_args))
        self.modules['xbmcplugin'].endOfDirectory.assert_called_once_with(1, succeeded=True)

    def test_manual_search_uses_entered_name(self):
        self.modules['xbmc'].Player.return_value.getPlayingFile.return_value = ''
        with patch.object(self.service, 'search_all_subtitles', return_value=[]) as query:
            self.service.main(['plugin://thunder', '1', '?action=manualsearch&searchstring=Spider-Man.2.2004'])
        self.assertEqual(query.call_args.args[1], ['Spider-Man.2.2004'])

    def test_cancel_manual_input_returns_without_network(self):
        self.modules['xbmcgui'].Dialog.return_value.input.return_value = ''
        with patch.object(self.service, 'search_all_subtitles') as query:
            self.service.main(['plugin://thunder', '1', '?action=manualsearch'])
        query.assert_not_called()

    def test_name_only_result_does_not_claim_file_sync(self):
        self.modules['xbmc'].Player.return_value.getPlayingFile.return_value = 'Movie.mkv'
        with patch.object(self.service, 'cid_hash', return_value='A' * 40), patch.object(
                self.service, 'search_all_subtitles', return_value=[{'surl': 'https://subtitle.v.geilijiasu.com/a.srt', 'sname': 'name.srt', 'origin': '名称'}]):
            self.service.main(['plugin://thunder', '1', '?action=search'])
        self.modules['xbmcgui'].ListItem.return_value.setProperty.assert_any_call('sync', 'false')

    def test_episode_metadata_keeps_season_and_episode(self):
        labels = {'VideoPlayer.TVShowTitle': 'Example', 'VideoPlayer.Season': '1', 'VideoPlayer.Episode': '2'}
        self.modules['xbmc'].getInfoLabel.side_effect = lambda key: labels.get(key, '')
        names = self.service.search_names('smb://server/Example.S01E02.mkv')
        self.assertEqual(names, ['Example.S01E02.mkv', 'Example S01E02'])


if __name__ == '__main__':
    unittest.main()
