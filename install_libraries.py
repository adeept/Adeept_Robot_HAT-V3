#!/usr/bin/env python3
# coding=utf-8
# File name: install_setup.py
# Author: Adeept
# Description: Download Adeept_RaspberryPi_Setup repo and install dependencies

import os
import sys
import shutil
import subprocess
import shlex
import tempfile
import pwd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SETUP_REPO_URL = "https://github.com/adeept/Adeept_RaspberryPi_Setup.git"
SETUP_REPO_DIR = ROOT_DIR / "Adeept_RaspberryPi_Setup"
REQUIREMENTS_FILE = "requirements.yml"
WIFI_SERVICE = "wifi-hotspot-manager.service"

def run_command(cmd, cwd=None):
    print("\n>>>", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)

def privileged_command(cmd):
    if os.geteuid() != 0:
        cmd = ["sudo"] + cmd
    run_command(cmd)

def check_dependencies():
    packages = []
    if not shutil.which("git"):
        packages.append("git")

    try:
        import yaml
    except ImportError:
        packages.append("python3-yaml")

    if packages:
        privileged_command(["apt-get", "update"])
        privileged_command(["apt-get", "install", "-y"] + packages)

def download_setup_repo():
    git_dir = SETUP_REPO_DIR / ".git"
    if SETUP_REPO_DIR.exists() and git_dir.is_dir():
        print(f"\nUpdating existing repository at {SETUP_REPO_DIR}")
        run_command(["git", "pull"], cwd=SETUP_REPO_DIR)
    else:
        print("\n========== Downloading Adeept Raspberry Pi Setup ==========")
        print(f"Repository : {SETUP_REPO_URL}")
        print(f"Destination: {SETUP_REPO_DIR}")
        run_command(["git", "clone", "--depth", "1", SETUP_REPO_URL, str(SETUP_REPO_DIR)])


def install_setup_dependencies():
    import yaml
    req_path = SETUP_REPO_DIR / REQUIREMENTS_FILE
    if not req_path.is_file():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")

    with open(req_path, "r", encoding="utf-8") as f:
        requirements = yaml.safe_load(f) or {}

    apt_packages = requirements.get("apt", [])
    pip_packages = requirements.get("pip", [])

    if not isinstance(apt_packages, list) or not isinstance(pip_packages, list):
        raise ValueError("apt and pip dependencies must be lists")

    if apt_packages:
        print("\n========== Installing APT packages ==========")
        privileged_command(["apt-get", "update"])
        privileged_command(["apt-get", "install", "-y"] + apt_packages)

    if pip_packages:
        print("\n========== Installing Python packages ==========")
        privileged_command([sys.executable, "-m", "pip", "install", "--break-system-packages"] + pip_packages)


def enable_i2c_spi():
    print("\n========== Enabling I2C & SPI ==========")
    raspi_config = shutil.which("raspi-config")
    if not raspi_config:
        print("[WARN] raspi-config not found, skip enabling I2C/SPI")
        return
    privileged_command([raspi_config, "nonint", "do_i2c", "0"])
    privileged_command([raspi_config, "nonint", "do_spi", "0"])
    print("I2C enabled.")
    print("SPI enabled.")

def install_service_file(service_name, content):
    service_path = f"/etc/systemd/system/{service_name}"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        privileged_command(["install", "-m", "644", temp_path, service_path])
    finally:
        os.unlink(temp_path)

    privileged_command(["systemctl", "daemon-reload"])
    privileged_command(["systemctl", "enable", service_name])


def install_wifi_service(user_home):
    source = SETUP_REPO_DIR / "wifi_hotspot_manager.sh"
    if not source.is_file():
        raise FileNotFoundError(f"WiFi script not found: {source}")

    script_path = Path(user_home) / "wifi_hotspot_manager.sh"
    privileged_command(["install", "-m", "755", str(source), str(script_path)])

    service_content = f"""[Unit]
Description=WiFi and Hotspot Manager Service
After=network.target NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart={shlex.quote(str(script_path))}
User=root
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
    install_service_file(WIFI_SERVICE, service_content)
    print(f"WiFi service {WIFI_SERVICE} enabled")


def get_user_info():
    try:
        username = os.environ.get("SUDO_USER") or pwd.getpwuid(os.getuid()).pw_name
        user = pwd.getpwnam(username)
        return username, user.pw_dir
    except KeyError:
        raise RuntimeError(f"Cannot find user information: {username}")


def main():
    username, user_home = get_user_info()
    print(f"Username: {username}")
    print(f"User Home: {user_home}")

    check_dependencies()

    print("\n========================================")
    print("Adeept Raspberry Pi Setup Installer")
    print("========================================")

    download_setup_repo()
    install_setup_dependencies()
    enable_i2c_spi()
    install_wifi_service(user_home)

    print("\n========================================")
    print("Setup installation completed.")
    print(f"Repository path: {SETUP_REPO_DIR}")
    print("========================================")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"\nCommand failed: {error}")
        sys.exit(error.returncode)
    except Exception as error:
        print(f"\nInstallation failed: {error}")
        sys.exit(1)
