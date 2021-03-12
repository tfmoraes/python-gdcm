import glob
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import typing

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

def get_libpython2():
    d = setuptools.Distribution()
    b = build_ext(d)
    b.finalize_options()
    fpaths = b.library_dirs
    for fpath in fpaths:
        fpath = os.path.join(fpath, "python%s.lib" % sys.version[:3].replace('.', ''))
        if os.path.exists(fpath):
            return fpath
    return ""

def get_needed(shared_lib: str):
    output = subprocess.run(
        ["patchelf", "--print-needed", shared_lib], capture_output=True
    )
    return output.stdout.decode("utf8").split("\n")


def relocate(shared_lib: str, shared_libs_names: typing.List[str]):
    for needed in get_needed(shared_lib):
        needed = os.path.basename(needed)
        if needed in shared_libs_names:
            print(subprocess.run(["patchelf", "--replace-needed", needed, f"$ORIGIN/{needed}", shared_lib,]))


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
            try:
                libpython = get_libpython()
            except KeyError:
                libpython = get_libpython2()
            if not libpython:
                libpython = sys.executable

            output_dir = os.path.abspath(
                os.path.dirname(self.get_ext_fullpath(ext.name))
            )

            my_env = os.environ.copy()
            if sys.platform == 'darwin':
                try:
                    my_env["LDFLAGS"] += "-undefined dynamic_lookup"
                except KeyError:
                    my_env["LDFLAGS"] = "-undefined dynamic_lookup"

            cmake_args = [
                "-DCMAKE_BUILD_TYPE:STRING=Release",
                "-DGDCM_BUILD_APPLICATIONS:BOOL=ON",
                "-DGDCM_DOCUMENTATION:BOOL=OFF",
                "-DGDCM_BUILD_SHARED_LIBS:BOOL=ON",
                "-DGDCM_WRAP_PYTHON:BOOL=ON",
                "-DGDCM_NO_PYTHON_LIBS_LINKING:BOOL=ON",
                "-DGDCM_BUILD_DOCBOOK_MANPAGES:BOOL=OFF",
                "-DPYTHON_EXECUTABLE=%s" % sys.executable,
                "-DPYTHON_INCLUDE_DIR=%s" % sysconfig.get_paths()["platinclude"],
                "-DPYTHON_LIBRARY=%s" % libpython,
                "-SWIG_EXECUTABLE=%s" % SWIG_EXE,
                "-DEXECUTABLE_OUTPUT_PATH=%s" % output_dir,
                "-DLIBRARY_OUTPUT_PATH=%s" % output_dir,
            ]

            subprocess.check_call(
                [CMAKE_EXE, "-GNinja", ] + cmake_args + [GDCM_SOURCE, ],
                env=my_env,
                cwd=BUILD_DIR,
            )

            subprocess.check_call(
                [CMAKE_EXE, "--build", BUILD_DIR, ],
                env=my_env,
                cwd=BUILD_DIR
            )

            if sys.platform.startswith("linux"):
                shared_libs = [f for f in glob.glob(os.path.join(output_dir, "*")) if not f.endswith(".py")]
                for shared_lib in shared_libs:
                    subprocess.check_call(
                        ["patchelf", "--set-rpath", "$ORIGIN", shared_lib]
                    )
            elif sys.platform == 'darwin':
                shared_libs = [f for f in glob.glob(os.path.join(output_dir, "*")) if not ( f.endswith(".py") or "dylib" in f)]
                for shared_lib in shared_libs:
                    subprocess.check_call(
                        ["install_name_tool", "-add_rpath", "@loader_path", shared_lib]
                    )
            shutil.rmtree(BUILD_DIR)
        else:
            super().build_extension(ext)


setuptools.setup(
    name="python-gdcm",
    version="3.0.8.1",
    author="Thiago Franco de Moraes",
    author_email="totonixsame@gmail.com",
    description="Grassroots DICOM runtime libraries",
    long_description=open("README.md", encoding="utf-8").read(),
    url="https://github.com/tfmoraes/python-gdcm/",
    license="BSD",
    py_modules=[
        "gdcm",
    ],
    packages=[
        "_gdcm",
    ],
    ext_package="_gdcm",
    ext_modules=[
        ConfiguredCMakeExtension("_gdcm", target="_gdcm"),
    ],
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
            # GDCM applications
            "*.exe",
            "gdcmanon",
            "gdcmconv",
            "gdcmdiff",
            "gdcmdump",
            "gdcmgendir",
            "gdcmimg",
            "gdcminfo",
            "gdcmpap3",
            "gdcmraw",
            "gdcmscanner",
            "gdcmscu",
            "gdcmtar",
            "gdcmxml",
        ],
    },
    scripts = [
        "scripts/gdcmanon",
        "scripts/gdcmconv",
        "scripts/gdcmdiff",
        "scripts/gdcmdump",
        "scripts/gdcmgendir",
        "scripts/gdcmimg",
        "scripts/gdcminfo",
        "scripts/gdcmpap3",
        "scripts/gdcmraw",
        "scripts/gdcmscanner",
        "scripts/gdcmscu",
        "scripts/gdcmtar",
        "scripts/gdcmxml",
    ],
    cmdclass={
        "build_ext": CMakeBuildExt,
    },
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
        "License :: OSI Approved :: Apache Software License",
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
