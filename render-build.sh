#!/usr/bin/env bash
# render-build.sh

# Install Chromium and chromedriver
apt-get update
apt-get install -y chromium-browser chromium-chromedriver

# Install Python dependencies
pip install -r requirements.txt