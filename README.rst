jenkinscfg
==========

Update Jenkins job configuration declaratively from a Git repository.

Think kubecfg for Jenkins
-------------------------

.. code-block:: bash

   $ export JENKINS_HOST=http://localhost:8080

   $ tree jobs
   jobs
   └── HelloWorldJobFolder
      ├── config.xml
      └── HelloWorldJob
         └── config.xml

   $ jenkinscfg update jobs
   Creating HelloWorldJobFolder
   Creating HelloWorldJobFolder/HelloWorldJob

   $ mv jobs/HelloWorldJobFolder jobs/NewJobFolder

   $ jenkinscfg diff jobs
   Removed   HelloWorldJobFolder
   Removed   HelloWorldJobFolder/HelloWorldJob
   Added     NewJobFolder
   Added     NewJobFolder/HelloWorldJob

   $ jenkinscfg update jobs
   Deleting HelloWorldJobFolder/HelloWorldJob
   Deleting HelloWorldJobFolder
   Creating NewJobFolder
   Creating NewJobFolder/HelloWorldJob

   $ sed -i 's/false/true/' jobs/NewJobFolder/HelloWorldJob/config.xml

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

   $ jenkinscfg update jobs
   Updating NewJobFolder/HelloWorldJob
