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
    scripts=['iggyref/bin/iggyref_update'],
)
