#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
obspy.mseed installer

:copyright:
    The ObsPy Development Team (devs@obspy.org) & Chad Trabant
:license:
    GNU General Public License (GPL)
    
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
    02110-1301, USA.
"""

from distutils.ccompiler import get_default_compiler
from setuptools import find_packages, setup
from setuptools.extension import Extension
import os
import platform
import sys


VERSION = open(os.path.join("obspy", "mseed", "VERSION.txt")).read()


# hack to prevent build_ext from trying to append "init" to the export symbols
class finallist(list):
    def append(self, object):
        return

class MyExtension(Extension):
    def __init__(self, *args, **kwargs):
        Extension.__init__(self, *args, **kwargs)
        self.export_symbols = finallist(self.export_symbols)

macros = []
extra_link_args = []
if platform.system() == "Windows":
    macros.append(('WIN32', '1'))
    # disable some warnings for MSVC
    macros.append(('_CRT_SECURE_NO_WARNINGS', '1'))
    # Workaround Win32 + MinGW + Python 2.6 
    # :see: http://bugs.python.org/issue3308
    if 'mingw32' in sys.argv or \
       ('-c' not in sys.argv and get_default_compiler() == 'mingw32'):
        macros.append(('time_t', '__int64'))
        macros.append(('localtime', '_localtime64'))
        macros.append(('gmtime', '_gmtime64'))

src = os.path.join('obspy', 'mseed', 'src', 'libmseed') + os.sep
symbols = [s.strip() for s in open(src + 'libmseed.def', 'r').readlines()[2:]]
lib = MyExtension('libmseed',
                  define_macros=macros,
                  libraries=[],
                  sources=[src + 'fileutils.c', src + 'genutils.c',
                           src + 'gswap.c', src + 'lmplatform.c',
                           src + 'lookup.c', src + 'msrutils.c',
                           src + 'pack.c', src + 'packdata.c',
                           src + 'traceutils.c', src + 'tracelist.c',
                           src + 'unpack.c', src + 'unpackdata.c',
                           src + 'selection.c', src + 'logging.c'],
                  export_symbols=symbols,
                  extra_link_args=extra_link_args)


setup(
    name='obspy.mseed',
    version=VERSION,
    description="Read & write seismograms, Format MiniSeed",
    long_description="""
    obspy.mseed - Read & write seismograms, Format MiniSeed
    
    This module contains Python wrappers for libmseed - The MiniSeed
    library of Chad Trabant. Libmseed is written in C and interfaced via
    Python ctypes.

    For more information visit http://www.obspy.org.
    """,
    url='http://www.obspy.org',
    author='The ObsPy Development Team & Chad Trabant',
    author_email='devs@obspy.org',
    license='GNU General Public License (GPL)',
    platforms='OS Independent',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Geophysics',
    ],
    keywords=['ObsPy', 'seismology', 'MSEED', 'MiniSEED', 'waveform',
              'seismograms'],
    packages=find_packages(),
    namespace_packages=['obspy'],
    zip_safe=True,
    install_requires=[
        'setuptools',
        'obspy.core',
    ],
    download_url="https://svn.geophysik.uni-muenchen.de" + \
        "/svn/obspy/obspy.mseed/trunk#egg=obspy.mseed-dev",
    ext_package='obspy.mseed.lib',
    ext_modules=[lib],
    include_package_data=True,
    test_suite="obspy.mseed.tests.suite",
    entry_points="""
        [obspy.plugin.waveform]
        MSEED = obspy.mseed.core

        [obspy.plugin.waveform.MSEED]
        isFormat = obspy.mseed.core:isMSEED
        readFormat = obspy.mseed.core:readMSEED
        writeFormat = obspy.mseed.core:writeMSEED
    """,
)