from setuptools import setup, find_packages

setup(
    name='oco2L1',
    version='0.1',
    packages=find_packages('package/oco2_L1'),
    package_dir={'':'package/oco2_L1'},
    
    author='Tim Hill',
    author_email='tim.hill3@canada.ca',
    description='Creates KMZ files with footprint outlines for OCO-2 Level 1 data',
)