from setuptools import setup, find_packages

setup(
    name = 'iggyref',
    version = '1.0',
    packages = find_packages(),
    install_requires = [
        'SQLAlchemy>=1.1.5',
        'PyYAML>=3.12',
    ],
    include_package_data = True,
    entry_points={
        'console_scripts': [
            'iggyref_update=iggyref.iggyref_update:update',
        ],
    },
)
