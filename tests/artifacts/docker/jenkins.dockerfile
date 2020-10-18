FROM jenkins/jenkins:lts

ENV JENKINS_USER integration_test
ENV JENKINS_PASS integration_test

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.security.csrf.DefaultCrumbIssuer.EXCLUDE_SESSION_ID=true"

USER root

RUN apt-get update \
 && apt-get install -y python3 python3-pip python3-venv

USER jenkins

ENV JENKINS_OPTS --httpPort=8080
ENV JENKINS_SLAVE_AGENT_PORT 50000

EXPOSE 8080
EXPOSE 50000

COPY plugins /usr/share/jenkins/ref/plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt

COPY default-user.groovy /usr/share/jenkins/ref/init.groovy.d/default-user.groovy
