#!/bin/sh

readonly gdcmroot="/gdcm"
readonly gdcmsrc="$gdcmroot/src"
readonly gdcmout="$gdcmroot/out"

readonly baseimage="quay.io/pypa/manylinux_2_28_x86_64"
readonly container="gdcm-wheel"

mkdir -p "$PWD/dist"

podman pull "$baseimage"
podman run -it --rm --workdir="$gdcmroot" --name="$container" -v "$PWD:$gdcmroot":z "$baseimage" /bin/bash
