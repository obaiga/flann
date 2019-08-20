#!/usr/bin/env python
"""
An Ode to Python Packaging:

Oh Python Packaging, when will you get better?
You've already improved so much...
but, lets say, there's still a lot of room for improvement.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import skbuild as skb
import sys


def parse_long_description():
    # ONLY WORKS IN A SPECIFIC DIRECTORY
    candidates = ['README.rst']
    for fpath in candidates:
        if exists(fpath):
            return open(fpath, 'r').read()
    return ''


def parse_version(package):
    """
    Statically parse the version number from __init__.py

    CommandLine:
        python -c "import setup; print(setup.parse_version('vtool'))"
    """
    from os.path import dirname, join, exists
    import ast

    # Check if the package is a single-file or multi-file package
    _candiates = [
        join(dirname(__file__), package + '.py'),
        join(dirname(__file__), package, '__init__.py'),
    ]
    _found = [init_fpath for init_fpath in _candiates if exists(init_fpath)]
    if len(_found) > 0:
        init_fpath = _found[0]
    elif len(_found) > 1:
        raise Exception('parse_version found multiple init files')
    elif len(_found) == 0:
        raise Exception('Cannot find package init file')

    with open(init_fpath) as file_:
        sourcecode = file_.read()
    pt = ast.parse(sourcecode)
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == '__version__':
                    self.version = node.value.s
    visitor = VersionVisitor()
    visitor.visit(pt)
    return visitor.version


def parse_requirements(fname='requirements.txt'):
    """
    Parse the package dependencies listed in a requirements file but
    strips specific versioning information.

    TODO:
        perhaps use https://github.com/davidfischer/requirements-parser instead

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    from os.path import exists
    import re
    require_fpath = fname

    def parse_line(line):
        """
        Parse information from a line in a requirements text file
        """
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        elif line.startswith('-e '):
            info = {}
            info['package'] = line.split('#egg=')[1]
            yield info
        else:
            # Remove versioning from the package
            pat = '(' + '|'.join(['>=', '==', '>']) + ')'
            parts = re.split(pat, line, maxsplit=1)
            parts = [p.strip() for p in parts]

            info = {}
            info['package'] = parts[0]
            if len(parts) > 1:
                op, rest = parts[1:]
                if ';' in rest:
                    # Handle platform specific dependencies
                    # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                    version, platform_deps = map(str.strip, rest.split(';'))
                    info['platform_deps'] = platform_deps
                else:
                    version = rest  # NOQA
                info['version'] = (op, version)
            yield info

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    # This breaks on pip install, so check that it exists.
    packages = []
    if exists(require_fpath):
        for info in parse_require_file(require_fpath):
            package = info['package']
            if not sys.version.startswith('3.4'):
                # apparently package_deps are broken in 3.4
                platform_deps = info.get('platform_deps')
                if platform_deps is not None:
                    package += ';' + platform_deps
            packages.append(package)
    return packages


def parse_authors():
    """
    Parse the git authors of a repo

    Returns:
        List[str]: list of authors

    CommandLine:
        python -c "import skbuild_template; print(skbuild_template.parse_authors())"
    """
    try:
        import ubelt as ub
        info = ub.cmd('git shortlog -s')
        if info['ret'] != 0:
            print('info = {!r}'.format(info))
            raise Exception
    except Exception as ex:
        print('ex = {!r}'.format(ex))
        return []
    else:
        striped_lines = (l.strip() for l in info['out'].split('\n'))
        freq_authors = [line.split(None, 1) for line in striped_lines if line]
        freq_authors = sorted((int(f), a) for f, a in freq_authors)[::-1]
        # keep authors with uppercase letters
        authors = [a for f, a in freq_authors if a.lower() != a]
        return authors


try:
    class EmptyListWithLength(list):
        def __len__(self):
            return 1
except Exception:
    raise RuntimeError('FAILED TO ADD BUILD CONSTRUCTS')


def get_lib_ext():
    if sys.platform.startswith('win32'):
        ext = '.dll'
    elif sys.platform.startswith('darwin'):
        ext = '.dylib'
    elif sys.platform.startswith('linux'):
        ext = '.so'
    else:
        raise Exception('Unknown operating system: %s' % sys.platform)
    return ext


# TODO: Push for merger of PR adding templatable utilities to skb.utils
from setuptools import find_packages
skb.utils.find_packages = find_packages
skb.utils.parse_authors = parse_authors
skb.utils.parse_version = parse_version
skb.utils.parse_requirements = parse_requirements
skb.utils.EmptyListWithLength = EmptyListWithLength
skb.utils.get_lib_ext = get_lib_ext
skb.utils.parse_long_description = parse_long_description

_ = skb.utils.CLASSIFIER_STATUS_OPTIONS = {
    '1': 'Development Status :: 1 - Planning',
    '2': 'Development Status :: 2 - Pre-Alpha',
    '3': 'Development Status :: 3 - Alpha',
    '4': 'Development Status :: 4 - Beta',
    '5': 'Development Status :: 5 - Production/Stable',
    '6': 'Development Status :: 6 - Mature',
    '7': 'Development Status :: 7 - Inactive',
}
_.update({
    'planning': _['1'],
    'pre-alpha': _['2'],
    'alpha': _['3'],
    'beta': _['4'],
    'stable': _['5'],
    'mature': _['6'],
    'inactive': _['7'],
})

# https://pypi.python.org/pypi?%3Aaction=list_classifiers
_ = skb.utils.CLASSIFIER_LICENSE_OPTIONS = {
    'apache': 'License :: OSI Approved :: Apache Software License',
    'bsd': 'License :: OSI Approved :: BSD License',
    'lgpl': 'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
    'gpl': 'License :: OSI Approved :: GNU General Public License (GPL)',
}
del _


TEMPLATE = r"""
Example
-------
import os
import skbuild as skb
NAME = '{NAME}'
AUTHORS = ['{PRIMARY}'] + sorted(skb.utils.parse_authors())
AUTHOR_EMAIL = '{EMAIL}'
URL = '{URL}'
LICENCE = '{LICENCE}'
DESCRIPTION = '{DESCRIPTION}'


KWARGS = dict(
    ext_modules=skb.utils.EmptyListWithLength(),  # hack for including ctypes bins
    name=NAME,
    version=VERSION,
    author=', '.join(AUTHORS),
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=skb.parse_long_description(),
    long_description_content_type='text/x-rst',
    url=URL,
    license=LICENCE,
    install_requires=skb.utils.parse_requirements('requirements/runtime.txt'),
    packages=skb.utils.find_packages(),
    extras_require={
        'all': skb.utils.parse_requirements('requirements.txt'),
        'tests': skb.utils.parse_requirements('requirements/tests.txt'),
        'build': skb.utils.parse_requirements('requirements/build.txt'),
        'runtime': skb.utils.parse_requirements('requirements/runtime.txt'),
    },
    include_package_data=True,
    package_data={
        NAME: (
            ['*{}'.format(skb.utils.get_lib_ext())] +
            (['Release\\*.dll'] if os.name == 'nt' else [])
        ),
    },
    # List of classifiers available at:
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # CLASSIFIERS = [
    # ],
)

if __name__ == '__main__':
    skb.setup(**KWARGS)
"""
