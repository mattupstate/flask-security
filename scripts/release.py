#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    make-release
    ~~~~~~~~~~~~

    Helper script that performs a release.  Does pretty much everything
    automatically for us.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

import os
import re
import sys
from datetime import date, datetime
from subprocess import PIPE, Popen

_date_clean_re = re.compile(r'(\d+)(st|nd|rd|th)')


def installed_libraries():
    return Popen(['pip', 'freeze'], stdout=PIPE).communicate()[0]


def has_library_installed(library):
    return library + '==' in installed_libraries()


def parse_changelog():
    with open('CHANGES') as f:
        lineiter = iter(f)
        for line in lineiter:
            match = re.search('^Version\s+(.*)', line.strip())

            if match is None:
                continue

            version = match.group(1).strip()

            if lineiter.next().count('-') != len(line.strip()):
                fail('Invalid hyphen count below version line: %s',
                     line.strip())

            while True:
                released = lineiter.next().strip()
                if released:
                    break

            match = re.search(r'Released (\w+\s+\d+\w+\s+\d+)', released)

            if match is None:
                fail('Could not find release date in version %s' % version)

            datestr = parse_date(match.group(1).strip())

            return version, datestr


def bump_version(version):
    try:
        parts = map(int, version.split('.'))
    except ValueError:
        fail('Current version is not numeric')
    parts[-1] += 1
    return '.'.join(map(str, parts))


def parse_date(string):
    string = _date_clean_re.sub(r'\1', string)
    return datetime.strptime(string, '%B %d %Y')


def set_filename_version(filename, version_number, pattern):
    changed = []

    def inject_version(match):
        before, old, after = match.groups()
        changed.append(True)
        return before + version_number + after

    with open(filename) as f:
        contents = re.sub(r"^(\s*%s\s*=\s*')(.+?)(')(?sm)" % pattern,
                          inject_version, f.read())

    if not changed:
        fail('Could not find %s in %s', pattern, filename)

    with open(filename, 'w') as f:
        f.write(contents)


def set_init_version(version):
    info('Setting __init__.py version to %s', version)
    set_filename_version('flask_security/__init__.py', version, '__version__')


def set_setup_version(version):
    info('Setting setup.py version to %s', version)
    set_filename_version('setup.py', version, 'version')


def set_docs_version(version):
    info('Setting docs/conf.py version to %s', version)
    set_filename_version('docs/conf.py', version, 'version')


def build_and_upload():
    Popen([sys.executable, 'setup.py', 'sdist',
           'build_sphinx', 'upload', 'upload_sphinx']).wait()


def fail(message, *args):
    print('Error: %s' % message % args, file=sys.stderr)
    sys.exit(1)


def info(message, *args):
    print(message % args, file=sys.stderr)


def get_git_tags():
    return set(Popen(['git', 'tag'], stdout=PIPE).communicate()[
               0].splitlines())


def git_is_clean():
    return Popen(['git', 'diff', '--quiet']).wait() == 0


def make_git_commit(message, *args):
    message = message % args
    Popen(['git', 'commit', '-am', message]).wait()


def make_git_tag(tag):
    info('Tagging "%s"', tag)
    Popen(['git', 'tag', '-a', tag, '-m', '%s release' % tag]).wait()
    Popen(['git', 'push', '--tags']).wait()


def update_version(version):
    for f in [set_init_version, set_setup_version, set_docs_version]:
        f(version)


def get_branches():
    return set(Popen(['git', 'branch'], stdout=PIPE).communicate()[
               0].splitlines())


def branch_is(branch):
    return '* ' + branch in get_branches()


def main():
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))

    rv = parse_changelog()

    if rv is None:
        fail('Could not parse changelog')

    version, release_date = rv

    tags = get_git_tags()

    for lib in ['Sphinx', 'Sphinx-PyPI-upload']:
        if not has_library_installed(lib):
            fail('Build requires that %s be installed', lib)

    if version in tags:
        fail('Version "%s" is already tagged', version)
    if release_date.date() != date.today():
        fail('Release date is not today')

    if not branch_is('master'):
        fail('You are not on the master branch')

    if not git_is_clean():
        fail('You have uncommitted changes in git')

    info('Releasing %s (release date %s)',
         version, release_date.strftime('%d/%m/%Y'))

    update_version(version)
    make_git_commit('Bump version number to %s', version)
    make_git_tag(version)
    build_and_upload()


if __name__ == '__main__':
    main()
