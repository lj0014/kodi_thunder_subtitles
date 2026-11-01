import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'resources/lib' if (ROOT / 'resources/lib').exists() else ROOT / 'plugins.v2/thundersubtitles'))
import name_search as ns


def clean(value):
    return str(value).replace('\\', '/').rsplit('/', 1)[-1]


def response(payload):
    r = Mock()
    r.__enter__ = Mock(return_value=r)
    r.__exit__ = Mock(return_value=False)
    r.iter_content.return_value = [json.dumps(payload).encode('utf-8')]
    return r


def record(name='Movie.srt', url='https://subtitle.v.geilijiasu.com/a.srt'):
    return {'name': name, 'url': url, 'language': '简体', 'rate': 4, 'votes': 3}


class NameSearchTests(unittest.TestCase):
    @patch.object(ns.requests, 'get')
    def test_real_api_fields_and_allowed_download_hosts(self, get):
        get.return_value = response({'code': 0, 'data': [
            {'name': '蜘蛛侠2.chs.eng.srt', 'url': 'http://subtitle.v.geilijiasu.com/a.srt',
             'languages': ['简体', '英语'], 'duration': 7805000, 'score': 0},
            {'name': 'bad', 'url': 'http://127.0.0.1/private'}, None]})
        found = ns.search_name('Spider-Man.2.2004', clean)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['language'], '简体、英语')
        self.assertEqual(found[0]['duration_ms'], 7805000)
        self.assertEqual(found[0]['origin'], '名称')
        self.assertTrue(found[0]['url'].startswith('https://'))
        self.assertEqual(get.call_args.kwargs['params'], {'name': 'Spider-Man.2.2004'})

    def test_duplicate_cid_and_name_url_retains_cid_ranking_and_adds_metadata(self):
        cid = record(url='http://subtitle.v.geilijiasu.com/a.srt')
        named = dict(record(), rate=0, votes=None, duration_ms=1000)
        found = ns.merge_records([('CID', [cid]), ('名称', [named, named])])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['origin'], 'CID＋名称')
        self.assertEqual(found[0]['rate'], 4)
        self.assertEqual(found[0]['duration_ms'], 1000)
        self.assertNotIn('origin', cid)

    @patch.object(ns, 'search_name', return_value=[record()])
    def test_old_api_empty_still_returns_name_candidates(self, name):
        found, failures = ns.combined_search(lambda: [], ['Movie.2004.mkv'], clean)
        self.assertEqual(found[0]['origin'], '名称')
        self.assertEqual(failures, ())

    def test_one_failed_source_preserves_the_other(self):
        for which in ('CID', '名称'):
            cid = Mock(return_value=[record()])
            with patch.object(ns, 'search_name', return_value=[record()]) as name:
                (cid if which == 'CID' else name).side_effect = ns.NameSearchError('offline')
                found, failures = ns.combined_search(cid, ['Movie'], clean)
            self.assertEqual(len(found), 1)
            self.assertEqual(failures, (which,))

    @patch.object(ns, 'search_name', side_effect=ns.NameSearchError('offline'))
    def test_all_sources_failed_is_an_error(self, name):
        with self.assertRaises(ns.NameSearchError):
            ns.combined_search(Mock(side_effect=OSError()), ['Movie'], clean)

    @patch.object(ns, 'search_name', return_value=[])
    def test_names_are_basename_only_deduplicated_and_bounded(self, name):
        ns.combined_search(None, ['C:\\private\\Movie.mkv', '/other/movie.mkv', 'Second', 'Third', 'Fourth'], clean)
        names = {c.args[0] for c in name.call_args_list}
        self.assertEqual(names, {'Movie.mkv', 'Second', 'Third'})

    @patch.object(ns.requests, 'get')
    def test_malformed_response_retries_at_most_twice(self, get):
        for payload in ([], {'code': 1, 'data': []}, {'code': 0, 'data': None}):
            get.reset_mock(); get.return_value = response(payload)
            with self.assertRaises(ns.NameSearchError): ns.search_name('Movie', clean)
            self.assertEqual(get.call_count, 2)

    @patch.object(ns.requests, 'get')
    def test_abort_prevents_network_requests(self, get):
        with self.assertRaises(ns.SearchCancelled): ns.combined_search(None, ['Movie'], clean, lambda: True)
        get.assert_not_called()


if __name__ == '__main__': unittest.main()
