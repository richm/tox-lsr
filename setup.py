from setuptools import setup

# /usr/lib64/python3.8/distutils/dist.py:274:
# UserWarning: Unknown distribution option: 'use_scm_version'
# setup(use_scm_version={"write_to": "src/tox_lsr/version.py"})

setup(package_data={"": ["data/*", "data/.*"]})
