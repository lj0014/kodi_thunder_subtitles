import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'resources' / 'lib'))
import thunder


class VFS(io.BytesIO):
    def size(self):
        return len(self.getvalue())

    def readBytes(self, length):
        # Simulate a network VFS returning partial reads.
        return bytearray(self.read(min(length, 4096)))


def response(data):
    result = Mock()
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    result.iter_content.return_value = [data]
    return result


class CIDTests(unittest.TestCase):
    def test_reference_hashes_and_boundary(self):
        for length in (1, 0xEFFF, 0xF000, 200000):
            data = bytes(i % 251 for i in range(length))
            sample = data if length < 0xF000 else data[:0x5000] + data[length // 3:length // 3 + 0x5000] + data[-0x5000:]
            self.assertEqual(thunder.cid_hash(VFS(data)), hashlib.sha1(sample).hexdigest().upper())

    def test_empty_unseekable_and_short_reads(self):
        for stream in (VFS(), Mock(size=lambda: 100, seek=lambda *args: -1), Mock(size=lambda: 100, seek=lambda *args: 0, readBytes=lambda n: b'')):
            with self.assertRaises(thunder.SubtitleError):
                thunder.cid_hash(stream)


class SearchTests(unittest.TestCase):
    @patch('thunder.requests.get')
    def test_combined_wrapper_returns_name_results_when_cid_empty(self, get):
        import json
        def request(url, **kwargs):
            if url == thunder.API_URL.format('A' * 40):
                return response(b'{"sublist":[]}')
            return response(json.dumps({'code': 0, 'data': [{'name': 'Spider-Man.2.2004.chs.srt',
                'url': 'https://subtitle.v.geilijiasu.com/spider.srt', 'languages': ['简体']}]}).encode())
        get.side_effect = request
        found = thunder.search_all_subtitles('A' * 40, ['Spider-Man.2.2004'])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['sname'], 'Spider-Man.2.2004.chs.srt')
        self.assertEqual(found[0]['origin'], '名称')

    @patch('thunder.requests.get')
    def test_filters_malformed_and_duplicate_records(self, get):
        get.return_value = response(b'{"sublist":[null,{}, {"surl":"file:///etc/passwd"}, {"surl":"https://example.com/a?x=1&y=2","sname":"test"}, {"surl":"https://example.com/a?x=1&y=2"}]}')
        self.assertEqual(thunder.search_subtitles('A' * 40), [{'surl': 'https://example.com/a?x=1&y=2', 'sname': 'test'}])
        self.assertEqual(get.call_args.kwargs['timeout'], thunder.TIMEOUT)

    @patch('thunder.requests.get')
    def test_damaged_utf8_metadata_preserves_download_link(self, get):
        get.return_value = response(b'{"sublist":[{"sname":"bad\xff.srt","surl":"https://example.com/a.srt"}]}')
        subtitles = thunder.search_subtitles('A' * 40, max_attempts=1)
        self.assertEqual(subtitles[0]['surl'], 'https://example.com/a.srt')
        self.assertEqual(subtitles[0]['sname'], 'bad.srt')

    @patch('thunder.requests.get')
    def test_gbk_name_is_decoded_before_bytes_are_lost(self, get):
        get.return_value = response(b'{"sublist":[{"sname":"' + '阿甘正传.简体.srt'.encode('gb18030') + b'","surl":"https://example.com/a.srt"}]}')
        subtitles = thunder.search_subtitles('A' * 40, max_attempts=1)
        self.assertEqual(subtitles[0]['sname'], '阿甘正传.简体.srt')

    @patch('thunder.requests.get')
    def test_failed_requests_are_bounded(self, get):
        get.side_effect = thunder.requests.Timeout()
        with self.assertRaises(thunder.SubtitleError):
            thunder.search_subtitles('A' * 40, max_attempts=100)
        self.assertEqual(get.call_count, 3)

    @patch('thunder.requests.get')
    def test_invalid_json_and_schema(self, get):
        for data in (b'not json', b'{}', b'{"sublist":null}', b'[]'):
            get.return_value = response(data)
            with self.assertRaises(thunder.SubtitleError):
                thunder.search_subtitles('A' * 40, max_attempts=1)

    @patch('thunder.requests.get')
    def test_valid_empty_list(self, get):
        get.return_value = response(b'{"sublist":[]}')
        self.assertEqual(thunder.search_subtitles('A' * 40), [])

    @patch('thunder.requests.get')
    def test_abort_stops_network(self, get):
        self.assertEqual(thunder.search_subtitles('A' * 40, monitor=Mock(abortRequested=lambda: True)), [])
        get.assert_not_called()


class SubtitleNameTests(unittest.TestCase):
    def test_damaged_annotations_in_screenshot(self):
        names = {
            '[��������(��ĩ��)].Forrest.Gump.1994.BluRay.srt': 'Forrest.Gump.1994.BluRay.srt',
            'Forrest Gump.1080i.dts(全�?)国英四音轨ts版.hdpop1.srt': 'Forrest Gump.1080i.dts国英四音轨ts版.hdpop1.srt',
            'Forrest.Gump.1994.1080p.BluRay.x264.DTS-ETRG.����.srt': 'Forrest.Gump.1994.1080p.BluRay.x264.DTS-ETRG.srt',
        }
        for original, expected in names.items():
            self.assertEqual(thunder.subtitle_name(original), expected)

    def test_valid_chinese_and_release_annotations_are_preserved(self):
        for name in ('阿甘正传（简体中文）.srt', '[中英双语].Forrest.Gump.1994[1080p].ass', 'Forrest Gump+中文.srt'):
            self.assertEqual(thunder.subtitle_name(name), name)

    def test_encoded_upload_paths_and_legacy_percent_encoding(self):
        self.assertEqual(thunder.subtitle_name('C%3A%5Csubs%5C%E9%98%BF%E7%94%98%E6%AD%A3%E4%BC%A0.srt'), '阿甘正传.srt')
        self.assertEqual(thunder.subtitle_name('%B0%A2%B8%CA%D5%FD%B4%AB.srt'), '阿甘正传.srt')

    def test_latin1_mojibake_and_fallbacks(self):
        damaged = '阿甘正传.srt'.encode('utf-8').decode('latin-1')
        self.assertEqual(thunder.subtitle_name(damaged), '阿甘正传.srt')
        for name in (None, '', '[����].srt', '\ufffd\ufffd'):
            self.assertEqual(thunder.subtitle_name(name, 'Subtitle 01'), 'Subtitle 01')


class DownloadTests(unittest.TestCase):
    @patch('thunder.requests.get')
    def test_signed_url_and_local_file(self, get):
        url = 'https://example.com/a.SRT?token=a+b==&name=x%20y'
        get.return_value = response(b'1\n00:00:01,000 --> 00:00:02,000\nhello\n')
        with tempfile.TemporaryDirectory() as directory:
            paths = thunder.download_subtitles(url, directory)
            self.assertEqual(Path(paths[0]).suffix, '.srt')
            self.assertIn(b'hello', Path(paths[0]).read_bytes())
        self.assertEqual(get.call_args.args[0], url)

    @patch('thunder.requests.get')
    def test_zip_selection_paths_stay_in_directory(self, get):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('../../escape.srt', 'hello')
            archive.writestr('C:\\escape.ass', 'world')
            archive.writestr('run.exe', 'bad')
        get.return_value = response(data.getvalue())
        with tempfile.TemporaryDirectory() as directory:
            paths = thunder.download_subtitles('https://example.com/a.zip', directory)
            self.assertEqual(len(paths), 2)
            self.assertTrue(all(Path(p).parent == Path(directory) for p in paths))

    @patch('thunder.requests.get')
    def test_empty_html_and_unsupported_archive(self, get):
        for data in (b'', b'<html>error', b'Rar!bad', b'PK\x03\x04broken'):
            get.return_value = response(data)
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(thunder.SubtitleError):
                thunder.download_subtitles('https://example.com/a', directory)

    def test_size_limit(self):
        with self.assertRaises(thunder.SubtitleError):
            thunder.read_response(response(b'abcd'), limit=3)

    def test_reject_non_http(self):
        with self.assertRaises(thunder.SubtitleError):
            thunder.download_subtitles('file:///etc/passwd', '.')

    def test_conversion_utf8_utf16_gb18030_and_traditional(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'subtitle.srt'
            for encoding in ('utf-8-sig', 'utf-16', 'gb18030'):
                original = '这是中文字幕测试，欢迎使用。\n' * 20
                path.write_bytes(original.encode(encoding))
                thunder.convert_encoding(str(path))
                self.assertEqual(path.read_text(encoding='utf-8'), original)
            path.write_text('汉语', encoding='utf-8')
            thunder.convert_encoding(str(path), '2')
            self.assertEqual(path.read_text(encoding='utf-8'), '漢語')
            thunder.convert_encoding(str(path), '1')
            self.assertEqual(path.read_text(encoding='utf-8'), '汉语')


if __name__ == '__main__':
    unittest.main()
