import glob
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile

import setuptools
from setuptools.command.build_ext import build_ext

CMAKE_EXE = os.environ.get("CMAKE_EXE", shutil.which("cmake"))
SWIG_EXE = os.environ.get("SWIG_EXE", shutil.which("swig"))

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = tempfile.mkdtemp()
GDCM_SOURCE = os.path.join(CURRENT_DIR, "gdcm_src")
GDCM_MODULE = os.path.join(CURRENT_DIR, "_gdcm")

# See https://stackoverflow.com/a/50357801/115612
def get_libpython():
    v = sysconfig.get_config_vars()
    fpaths = [os.path.join(v[pv], v["LDLIBRARY"]) for pv in ("LIBDIR", "LIBPL")]
    for fpath in fpaths:
        if os.path.exists(fpath):
            return fpath
    return ""


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
            libpython = get_libpython()
            if not libpython:
                libpython = sys.executable

            output_dir = os.path.abspath(
                os.path.dirname(self.get_ext_fullpath(ext.name))
            )

            subprocess.check_call(
                [
                    CMAKE_EXE,
                    "-GNinja",
                    "-DCMAKE_BUILD_TYPE:STRING=Release",
                    "-DGDCM_BUILD_APPLICATIONS=OFF",
                    "-DGDCM_DOCUMENTATION=OFF",
                    "-DGDCM_BUILD_SHARED_LIBS=ON",
                    "-DGDCM_WRAP_PYTHON=ON",
                    "-DGDCM_BUILD_DOCBOOK_MANPAGES:BOOL=OFF",
                    "-DPYTHON_EXECUTABLE=%s" % sys.executable,
                    "-DPYTHON_INCLUDE_DIR=%s" % sysconfig.get_paths()["platinclude"],
                    "-DPYTHON_LIBRARY=%s" % libpython,
                    "-SWIG_EXECUTABLE=%s" % SWIG_EXE,
                    "-DEXECUTABLE_OUTPUT_PATH=%s" % output_dir,
                    "-DLIBRARY_OUTPUT_PATH=%s" % output_dir,
                    GDCM_SOURCE,
                ],
                cwd=BUILD_DIR,
            )

            subprocess.check_call([CMAKE_EXE, "--build", BUILD_DIR], cwd=BUILD_DIR)

            if sys.platform.startswith("linux"):
                for shared_lib in glob.glob(os.path.join(output_dir, "*.so")):
                    subprocess.check_call(
                        ["patchelf", "--set-rpath", "$ORIGIN", shared_lib]
                    )
            else:
                for shared_lib in glob.glob(os.path.join(output_dir, "*.so")):
                    subprocess.check_call(
                        ["patchelf", "--set-rpath", "@loader_path", shared_lib]
                    )
            shutil.rmtree(BUILD_DIR)
        else:
            super().build_extension(ext)


setuptools.setup(
    name="gdcm",
    version="3.0.7",
    author="Mathieu Malaterre",
    author_email="mathieu.malaterre@gmail.com",
    description="Grassroots DICOM runtime libraries",
    long_description="Grassroots DiCoM is a C++ library for DICOM medical files. It is automatically wrapped to python/C#/Java (using swig). It supports RAW,JPEG (lossy/lossless),J2K,JPEG-LS, RLE and deflated. It also comes with DICOM Part 3,6 & 7 of the standard as XML files.",
    url="https://github.com/malaterre/GDCM",
    license="BSD",
    py_modules=["gdcm",],
    packages=["_gdcm",],
    ext_package="_gdcm",
    ext_modules=[ConfiguredCMakeExtension("_gdcm", target="_gdcm"),],
    package_data={
        "_gdcm": [
            "*.py",
            "*.so.*",
            "_gdcm*.so",
            # Linux modules.
            "*-linux-gnu.so",
            # Unix shared libraries.
            "lib*.so*",
            # macOS modules.
            "*-darwin.so",
            # macOS shared libraries.
            "lib*.dylib*",
            # Windows modules.
            "*.pyd",
            # Windows shared libraries.
            "*.dll",
        ],
    },
    cmdclass={"build_ext": CMakeBuildExt,},
    # data_files =[(site_packages_path, ['gdcm.pth',])],
    include_package_data=True,
    #  distclass=BinaryDistribution,
    zip_safe=False,
    python_requires=">=3.6",
    platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache License 2.0",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
    ],
)
