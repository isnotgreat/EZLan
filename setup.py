from setuptools import setup, find_packages

setup(
    name="ezlan",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6',
        'cryptography',
        'requests',
        'netifaces',
    ],
    entry_points={
        'console_scripts': [
            'ezlan=ezlan.main:main',
        ],
    }
)
