FROM python:3.13-slim

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    sudo \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
ENV UV_CACHE_DIR=/uv-cache

# Verify installations
RUN uv --version && \
    uvx --version && \
    python3 --version && \
    git --version

USER $USERNAME
WORKDIR /workspaces/ARC-AGI-3-Agents
