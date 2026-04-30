#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/bootstrap-ec2-ubuntu.sh" >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git make docker.io docker-compose-plugin

systemctl enable --now docker

if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  usermod -aG docker "${SUDO_USER}"
fi

echo "Bootstrap complete."
echo "If your user was added to the docker group, log out and back in before running docker without sudo."
