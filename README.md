[![Python version](https://img.shields.io/pypi/pyversions/python-gdcm.svg)](https://img.shields.io/pypi/pyversions/python-gdcm.svg)
[![PyPI version](https://badge.fury.io/py/python-gdcm.svg)](https://badge.fury.io/py/python-gdcm)

# Python-GDCM

**Unofficial** [GDCM](http://gdcm.sourceforge.net/wiki/index.php/Main_Page) packages for Python 3 on Linux, Windows and MacOS (both Intel and Apple Silicon).

Grassroots DiCoM is a C++ library for [DICOM](https://www.dicomstandard.org/) medical files that can be wrapped for Python using [SWIG](http://www.swig.org/). It supports datasets encoded using native, JPEG, JPEG 2000, JPEG-LS, RLE and deflated transfer syntaxes. It also comes with Parts 3, 6 & 7 of the DICOM Standard as XML files.

## Installation

### Using pip

```bash
pip install -U python-gdcm
```

### From source

#### Install dependencies
- Compiler for you platform (GCC, Clang, MSVC)
- [CMake](https://cmake.org/)
- [SWIG](http://www.swig.org/)
- [patchelf](https://github.com/NixOS/patchelf) will also be needed on Linux
- [Git](https://git-scm.com/) to get the source code

#### Setup environment
If the `cmake` or `swig` executables aren't in `$PATH`, either add them or create  `CMAKE_EXE` and `SWIG_EXE` envars:
```bash
export CMAKE_EXE="path/to/cmake/executable"
export SWIG_EXE="path/to/swig/executable"
```

#### Clone source
```bash
git clone --recurse-submodules https://github.com/tfmoraes/python-gdcm
```

#### Build and install
```bash
# Note the trailing slash!
pip install python-gdcm/
```

#### Test installed package
```bash
python -c "import gdcm; print(gdcm.GDCM_VERSION)"
```
If you get a `ModuleNotFoundError: No module named '_gdcm.gdcmswig'` error then make sure your current working directory doesn't contain a `_gdcm` folder.

## Usage

### Reading a DICOM image file

```python
import gdcm
reader = gdcm.ImageReader()
reader.SetFileName("dicom_image_file.dcm")
ret = reader.Read()
if not ret:
    print("It was not possible to read your DICOM file")
```

### Other Examples

See here https://github.com/malaterre/GDCM/tree/master/Examples/Python
