import pathlib
import pkg_resources
import setuptools
from typing import List


with pathlib.Path('requirements.txt').open() as requirements_txt:
    INSTALL_REQUIRES = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

LONG_DESCRIPTION = pathlib.Path('README.rst').read_text()

setuptools.setup(
    name='jenkinscfg',
    version='0.1.0a1',
    author='Tim Weidner',
    author_email='timaa2k@gmail.com',
    description='Declarative Jenkins Jobs Configuration',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    url='https://github.com/timaa2k/jenkinscfg',
    include_package_data=True,
    packages=setuptools.find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    dependency_links=[],
    entry_points={
        'console_scripts': [
            'jenkinscfg=jenkinscfg.cli:cli',
        ],
    }
)
