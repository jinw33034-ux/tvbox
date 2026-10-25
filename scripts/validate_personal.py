#!/usr/bin/env python3
"""Python 3.10+, standard library only. Never executes referenced plugins."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
from urllib.request import Request, urlopen

SECRET_KEY = re.compile(r"^(cookie|authorization|password|passwd|token|access_token|refresh_token|api[_-]?key|secret|sk)$", re.I)
SECRET_VALUE = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+\S+", re.I)

def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON member: ' + key)
        result[key] = value
    return result

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=strict_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON number')))

def validate(config, root):
    errors, warnings, dependencies, urls = [], [], set(), set()
    root = root.resolve()
    if not isinstance(config, dict):
        return ['root must be an object'], [], [], []
    for group, identity, fields in [('sites', 'key', ('key', 'name', 'api')),
                                    ('lives', 'name', ('name', 'url')),
                                    ('parses', 'name', ('name', 'url'))]:
        items = config.get(group)
        if not isinstance(items, list):
            errors.append(group + ' must be an array')
            continue
        seen, names = set(), set()
        for i, item in enumerate(items):
            where = f'{group}[{i}]'
            if not isinstance(item, dict):
                errors.append(where + ' must be an object')
                continue
            for field in fields:
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(where + '.' + field + ' must be a nonempty string')
            key = item.get(identity)
            if isinstance(key, str):
                if key in seen:
                    errors.append(where + ' has duplicate ' + identity)
                seen.add(key)
            name = item.get('name')
            if isinstance(name, str):
                if name in names:
                    errors.append(where + ' has duplicate display name')
                names.add(name)
            if type(item.get('type')) is not int or item['type'] not in (0, 1, 2, 3, 4):
                errors.append(where + '.type must be an integer in 0..4')
            for flag in ('searchable', 'quickSearch', 'filterable', 'changeable'):
                if flag in item and (type(item[flag]) is not int or item[flag] not in (0, 1)):
                    errors.append(where + '.' + flag + ' must be 0 or 1')
    if 'flags' in config and (not isinstance(config['flags'], list) or
                             any(not isinstance(x, str) for x in config['flags'])):
        errors.append('flags must be a string array')
    for field in ('spider', 'wallpaper'):
        if field in config and not isinstance(config[field], str):
            errors.append(field + ' must be a string')
    sites = config.get('sites') if isinstance(config.get('sites'), list) else []
    if any(isinstance(x, dict) and str(x.get('api', '')).startswith('csp_')
           for x in sites) and not config.get('spider'):
        errors.append('csp_ sites require an explicitly audited spider')

    def walk(value, where='$'):
        if isinstance(value, dict):
            for key, child in value.items():
                if SECRET_KEY.fullmatch(key) and child:
                    errors.append(where + '.' + key + ': potential secret (value redacted)')
                walk(child, where + '.' + key)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, f'{where}[{i}]')
        elif isinstance(value, str):
            if SECRET_VALUE.search(value):
                errors.append(where + ': secret pattern (value redacted)')
            ref, sep, digest = value.partition(';md5;')
            if sep and not re.fullmatch('[0-9a-fA-F]{32}', digest):
                errors.append(where + ': malformed MD5')
            if ref.startswith('./'):
                # Exact case matters on GitHub Raw, even on Windows.
                decoded = unquote(urlsplit(ref).path)
                target = (root / decoded).resolve()
                if not target.is_relative_to(root):
                    errors.append(where + ': dependency escapes repository')
                    return
                current = root
                try:
                    for part in Path(decoded).parts:
                        if part == '.':
                            continue
                        if part not in {x.name for x in current.iterdir()}:
                            raise FileNotFoundError
                        current = current / part
                    if not target.is_file():
                        raise FileNotFoundError
                    dependencies.add(target.relative_to(root).as_posix())
                    if sep and re.fullmatch('[0-9a-fA-F]{32}', digest):
                        if hashlib.md5(target.read_bytes()).hexdigest() != digest.lower():
                            errors.append(where + ': MD5 mismatch')
                except OSError:
                    errors.append(where + ': missing or wrong-case local dependency')
            elif ref.startswith(('http://', 'https://')):
                try:
                    parsed = urlsplit(ref)
                    if not parsed.hostname:
                        raise ValueError
                    if parsed.username or parsed.password or re.search(
                            r'(?:^|&)(?:token|access_token|api_key|password|auth|key|secret)=', parsed.query, re.I):
                        errors.append(where + ': credential in URL (redacted)')
                    else:
                        urls.add(ref)
                    if sep:
                        warnings.append(where + ': remote MD5 is not checked; vendor and audit the file locally')
                except ValueError:
                    errors.append(where + ': invalid URL')
            elif ref.startswith(('../', '/', 'file:', 'http:', 'https:')) or re.match(r'^[A-Za-z]:[\\/]', ref):
                errors.append(where + ': unsupported or unsafe reference')
            elif re.search(r'\.(?:jar|js|py|json|m3u|txt)(?:[?#].*)?$', ref, re.I):
                errors.append(where + ': file references must use ./ or HTTPS')
    walk(config)
    if not any(config.get(x) for x in ('sites', 'lives', 'parses')):
        warnings.append('EMPTY BASELINE: no content sources; playback is not available until authorized sources are added')
    return errors, warnings, sorted(dependencies), sorted(urls)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'personal.json')
    parser.add_argument('--root', type=Path, help='repository root (default: config directory)')
    parser.add_argument('--network', action='store_true', help='opt-in bounded URL probes; never executes plugins')
    parser.add_argument('--max-urls', type=int, default=10)
    parser.add_argument('--timeout', type=float, default=8)
    args = parser.parse_args()
    if not 1 <= args.max_urls <= 25 or not 0 < args.timeout <= 30:
        parser.error('max-urls must be 1..25; timeout must be >0 and <=30')
    try:
        config = load(args.config)
        errors, warnings, deps, urls = validate(config, args.root or args.config.parent)
    except (OSError, ValueError, TypeError) as exc:
        print('FAIL: unable to parse configuration (' + type(exc).__name__ + ')')
        return 1
    for message in warnings:
        print('WARN:', message)
    for message in errors:
        print('ERROR:', message)
    print(f'Local direct dependencies: {len(deps)}; external URLs: {len(urls)}')
    for dep in deps:
        print('DEPENDENCY:', dep)
    # Do not transmit anything if static validation failed.
    if args.network and not errors:
        print(f'Network probes: {min(len(urls), args.max_urls)} of {len(urls)}; templates skipped')
        for i, url in enumerate(urls[:args.max_urls]):
            if '{' in url or '}' in url:
                print(f'URL #{i + 1}: SKIP template')
                continue
            try:
                req = Request(url, headers={'User-Agent': 'TVBox-Personal-Validator/1', 'Range': 'bytes=0-1023'})
                with urlopen(req, timeout=args.timeout) as response:
                    response.read(1024)
                    print(f'URL #{i + 1}: HTTP {response.status}')
            except Exception as exc:
                errors.append('network failure')
                print(f'URL #{i + 1}: FAIL ({type(exc).__name__}; URL redacted)')
    print('FAIL' if errors else 'PASS (static checks; not a playback or licensing certification)')
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
