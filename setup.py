from setuptools import setup, Extension
from setuptools.command.install import install as install_
from Cython.Distutils import build_ext
#from Cython.Build import cythonize
import numpy as np
# XXX h5py needs to be present to run setup.py. Can't be installed
# automatically?
import h5py
import os
import sys
from os import path
import shutil
import glob


COMPILE_FLAGS = ['-Ofast', '-march=native', '-std=c99',]
# Cython breaks strict aliasing rules.
COMPILE_FLAGS += ["-fno-strict-aliasing"]
#COMPILE_FLAGS = ['-Ofast', '-march=core2', '-std=c99', '-fopenmp']

MACROS = [
        ("HAVE_LZ4", None)
          ]


H5PLUGINS_DEFAULT = '/usr/local/hdf5/lib/plugin'

# Copied from h5py.
# TODO, figure out what the canonacal way to do this should be.
INCLUDE_DIRS = ['/usr/include/']
LIBRARY_DIRS = []
if sys.platform == 'darwin':
    # putting here both macports and homebrew paths will generate
    # "ld: warning: dir not found" at the linking phase 
    INCLUDE_DIRS += ['/opt/local/include'] # macports
    LIBRARY_DIRS += ['/opt/local/lib']     # macports
    INCLUDE_DIRS += ['/usr/local/include'] # homebrew
    LIBRARY_DIRS += ['/usr/local/lib']     # homebrew
elif sys.platform.startswith('freebsd'):
    INCLUDE_DIRS += ['/usr/local/include'] # homebrew
    LIBRARY_DIRS += ['/usr/local/lib']     # homebrew

INCLUDE_DIRS += ["internal-complibs/lz4-1.5.0/"]


lzf_plugin = Extension("plugin.libh5blosc",
                   ["hdf5/blosc_plugin.c", "hdf5/blosc_filter.c"]
                       + glob.glob("blosc/*.c")
                       + glob.glob("internal-complibs/lz4-1.5.0/*.c"),
                   depends=["hdf5/blosc_filter.h", "hdf5/blosc_plugin.h"]
                        + glob.glob("blosc/*.h"),
                   include_dirs = INCLUDE_DIRS + ["blosc/", "hdf5/"],
                   library_dirs = LIBRARY_DIRS,
                   libraries = ['hdf5', 'pthread'],
                   extra_compile_args=['-fPIC', '-g'] + COMPILE_FLAGS,
                   define_macros=MACROS,
                   )


H5VERSION = h5py.h5.get_libversion()
if (H5VERSION[0] < 1 or (H5VERSION[0] == 1
    and (H5VERSION[1] < 8 or (H5VERSION[1] == 8 and H5VERSION[2] < 11)))):
    H51811P = False
    EXTENSIONS = []
else:
    H51811P = True
    EXTENSIONS = [lzf_plugin]

#EXTENSIONS = cythonize(EXTENSIONS)


# Custom installation to include installing dynamic filters.
class install(install_):
    user_options = install_.user_options + [
        ('h5plugin', None, 'Install HDF5 filter plugins for use outside of python.'),
        ('h5plugin-dir=', None,
         'Where to install filter plugins. Default %s.' % H5PLUGINS_DEFAULT),
    ]
    def initialize_options(self):
        install_.initialize_options(self)
        self.h5plugin = False
        self.h5plugin_dir = H5PLUGINS_DEFAULT
    def finalize_options(self):
        install_.finalize_options(self)
        assert self.h5plugin or not self.h5plugin, "Invalid h5plugin argument."
        self.h5plugin_dir = path.abspath(self.h5plugin_dir)
    def run(self):
        install_.run(self)
        if self.h5plugin:
            if H51811P:
                pass
            else:
                print "HDF5 < 1.8.11, not installing filter plugins."
                return
            #from h5py import h5
            #h5version = h5.get_libversion()
            plugin_build = path.join(self.build_lib, "plugins")
            try:
                os.makedirs(self.h5plugin_dir)
            except OSError as e:
                if e.args[0] == 17:
                    # Directory already exists, this is fine.
                    pass
                else:
                    raise
            plugin_libs = glob.glob(path.join(plugin_build, "*"))
            for plugin_lib in plugin_libs:
                plugin_name = path.split(plugin_lib)[1]
                shutil.copy2(plugin_lib, path.join(self.h5plugin_dir, plugin_name))
            print "Installed HDF5 filter plugins to %s" % self.h5plugin_dir


# TODO hdf5 support should be an "extra". Figure out how to set this up.

setup(
    name = 'blosch5',

    packages = ['blosch5'],
    scripts=[],
    ext_modules = EXTENSIONS,
    cmdclass = {'build_ext': build_ext, 'install': install},
    #cmdclass = {'install': install},
    #install_requires = ['numpy', 'h5py', 'Cython', 'setuptools>=0.7'],
    install_requires = ['numpy', 'h5py', 'Cython'],
    #extras_require = {'H5':  ["h5py"]},
)

