#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/bootstrap-ec2-ubuntu.sh" >&2
  exit 1
fi

# Base tooling
apt-get update
apt-get install -y ca-certificates curl gnupg git make

# Remove distro Docker if a previous run installed it; docker.io conflicts
# with docker-ce (both provide /usr/bin/docker) and does not bundle the
# compose plugin.
apt-get remove -y docker.io docker-doc docker-compose podman-docker containerd runc 2>/dev/null || true

# Docker's official apt repository (source of docker-compose-plugin).
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

systemctl enable --now docker

if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  usermod -aG docker "${SUDO_USER}"
fi

echo "Bootstrap complete."
echo "If your user was added to the docker group, log out and back in before running docker without sudo."
