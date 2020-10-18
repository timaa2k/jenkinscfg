jenkinscfg
==========


Prerequisites
-------------

- Python >= 3.8

.. code-block:: bash

   python3 --version


Setup
-----

1) Create virtual environment

.. code-block:: bash

   mkdir -p ~/.virtualenv
   python3 -m venv ~/.virtualenv/jenkinscfg

2) Activate virtual environment

.. code-block:: bash

   source ~/.virtualenv/jenkinscfg/bin/activate

3) Install Python packages required for development

Only do this while the virtual environment is active.

.. code-block:: bash

   pip install -e '.[dev]'

4) Execute the unpackaged jenkinscfg CLI

Only do this while the virtual environment is active.

.. code-block:: bash

   python3 src/jenkinscfg/cli.py update --dry-run <jobs_path>


Lint
----

Perform a linter check via:

.. code-block:: bash

   make lint


Test
----

Perform a test run via:

.. code-block:: bash

   make test
   make test.unit
   make test.integration

To run a particular test run the following and specify the test function:

.. code-block:: bash

   pytest -s -vvv -k test_function_xyz
