import pathlib
import setuptools


INSTALL_REQUIRES = [
    'click==7.1.2',
    'python-jenkins==1.7.0',
]

DEV_REQUIRES = [
    'docker==4.3.1',
    'flake8==3.8.4',
    'mypy==0.790',
    'pre-commit==2.7.1',
    'pytest==6.1.1',
    'requests==2.24.0',
    'setuptools==50.3.2',
    'wheel==0.35.1',
]

LONG_DESCRIPTION = pathlib.Path('README.rst').read_text()

setuptools.setup(
    name='jenkinscfg',
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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
    },
    dependency_links=[],
    entry_points={
        'console_scripts': [
            'jenkinscfg=jenkinscfg.cli:cli',
        ],
    }
)
