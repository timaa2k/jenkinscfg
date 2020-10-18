import pathlib
import setuptools
from typing import List


def _get_dependencies(requirements_file: pathlib.Path) -> List[str]:
    """
    Return requirements from a requirements file.
    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().strip().split('\n')
    print(lines)
    return [line for line in lines if not line.startswith('#')]


INSTALL_REQUIRES = _get_dependencies(
    requirements_file=pathlib.Path('requirements.txt'),
)

DEV_REQUIRES = _get_dependencies(
    requirements_file=pathlib.Path('dev-requirements.txt'),
)

LONG_DESCRIPTION = pathlib.Path('README.rst').read_text()

setuptools.setup(
    name='jenkinscfg',
    version='0.1.0',
    author='Tim Weidner',
    description='Declarative Jenkins Jobs Configuration',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    url='https://github.com/timaa2k/jenkinscfg',
    include_package_data=True,
    packages=setuptools.find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: GPLv3 License',
        'Operating System :: OS Independent',
    ],
    dependency_links=[],
)
