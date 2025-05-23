#!/bin/bash

#   __|    \    _ \  |      _ \   __| __ __| __ __|
#  (      _ \     /  |     (   | (_ |    |      |
# \___| _/  _\ _|_\ ____| \___/ \___|   _|     _|

# scripts/update_version.sh
# Created 1/21/25 - 9:56 PM UK Time (London) by carlogtt
# Copyright (c) Amazon.com Inc. All Rights Reserved.
# AMAZON.COM CONFIDENTIAL

# THIS SCRIPT CAN ONLY BE SOURCE FROM ANOTHER SCRIPT WHERE THE VARIABLES HERE BELOW ARE DEFINED
# DO NOT RUN THIS SCRIPT DIRECTLY

# Read the current version and date from the file
version_file="${project_root_dir_abs}/pyproject.toml"
current_version=$(grep "^version = \"" "${version_file}" | cut -d ' ' -f 3 | sed 's/"//g')

echo -e "Current version: ${current_version}"

# Parse the command line
read -r -p "Enter the version type (major, minor or [patch]): " option
if [[ -z "${option}" ]]; then
	# No option provided, so default to the patch version
	option="patch"
fi
echo -e "${option} version selected"

# Extract the major, minor, and patch version numbers
major=$(echo "${current_version}" | cut -d '.' -f 1)
minor=$(echo "${current_version}" | cut -d '.' -f 2)
patch=$(echo "${current_version}" | cut -d '.' -f 3)

# Get today's date in the format MM/DD/YYYY
today=$(date +%m/%d/%Y)

# Check what option was provided and increment the version accordingly
if [[ "${option}" == "major" ]]; then
	# Increment the major version
	new_major=$((major + 1))
	new_minor=0
	new_patch=0
elif [[ "${option}" == "minor" ]]; then
	# Increment the minor version
	new_major=${major}
	new_minor=$((minor + 1))
	new_patch=0
elif [[ "${option}" == "patch" ]]; then
	# Increment the patch version
	new_major=${major}
	new_minor=${minor}
	new_patch=$((patch + 1))
else
	echo "Invalid option. Please enter 'major', 'minor', or 'patch'."
	exit 1
fi

# Create the new version string
new_version="version = \"${new_major}.${new_minor}.${new_patch}\""
new_version_print="New version: ${new_major}.${new_minor}.${new_patch}"

# Write the new version to the file
sed -i '' "s|^version = \".*|${new_version}|" "${version_file}"

echo -e "\n${bold_green}${package} ${new_version_print}${end}\n"
