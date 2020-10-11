jenkinscfg
==========


Prerequisites
-------------

- Python 3.8

.. code-block:: bash

   python3 --version


Setup
-----

1) Create virtual environment

.. code-block:: bash

   mkdir -p ~/.virtualenv
   python3 -m venv ~/.virtualenv/economy-beat

2) Activate virtual environment

.. code-block:: bash

   source ~/.virtualenv/economy-beat/bin/activate

3) Install Python packages required for development

Only do this while the virtual environment is active.

.. code-block:: bash

   pip install -e '.[dev]'


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

To run a particular test run the following and put in the test name:

.. code-block:: bash

   pytest -s -vvv -k 'TestGroup and test_function'
