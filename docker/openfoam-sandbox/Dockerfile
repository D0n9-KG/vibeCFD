ARG BASE_IMAGE=enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest

FROM ${BASE_IMAGE}

USER root

SHELL ["/bin/bash", "-lc"]

ARG OPENFOAM_PACKAGE=openfoam13
ARG OPENFOAM_PLATFORM=linux64GccDPInt32Opt
ARG OPENFOAM_THIRD_PARTY_PLATFORM=linux64GccDPInt32
ARG OPENFOAM_DEB_URL=https://downloads.sourceforge.net/project/foam/foam/ubuntu/dists/jammy/main/binary-amd64/openfoam13_20260212_amd64.deb

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        g++ \
        libreadline-dev \
        libc6 \
        libgcc-s1 \
        libopenmpi3 \
        libstdc++6 \
        libxt-dev \
        zlib1g \
        binutils-dev \
        flex \
        libopenmpi-dev \
        openmpi-bin \
        gnuplot \
        gnuplot-x11 \
        make \
    && curl -L --retry 5 --retry-delay 5 "${OPENFOAM_DEB_URL}" -o "/tmp/${OPENFOAM_PACKAGE}.deb" \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y "/tmp/${OPENFOAM_PACKAGE}.deb" \
    && rm -f "/tmp/${OPENFOAM_PACKAGE}.deb" \
    && rm -rf /var/lib/apt/lists/*

RUN printf '%s\n' \
    "export FOAM_INST_DIR=/opt" \
    "export WM_PROJECT_DIR=/opt/${OPENFOAM_PACKAGE}" \
    "export WM_PROJECT_VERSION=13" \
    "export ZSH_NAME=\"\${ZSH_NAME:-}\"" \
    "if [ -f /opt/${OPENFOAM_PACKAGE}/etc/bashrc ]; then" \
    "  . /opt/${OPENFOAM_PACKAGE}/etc/bashrc >/dev/null 2>&1 || true" \
    "fi" \
    > /etc/profile.d/openfoam.sh

ENV BASH_ENV= \
    FOAM_INST_DIR=/opt \
    WM_PROJECT=OpenFOAM \
    WM_THIRD_PARTY=ThirdParty \
    WM_PROJECT_INST_DIR=/opt \
    WM_PROJECT_DIR=/opt/${OPENFOAM_PACKAGE} \
    WM_PROJECT_VERSION=13 \
    WM_OPTIONS=${OPENFOAM_PLATFORM} \
    WM_ARCH=linux64 \
    WM_ARCH_OPTION=64 \
    WM_COMPILER=Gcc \
    WM_MPLIB=SYSTEMOPENMPI \
    FOAM_APPBIN=/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/bin \
    FOAM_LIBBIN=/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib \
    FOAM_ETC=/opt/${OPENFOAM_PACKAGE}/etc \
    FOAM_APP=/opt/${OPENFOAM_PACKAGE}/applications \
    FOAM_MODULES=/opt/${OPENFOAM_PACKAGE}/applications/modules \
    FOAM_MPI=openmpi-system \
    FOAM_SRC=/opt/${OPENFOAM_PACKAGE}/src \
    FOAM_TUTORIALS=/opt/${OPENFOAM_PACKAGE}/tutorials \
    MPI_ARCH_PATH=/usr/lib/x86_64-linux-gnu/openmpi \
    ParaView_DIR=/usr \
    ParaView_INCLUDE_DIR=/usr/include/paraview-5.10 \
    ParaView_LIB_DIR=/usr/bin/../lib/x86_64-linux-gnu \
    ParaView_TYPE=system \
    ParaView_VERSION=5.10.0-RC1 \
    PV_PLUGIN_PATH=/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib/paraview-5.10 \
    PATH=/opt/${OPENFOAM_PACKAGE}/thirdparty/platforms/linux64Gcc/gperftools-svn/bin:/opt/${OPENFOAM_PACKAGE}/bin:/opt/${OPENFOAM_PACKAGE}/wmake:/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    LD_LIBRARY_PATH=/opt/${OPENFOAM_PACKAGE}/thirdparty/platforms/linux64Gcc/gperftools-svn/lib:/usr/lib/x86_64-linux-gnu:/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib/paraview-5.10:/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib/openmpi-system:/opt/${OPENFOAM_PACKAGE}/thirdparty/platforms/${OPENFOAM_THIRD_PARTY_PLATFORM}/lib/openmpi-system:/usr/lib/x86_64-linux-gnu/openmpi/lib:/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib:/opt/${OPENFOAM_PACKAGE}/thirdparty/platforms/${OPENFOAM_THIRD_PARTY_PLATFORM}/lib:/opt/${OPENFOAM_PACKAGE}/platforms/${OPENFOAM_PLATFORM}/lib/dummy

RUN bash -lc "command -v simpleFoam \
    && command -v blockMesh \
    && command -v snappyHexMesh \
    && simpleFoam -help >/tmp/simpleFoam.help 2>&1 || true \
    && grep -q 'foamRun' /tmp/simpleFoam.help \
    && blockMesh -help >/tmp/blockMesh.help 2>&1 \
    && grep -q 'Usage: blockMesh' /tmp/blockMesh.help"
