# Build new package version
echo -e "\n\n${bold_green}${hammer_and_wrench}  Building package${end}"
python3 -m build
echo -e "completed!"

# Check package artifacts
echo -e "\n\n${bold_green}${package} Checking package health${end}"
python3 -m twine check dist/*

# Upload package to TEST PyPi
echo -e "\n\n${bold_green}${network_world} Uploading package to TEST PyPi${end}"
python3 -m twine upload \
	--repository testpypi \
	--username __token__ \
	--password "${CARLOGTT_SECRET_PYPI_TEST_API_TOKEN}" \
	dist/*

# Upload package to PROD PyPi
echo -e "\n\n${bold_green}${network_world} Uploading package to PROD PyPi${end}"
python3 -m twine upload \
	--username __token__ \
	--password "${CARLOGTT_SECRET_PYPI_PROD_API_TOKEN}" \
	dist/*
