#!/bin/bash

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# scripts/formatter.sh
# Created 2/16/24 - 1:26 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

# Command used in the external tool is:
# --login -c "./scripts/formatter.sh"

# Colors
red=$'\033[31m'
green=$'\033[32m'
yellow=$'\033[33m'
blu=$'\033[34m'
bold_red=$'\033[1m\033[31m'
bold_green=$'\033[1m\033[32m'
bold_yellow=$'\033[1m\033[33m'
bold_blu=$'\033[1m\033[34m'
bold=$'\033[1m'
end=$'\033[0m'

# Emoji
green_check_mark="\xE2\x9C\x85"
hammer_and_wrench="\xF0\x9F\x9B\xA0"
clock="\xE2\x8F\xB0"
sparkles="\xE2\x9C\xA8"
stop_sign="\xF0\x9F\x9B\x91"
warning_sign="\xE2\x9A\xA0\xEF\xB8\x8F"
key="\xF0\x9F\x94\x91"
circle_arrows="\xF0\x9F\x94\x84"
broom="\xF0\x9F\xA7\xB9"
link="\xF0\x9F\x94\x97"

# Paths
script_fullpath="$0"
script_dir="$(dirname "${script_fullpath}")"
script_dir_absolute_path="$(realpath "${script_dir}")"
project_root_dir="$(realpath "${script_dir_absolute_path}/..")"

# Check if we are on DevDsk or local Dev Env
devdsk=5
if [ -d "${HOME}/devdsk${devdsk}" ]; then
    # Use DevDsk venv
    path_to_venv_root="${HOME}/devdsk${devdsk}/venvs/dev_tools"
else
    # Use local dev venv
    path_to_venv_root="${HOME}/Library/CloudStorage/Dropbox/SDE/VirtualEnvs/dev_tools"
fi
source "${path_to_venv_root}/bin/activate"
echo

echo -e "${bold_green}${green_check_mark} Virtual environment activated:${end}"
echo -e "OS Version: $(uname)"
echo -e "Kernel Version: $(uname -r)"
echo -e "venv: $VIRTUAL_ENV"
echo -e "running: $(python --version)"
echo

echo -e "${bold_green}${hammer_and_wrench} Project Root:${end}"
echo "${project_root_dir}"
echo

echo -e "${bold_green}${sparkles} Running iSort...${end}"
isort="Y"
if  [[ $isort == "Y" ]]; then
    isort "${project_root_dir}/src" 2>&1
else
    echo -e "${bold_red}[DISABLED]${end}"
fi
echo

echo -e "${bold_green}${sparkles} Running Black...${end}"
black="Y"
if  [[ $black == "Y" ]]; then
    black "${project_root_dir}/src" 2>&1
else
    echo -e "${bold_red}[DISABLED]${end}"
fi
echo

echo -e "${bold_green}${sparkles} Running Flake8...${end}"
flake8="Y"
if  [[ $flake8 == "Y" ]]; then
    flake8 -v "${project_root_dir}/src" 2>&1
else
    echo -e "${bold_red}[DISABLED]${end}"
fi
echo

echo -e "${bold_green}${sparkles} Running mypy...${end}"
mypy="N"
if  [[ $mypy == "Y" ]]; then
    mypy "${project_root_dir}/src" 2>&1
else
    echo -e "${bold_red}[DISABLED]${end}"
fi
echo

echo -e "${bold_yellow}${warning_sign} Virtual environment deactivated!${end}"
deactivate
