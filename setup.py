from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in gatepass/__init__.py
from gatepass import __version__ as version

setup(
	name="gatepass",
	version=version,
	description="gatepass",
	author="Ganu Reddy",
	author_email="ganu.b@caratred.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
