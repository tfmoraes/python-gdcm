import setuptools
import os
import sys
from setuptools.dist import Distribution
from setuptools.command.build_ext import build_ext
import shutil
import subprocess

import sysconfig
import glob



CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


CMAKE_EXE = os.environ.get('CMAKE_EXE', shutil.which('cmake'))
BUILD_DIR = os.environ.get('BUILD_DIR', "/tmp/bin")
GDCM_SOURCE =  os.environ.get('BUILD_DIR', "/tmp/src")
GDCM_MODULE = os.path.join(CURRENT_DIR, "_gdcm")
os.makedirs(GDCM_MODULE, exist_ok=True)

with open(os.path.join(GDCM_MODULE, '__init__.py'), 'w') as f:
    f.write('')

class ConfiguredCMakeExtension(setuptools.Extension):
    def __init__(self, name, target=None):
        super().__init__(name, sources=[])
        if target is None:
            self.target = name
        else:
            self.target = target


class CMakeBuildExt(build_ext):
    def build_extension(self, ext):
        if isinstance(ext, ConfiguredCMakeExtension):
            output_dir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
            subprocess.check_call([
                CMAKE_EXE,
                "-GNinja",
                "-DCMAKE_BUILD_TYPE:STRING=Release",
                "-DGDCM_WRAP_PYTHON=ON",
                "-DPYTHON_EXECUTABLE=%s" % sys.executable,
                "-DPYTHON_INCLUDE_DIR=%s" % sysconfig.get_paths()['platinclude'],
                "-DPYTHON_LIBRARY=%s" % sys.executable,
                "-DGDCM_BUILD_SHARED_LIBS=ON",
                "-DEXECUTABLE_OUTPUT_PATH=%s" % GDCM_MODULE,
                "-DLIBRARY_OUTPUT_PATH=%s" %  GDCM_MODULE,
                GDCM_SOURCE,
            ], cwd=BUILD_DIR)

            subprocess.check_call([
                "ninja-build",
            ], cwd=BUILD_DIR)

            print("GDCM_MODULE", GDCM_MODULE)
            #  for shared_lib in glob.glob(os.path.join(GDCM_MODULE, "*.so")):
                #  subprocess.check_call([
                    #  'patchelf',
                    #  '--set-rpath',
                    #  '$ORIGIN',
                    #  shared_lib
                #  ])
        else:
            super().build_extension(ext)


class BinaryDistribution(Distribution):
    #  def is_pure(self):
        #  return False
    def has_ext_modules(self):
        return True


def get_libs(folder):
    sh_files = []
    for f in os.listdir(folder):
        if not f.endswith('.py'):
            sh_files.append(f)

    print(sh_files)
    return sh_files

#  with open("README.md", "r") as fh:
    #  long_description = fh.read()


print(os.getcwd())
setuptools.setup(
    name="gdcm",
    version="3.0.7",
    author="Mathieu Malaterre",
    author_email="mathieu.malaterre@gmail.com",
    description="Grassroots DICOM runtime libraries",
    long_description="Grassroots DiCoM is a C++ library for DICOM medical files. It is automatically wrapped to python/C#/Java (using swig). It supports RAW,JPEG (lossy/lossless),J2K,JPEG-LS, RLE and deflated. It also comes with DICOM Part 3,6 & 7 of the standard as XML files.",
    url="https://github.com/malaterre/GDCM",
    license="BSD",
    py_modules = [
        'gdcm',
    ],
    packages=[
        '_gdcm',
    ],
    ext_package = '_gdcm',
    ext_modules = [
        ConfiguredCMakeExtension('_gdcm', target='_gdcm'),
    ],
    package_data={
        '_gdcm': [
            '*.py',
            '*.so',
            '_gdcm*.so',
            # Linux modules.
            '*-linux-gnu.so',
            # Unix shared libraries.
            'lib*.so*',
            # macOS modules.
            '*-darwin.so',
            # macOS shared libraries.
            'lib*.dylib*',
            # Windows modules.
            '*.pyd',
            # Windows shared libraries.
            '*.dll',
        ],
    },
    cmdclass={
        'build_ext': CMakeBuildExt,
    },
    #data_files =[(site_packages_path, ['gdcm.pth',])],
    include_package_data=True,
    #  distclass=BinaryDistribution,
    zip_safe=False,
    python_requires='>=3.6',
    platforms = ["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: Apache License 2.0',
            'Programming Language :: C',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: Implementation :: CPython',
            'Topic :: Scientific/Engineering',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Operating System :: MacOS',
        ],
)
