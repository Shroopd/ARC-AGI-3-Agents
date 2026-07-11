FROM rockylinux:9

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN dnf -y update && dnf install -y \
    dnf-plugins-core \
    epel-release \
    && dnf config-manager --set-enabled crb \
    && dnf -y update

RUN dnf -y install --allowerasing \
    git \
    curl \
    which \
    procps-ng \
    sudo \
    python3.13 \
    findutils \
    unzip \
    wget \
    bash-completion \
    && dnf clean all

# Python venv support
RUN python3.13 -m ensurepip --upgrade && \
    python3.13 -m pip install --upgrade pip setuptools wheel

# Install uv (Rust-based Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    cp /root/.local/bin/uvx /usr/local/bin/uvx && \
    rm /root/.local/bin/uv /root/.local/bin/uvx

# Create non-root user with sudo access
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

ENV SHELL=/bin/bash
ENV UV_LINK_MODE=copy

# Verify installations
RUN uv --version && \
    uvx --version && \
    python3 --version && \
    git --version

USER $USERNAME
WORKDIR /workspaces/ARC-AGI-3-Agents