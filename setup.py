from setuptools import setup, find_packages

setup(
    name="echofoam-falsifiability-suite",
    version="0.1.0",
    packages=find_packages('src'),
    package_dir={'': 'src'},
)
