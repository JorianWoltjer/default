from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='default',
    version='1.0',
    packages=find_packages(),
    entry_points={
        # To run from command line
        'console_scripts': ['default=default.main:main']
    },
    install_requires=requirements,
)
