import glob
import os
import platform
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
    version = "".join([str(x) for x in sys.version_info[:2]])
    fpaths = b.library_dirs
    for fpath in fpaths:
        fpath = os.path.join(fpath, f"python{version}.lib")
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
            print(
                subprocess.run(
                    [
                        "patchelf",
                        "--replace-needed",
                        needed,
                        f"$ORIGIN/{needed}",
                        shared_lib,
                    ]
                )
            )


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

            xml_folder = os.path.join(output_dir, "XML")
            os.mkdir(xml_folder)
            data_dict_folder = "gdcm_src/Source/DataDictionary/"
            info_obj_def_folder = "gdcm_src/Source/InformationObjectDefinition"
            for xml_file in glob.glob(os.path.join(data_dict_folder, "*.xml")):
                shutil.copy(xml_file, xml_folder)
            for xml_file in glob.glob(os.path.join(info_obj_def_folder, "*.xml")):
                shutil.copy(xml_file, xml_folder)

            my_env = os.environ.copy()
            if sys.platform == "darwin":
                try:
                    my_env["LDFLAGS"] += "-undefined dynamic_lookup -liconv"
                except KeyError:
                    my_env["LDFLAGS"] = "-undefined dynamic_lookup -liconv"

            if sys.platform == "win32":
                is_shared = "OFF"
            else:
                is_shared = "ON"

            cmake_args = [
                "-DCMAKE_CXX_STANDARD=11",
                "-DCMAKE_BUILD_TYPE:STRING=Release",
                "-DGDCM_BUILD_APPLICATIONS:BOOL=ON",
                "-DGDCM_DOCUMENTATION:BOOL=OFF",
                f"-DGDCM_BUILD_SHARED_LIBS:BOOL={is_shared}",
                "-DGDCM_WRAP_PYTHON:BOOL=ON",
                "-DGDCM_NO_PYTHON_LIBS_LINKING:BOOL=ON",
                "-DGDCM_BUILD_DOCBOOK_MANPAGES:BOOL=OFF",
                f"-DPYTHON_EXECUTABLE={sys.executable}",
                f"-DPYTHON_INCLUDE_DIR={sysconfig.get_paths()['platinclude']}",
                f"-DPYTHON_LIBRARY={libpython}",
                f"-DSWIG_EXECUTABLE={SWIG_EXE}",
                "-DGDCM_USE_SYSTEM_OPENSSL:BOOL=ON",
                f"-DEXECUTABLE_OUTPUT_PATH={output_dir}",
                f"-DLIBRARY_OUTPUT_PATH={output_dir}",
            ]

            # platform.machine() may not return 'arm64' for Apple M1 on older
            # Python versions, or if not running natively
            arch = os.environ.get("CMAKE_OSX_ARCHITECTURES", platform.machine())
            if sys.platform == "darwin" and arch == "arm64":
                cmake_args.append("-DCMAKE_OSX_ARCHITECTURES=arm64")

            # Based on opencv-python
            if "CMAKE_ARGS" in os.environ:
                import shlex

                cmake_args.extend(shlex.split(os.environ["CMAKE_ARGS"]))
                del shlex

            subprocess.check_call(
                [
                    CMAKE_EXE,
                    "-GNinja",
                ]
                + cmake_args
                + [
                    GDCM_SOURCE,
                ],
                env=my_env,
                cwd=BUILD_DIR,
            )

            subprocess.check_call(
                [
                    CMAKE_EXE,
                    "--build",
                    BUILD_DIR,
                ],
                env=my_env,
                cwd=BUILD_DIR,
            )

            if sys.platform.startswith("linux"):
                shared_libs = [
                    f
                    for f in glob.glob(os.path.join(output_dir, "*"))
                    if not (f.endswith(".py") or os.path.isdir(f))
                ]
                for shared_lib in shared_libs:
                    subprocess.check_call(
                        ["patchelf", "--set-rpath", "$ORIGIN", shared_lib]
                    )
            elif sys.platform == "darwin":
                shared_libs = [
                    f
                    for f in glob.glob(os.path.join(output_dir, "*"))
                    if not (f.endswith(".py") or "dylib" in f or os.path.isdir(f))
                ]
                for shared_lib in shared_libs:
                    subprocess.check_call(
                        ["install_name_tool", "-add_rpath", "@loader_path", shared_lib]
                    )
            shutil.rmtree(BUILD_DIR)
        else:
            super().build_extension(ext)


setuptools.setup(
    ext_package="_gdcm",
    ext_modules=[
        ConfiguredCMakeExtension("_gdcm", target="_gdcm"),
    ],
    cmdclass={
        "build_ext": CMakeBuildExt,
    },
)
