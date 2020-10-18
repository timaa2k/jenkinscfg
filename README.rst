jenkinscfg
==========

Update Jenkins jobs configuration declaratively from a Git repository.


Installation
------------

.. code-block:: bash

   $ pip install jenkinscfg


Usage
-----

.. code-block:: bash

   Usage: jenkinscfg [OPTIONS] COMMAND [ARGS]...

   Options:
     -h, --host TEXT
     -u, --username TEXT
     -p, --password TEXT
     --version            Show the version and exit.
     --help               Show this message and exit.

   Commands:
     diff
     dump
     update


Example
-------

.. code-block:: bash

   $ export JENKINS_HOST=http://old.leeroy.jenkins:8080

.. code-block:: bash

   $ jenkinscfg dump jobs

.. code-block:: bash

   $ tree jobs
   jobs
   └── HelloWorldJobFolder
      ├── config.xml
      └── HelloWorldJob
         └── config.xml

.. code-block:: bash

   $ export JENKINS_HOST=http://new.better.jenkins:8080

.. code-block:: bash

   $ jenkinscfg update jobs
   Creating HelloWorldJobFolder
   Creating HelloWorldJobFolder/HelloWorldJob

.. code-block:: bash

   $ mv jobs/HelloWorldJobFolder jobs/NewJobFolder

.. code-block:: bash

   $ jenkinscfg diff jobs
   Removed   HelloWorldJobFolder
   Removed   HelloWorldJobFolder/HelloWorldJob
   Added     NewJobFolder
   Added     NewJobFolder/HelloWorldJob

.. code-block:: bash

   $ jenkinscfg update jobs
   Deleting HelloWorldJobFolder/HelloWorldJob
   Deleting HelloWorldJobFolder
   Creating NewJobFolder
   Creating NewJobFolder/HelloWorldJob

.. code-block:: bash

   $ sed -i 's/false/true/' jobs/NewJobFolder/HelloWorldJob/config.xml

.. code-block:: bash

   $ jenkinscfg diff jobs
   Changed   NewJobFolder/HelloWorldJob
   ---
   +++
   @@ -1,12 +1,12 @@
    <?xml version="1.0" encoding="UTF-8"?><project>
   -  <keepDependencies>false</keepDependencies>
   +  <keepDependencies>true</keepDependencies>
      <properties/>
      <scm class="jenkins.scm.NullSCM"/>
      <canRoam>true</canRoam>
   -  <disabled>false</disabled>
   -  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
   +  <disabled>true</disabled>
   +  <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
      <triggers class="vector"/>
   -  <concurrentBuild>false</concurrentBuild>
   +  <concurrentBuild>true</concurrentBuild>
      <builders/>
      <publishers/>
      <buildWrappers/>

   Unchanged NewJobFolder

.. code-block:: bash

   $ jenkinscfg update jobs
   Updating NewJobFolder/HelloWorldJob
