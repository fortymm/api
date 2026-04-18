# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/devcontainers/base:bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        build-essential \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER vscode
ENV MISE_DATA_DIR=/home/vscode/.local/share/mise \
    MISE_CONFIG_DIR=/home/vscode/.config/mise \
    PATH=/home/vscode/.local/bin:/home/vscode/.local/share/mise/shims:$PATH

RUN curl -fsSL https://mise.run | sh \
    && echo 'eval "$(/home/vscode/.local/bin/mise activate bash)"' >> /home/vscode/.bashrc \
    && echo 'eval "$(/home/vscode/.local/bin/mise activate zsh)"' >> /home/vscode/.zshrc

WORKDIR /workspaces/api
