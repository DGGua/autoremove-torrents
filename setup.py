#-*- coding:UTF-8 -*-

from setuptools import setup, find_packages
from autoremovetorrents.version import __version__
from autoremovetorrents.compatibility.disk_usage_ import SUPPORT_SHUTIL
from autoremovetorrents.compatibility.open_ import open_
from autoremovetorrents.compatibility.pyyaml_version_ import PYYAML_VERSION

setup(name = 'autoremove-torrents-hnr',
    version = __version__,
    description = 'Automatically remove torrents according to your strategies with H&R check support.',
    long_description = open_('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers = [
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ], # Get classifiers from https://pypi.org/pypi?%3Aaction=list_classifiers
    keywords = 'python autoremove torrent',
    author = 'TJUPT',
    author_email = 'ptmaster@tjupt.org',
    url = 'https://github.com/tjupt/autoremove-torrents',
    license = 'MIT',
    packages = find_packages(),
    include_package_data = True,
    zip_safe = True,
    install_requires = [
        'deluge-client',
        'enum34',
        'ply',
        '' if SUPPORT_SHUTIL else 'psutil',
        PYYAML_VERSION,
        'requests',
    ],
    entry_points = {
        'console_scripts':[
            'autoremove-torrents = autoremovetorrents.main:main'
        ]
    }
)