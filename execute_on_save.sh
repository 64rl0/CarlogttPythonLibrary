#! /bin/bash

# Command used in the external tool is:
# --login -c "./execute_on_save.sh"

# Set venv with iSor and Black binaries here
path_to_venv_root='/Users/carlogtt/Library/CloudStorage/Dropbox/SDE/VirtualEnvs/dev_tools'
source ${path_to_venv_root}/bin/activate
echo

echo -e '\033[1m\033[32mVirtual environment activated:\033[0m'
echo "$VIRTUAL_ENV"
python --version
echo

echo -e '\033[1m\033[32mProject Root:\033[0m'
pwd
echo

echo -e '\033[1m\033[32mRunning iSort...\033[0m'
#echo 'currently disabled on project root'
isort . 2>&1
echo

echo -e '\033[1m\033[32mRunning Black...\033[0m'
#echo 'currently disabled on project root'
black . 2>&1
echo

echo -e '\033[1m\033[32mRunning Flake8...\033[0m'
#echo 'currently disabled on project root'
flake8 -v . 2>&1
echo
