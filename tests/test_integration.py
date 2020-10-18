import shutil
import textwrap
from pathlib import Path

import click.testing
import docker
import pytest
import requests

from jenkinscfg import cli


LOCALHOST = '127.0.0.1'
DEFAULT_TIMEOUT = (3.05, 27)  # Seconds.


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        self.timeout = DEFAULT_TIMEOUT
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs) -> requests.Response:  # type: ignore
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)


def http_retry_session() -> requests.Session:
    http = requests.Session()
    retries = requests.packages.urllib3.util.retry.Retry(
        total=10,
        # Yields 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256 seconds.
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=['HEAD', 'GET', 'OPTIONS'],
    )
    adapter = TimeoutHTTPAdapter(max_retries=retries)
    http.mount('http://', adapter)
    http.mount('https://', adapter)
    return http


@pytest.fixture(scope='session')
def jenkins_server() -> 'docker.models.Container':
    docker_client = docker.from_env()
    jenkins_image, _ = docker_client.images.build(
        path='tests/artifacts/docker/',
        dockerfile='jenkins.dockerfile',
        tag='jenkins:jenkinscfg_integration_test',
    )
    jenkins_container = docker_client.containers.run(
        image=jenkins_image,
        detach=True,
        ports={'8080/tcp': (LOCALHOST, 8080)},
    )
    try:
        http_retry_session().get(f'http://{LOCALHOST}:8080')
        yield jenkins_container
    finally:
        jenkins_container.remove(force=True)


@pytest.fixture(scope='function')
def empty_jenkins_server(
    jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> 'docker.models.Container':
    # Empty path update to clean all jobs.
    jenkinscfg('update', tmp_path)
    yield jenkins_server


def jenkinscfg(command: str, path: Path) -> str:
    runner = click.testing.CliRunner()
    result = runner.invoke(cli.cli, [command, str(path)])
    if result.exit_code != 0 and result.exception is not None:
        raise result.exception
    return result.output


def local_jenkins_job(path: Path) -> None:
    Path(path).mkdir()
    empty_job_xml = textwrap.dedent(
        """\
        <?xml version="1.0" encoding="UTF-8"?><project>
          <keepDependencies>false</keepDependencies>
          <properties/>
          <scm class="jenkins.scm.NullSCM"/>
          <canRoam>true</canRoam>
          <disabled>false</disabled>
          <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
          <triggers class="vector"/>
          <concurrentBuild>false</concurrentBuild>
          <builders/>
          <publishers/>
          <buildWrappers/>
        </project>"""
    )
    Path(path / 'config.xml').write_text(empty_job_xml)


def local_jenkins_dir(path: Path) -> None:
    Path(path).mkdir()
    empty_folder_xml = textwrap.dedent(
        """\
        <?xml version="1.0" encoding="UTF-8"?><com.cloudbees.hudson.plugins.folder.Folder plugin="cloudbees-folder@6.1.2">
          <actions/>
          <description/>
          <properties/>
          <folderViews/>
          <healthMetrics/>
        </com.cloudbees.hudson.plugins.folder.Folder>"""  # noqa: E501
    )
    Path(path / 'config.xml').write_text(empty_folder_xml)


def test_add_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    local_jenkins_job(tmp_path / 'TestJob')
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Added     TestJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Creating TestJob
        """
    )


def test_add_nested_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    local_jenkins_dir(tmp_path / 'TestJobFolder')
    local_jenkins_job(tmp_path / 'TestJobFolder' / 'TestJob')
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Added     TestJobFolder
        Added     TestJobFolder/TestJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Creating TestJobFolder
        Creating TestJobFolder/TestJob
        """
    )


def test_dump_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    job = 'TestJob'
    original_jobs = tmp_path / 'original'
    original_jobs.mkdir()
    local_jenkins_job(original_jobs / job)
    jenkinscfg('update', original_jobs)
    dumped_jobs = tmp_path / 'dumped'
    dumped_jobs.mkdir()
    assert jenkinscfg('dump', dumped_jobs) == ''
    original = Path(original_jobs / job / 'config.xml').read_text()
    dump = Path(dumped_jobs / job / 'config.xml').read_text()
    assert dump == original


def test_unchanged_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    local_jenkins_job(tmp_path / 'TestJob')
    jenkinscfg('update', tmp_path)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Unchanged TestJob
        """
    )
    assert jenkinscfg('update', tmp_path) == ''


def test_changed_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    job = tmp_path / 'TestJob'
    local_jenkins_job(job)
    jenkinscfg('update', tmp_path)
    config = Path(job / 'config.xml').read_text()
    new_config = config.replace(
        '<disabled>false</disabled>',
        '<disabled>true</disabled>',
    )
    Path(job / 'config.xml').write_text(new_config)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Changed   TestJob
        --- 
        +++ 
        @@ -3,7 +3,7 @@
           <properties/>
           <scm class="jenkins.scm.NullSCM"/>
           <canRoam>true</canRoam>
        -  <disabled>false</disabled>
        +  <disabled>true</disabled>
           <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
           <triggers class="vector"/>
           <concurrentBuild>false</concurrentBuild>

        """  # noqa: W291
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Updating TestJob
        """
    )


def test_remove_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    test_job = tmp_path / 'TestJob'
    local_jenkins_job(test_job)
    jenkinscfg('update', tmp_path)
    shutil.rmtree(test_job)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Removed   TestJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Deleting TestJob
        """
    )


def test_remove_nested_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    test_folder = tmp_path / 'TestJobFolder'
    local_jenkins_dir(test_folder)
    local_jenkins_job(test_folder / 'TestJob')
    jenkinscfg('update', tmp_path)
    shutil.rmtree(test_folder)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Removed   TestJobFolder
        Removed   TestJobFolder/TestJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Deleting TestJobFolder/TestJob
        Deleting TestJobFolder
        """
    )
