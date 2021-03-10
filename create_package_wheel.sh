#!/bin/sh

readonly gdcmroot="/gdcm"
readonly gdcmsrc="/tmp/src"
readonly gdcmbin="/tmp/bin"
readonly gdcmout="$gdcmroot/out"
readonly gdcmpy="$gdcmroot/_gdcm"
readonly cmake_ver="3.17.3"
readonly swig_ver="4.0.2"
readonly gdcm_ver="3.0.8"

mkdir -p "$gdcmout"

yum install -y gcc-c++ ninja-build pcre-devel

# Download and install cmake
cd /tmp
curl -OL "https://github.com/Kitware/CMake/releases/download/v$cmake_ver/cmake-$cmake_ver-Linux-x86_64.tar.gz"
mkdir -p /opt/cmake
tar --strip-components=1 -C /opt/cmake -xzf "cmake-$cmake_ver-Linux-x86_64.tar.gz"

# Download and install SWIG
cd /tmp
curl -OL "https://sourceforge.net/projects/swig/files/swig/swig-$swig_ver/swig-$swig_ver.tar.gz"
mkdir -p /tmp/swig
tar --strip-components=1 -C /tmp/swig -xzf "swig-$swig_ver.tar.gz"
cd /tmp/swig
./configure --with-python3=/opt/python/cp38-cp38/bin/python3
make
make install


# mkdir -p "$gdcmsrc"
# cd /tmp/
# curl -LO "https://github.com/malaterre/GDCM/archive/v$gdcm_ver.tar.gz"
# tar --strip-components=1 -C "$gdcmsrc" -xzf "v$gdcm_ver.tar.gz"

export PATH="/opt/cmake/bin:$PATH"

for pyver in 36 37 38 39; do
    suffix=""
    [ "$pyver" -le 37 ] && suffix="m"
    pyroot="/opt/python/cp$pyver-cp$pyver$suffix"
    cd "$gdcmroot"
    rm -rf build
    rm -rf gdcm.egg-info
    "$pyroot/bin/python" setup.py bdist_wheel
done

for i in $(find dist/ -name "*.whl"); do
    auditwheel addtag $i
    auditwheel repair $i
done
