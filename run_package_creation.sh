#!/bin/sh

readonly gdcmroot="/gdcm"
readonly gdcmsrc="$gdcmroot/src"
readonly gdcmout="$gdcmroot/out"

readonly baseimage="quay.io/pypa/manylinux2010_x86_64"
readonly container="gdcm-wheel"

mkdir -p "$PWD/dist"

docker pull "$baseimage"
docker run -it --rm --workdir="$gdcmroot" --name="$container" -v "$PWD:$gdcmroot" "$baseimage" /bin/bash ./create_package_wheel.py
