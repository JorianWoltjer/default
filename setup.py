from setuptools import setup, find_packages

setup(
    name='default',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['default=default.main:main']  # To run from command line
    },
    install_requires=[
        'colorama',  # Terminal colors
        'netifaces',  # Network interfaces
        'pyfiglet',  # ASCII art
        'dnslib',  # DNS listener
        'pyngrok',  # ngrok for tunnels
    ],
)
