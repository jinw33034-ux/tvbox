import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from validate_personal import validate, load

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = dict(sites=[], lives=[], parses=[], flags=[])

    def errors(self, value=None):
        return validate(self.config if value is None else value, self.root)[0]

    def test_empty_baseline(self):
        self.assertFalse(self.errors())
        self.assertTrue(validate(self.config, self.root)[1])

    def test_wrong_structure(self):
        for value in ([], None, {'sites': None}, dict(self.config, sites='bad')):
            with self.subTest(value=value): self.assertTrue(validate(value, self.root)[0])

    def test_duplicate_keys_and_names(self):
        item = dict(key='a', name='A', type=1, api='https://example.org/api')
        self.config['sites'] = [item, copy.deepcopy(item)]
        self.assertGreaterEqual(len(self.errors()), 2)

    def test_bool_is_not_integer(self):
        self.config['sites'] = [dict(key='a', name='A', type=True, api='https://example.org/api')]
        self.assertTrue(self.errors())

    def test_nested_dependency(self):
        (self.root / 'a.json').write_text('{}')
        self.config['extra'] = {'ext': ['./a.json']}
        self.assertFalse(self.errors())
        self.config['extra']['ext'].append('./missing.json')
        self.assertTrue(self.errors())

    def test_case_sensitive_path(self):
        (self.root / 'A.js').write_text('')
        self.config['extra'] = './a.js'
        self.assertTrue(self.errors())

    def test_traversal(self):
        for path in ('./../outside.jar', './%2e%2e/outside.jar', '../outside.jar'):
            self.config['extra'] = path
            self.assertTrue(self.errors())

    def test_md5(self):
        (self.root / 'a.jar').write_bytes(b'fixture, not executable')
        digest = hashlib.md5((self.root / 'a.jar').read_bytes()).hexdigest()
        self.config['spider'] = './a.jar;md5;' + digest
        self.assertFalse(self.errors())
        for digest in ('0' * 32, 'wrong'):
            self.config['spider'] = './a.jar;md5;' + digest
            self.assertTrue(self.errors())

    def test_secret_redacted(self):
        self.config['extra'] = {'Cookie': 'private-test-value'}
        self.assertTrue(self.errors())
        self.assertNotIn('private-test-value', str(self.errors()))

    def test_url_credentials(self):
        for url in ('https://user:private@example.org/a', 'https://example.org/a?token=private'):
            self.config['extra'] = url
            self.assertTrue(self.errors())

    def test_csp_requires_spider(self):
        self.config['sites'] = [dict(key='a', name='A', type=3, api='csp_Test')]
        self.assertTrue(self.errors())

    def test_strict_json(self):
        path = self.root / 'config.json'
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{bad}'):
            path.write_text(raw)
            with self.assertRaises(ValueError): load(path)

if __name__ == '__main__':
    unittest.main()
