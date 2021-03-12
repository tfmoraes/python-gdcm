# Python-GDCM

**Unoficial** [GDCM](http://gdcm.sourceforge.net/wiki/index.php/Main_Page) packages for Python.

Grassroots DiCoM is a C++ library for DICOM medical files. It is automatically wrapped to python/C#/Java (using swig). It supports RAW,JPEG (lossy/lossless),J2K,JPEG-LS, RLE and deflated. It also comes with DICOM Part 3,6 & 7 of the standard as XML files.

## Installation

### Using PIP

```
pip install python-gdcm
```

### From source

- Install building dependencies
    - Compiler for you platform (GCC, Clang, MSVC)
    - Cmake (https://cmake.org/) 
    - Swig (http://www.swig.org/)
- Build and install python-gdcm
    - If cmake isn't in `$PATH` export the env variable `CMAKE_EXE` to its path
        ```
        $ export CMAKE_EXE=/CMAKE/PATH
        ```
    - If swig isn't in `$PATH` export the env variable `SWIG_EXE` to its path
        ```
        $ export SWIG_EXE=/SWIG/PATH
        ```
    - Build and install
        ```                                                                
        $ python setup.py install
        ```

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
