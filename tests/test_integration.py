import shutil
import textwrap
from pathlib import Path

import click.testing
import docker
import pytest
import requests

from jenkinscfg import cli


JENKINS_HOSTNAME = '127.0.0.1'
JENKINS_PORT = 8080
JENKINS_HOST = f'http://{JENKINS_HOSTNAME}:{JENKINS_PORT}'
JENKINS_USERNAME = 'integration_test'
JENKINS_PASSWORD = 'integration_test'

SUPPORTED_CHARS = '_-+ \'"'        # Special characters in a job or folder name.
DEFAULT_HTTP_TIMEOUT = (3.05, 27)  # (Connection timeout, Read timeout) seconds.


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        self.timeout = DEFAULT_HTTP_TIMEOUT
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
        ports={f'{JENKINS_PORT}/tcp': (JENKINS_HOSTNAME, JENKINS_PORT)},
    )
    try:
        http_retry_session().get(JENKINS_HOST)
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
    env = {
        'JENKINS_HOST': JENKINS_HOST,
        'JENKINS_USERNAME': JENKINS_USERNAME,
        'JENKINS_PASSWORD': JENKINS_PASSWORD,
    }
    result = runner.invoke(cli.cli, [command, str(path)], env=env)
    if result.exit_code != 0 and result.exception is not None:
        raise result.exception
    return result.output


def local_jenkins_job(path: Path) -> None:
    Path(path).mkdir(exist_ok=True)
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
    Path(path).mkdir(exist_ok=True)
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


@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_add_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    job: str,
) -> None:
    local_jenkins_job(tmp_path / job)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Added     {job}
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        f"""\
        Creating {job}
        """
    )
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Unchanged {job}
        """
    )


@pytest.mark.parametrize('folder', ['TestJobFolder', SUPPORTED_CHARS])
@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_add_nested_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    folder: str,
    job: str,
) -> None:
    local_jenkins_dir(tmp_path / folder)
    local_jenkins_job(tmp_path / folder / job)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Added     {folder}
        Added     {folder}/{job}
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        f"""\
        Creating {folder}
        Creating {folder}/{job}
        """
    )
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Unchanged {folder}
        Unchanged {folder}/{job}
        """
    )


@pytest.mark.parametrize('folder', ['TestJobFolder', SUPPORTED_CHARS])
@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_dump_jobs(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    folder: str,
    job: str,
) -> None:
    original = tmp_path / 'original'
    original.mkdir()
    original_folder = original / folder
    local_jenkins_dir(original_folder)
    original_job = original_folder / job
    local_jenkins_job(original_job)
    jenkinscfg('update', original)
    dumped = tmp_path / 'dumped'
    dumped.mkdir()
    dumped_folder = dumped / folder
    dumped_job = dumped_folder / job
    assert jenkinscfg('dump', dumped) == ''
    original_conf = Path(original_job / 'config.xml').read_text()
    dumped_conf = Path(dumped_job / 'config.xml').read_text()
    assert dumped_conf == original_conf
    assert jenkinscfg('diff', dumped) == textwrap.dedent(
        f"""\
        Unchanged {folder}
        Unchanged {folder}/{job}
        """
    )


@pytest.mark.parametrize('folder', ['TestJobFolder', SUPPORTED_CHARS])
@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_unchanged_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    folder: str,
    job: str,
) -> None:
    folder_path = tmp_path / folder
    local_jenkins_dir(folder_path)
    local_jenkins_job(folder_path / job)
    jenkinscfg('update', tmp_path)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Unchanged {folder}
        Unchanged {folder}/{job}
        """
    )
    assert jenkinscfg('update', tmp_path) == ''


@pytest.mark.parametrize('folder', ['TestJobFolder', SUPPORTED_CHARS])
@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_changed_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    folder: str,
    job: str,
) -> None:
    folder_path = tmp_path / folder
    local_jenkins_dir(folder_path)
    local_jenkins_job(folder_path / job)
    jenkinscfg('update', tmp_path)
    config = Path(folder_path / 'config.xml').read_text()
    new_config = config.replace(
        '<description/>',
        '<description>A folder.</description>',
    )
    Path(folder_path / 'config.xml').write_text(new_config)
    job_path = folder_path / job
    config = Path(job_path / 'config.xml').read_text()
    new_config = config.replace(
        '<disabled>false</disabled>',
        '<disabled>true</disabled>',
    )
    Path(job_path / 'config.xml').write_text(new_config)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Changed   {folder}
        --- 
        +++ 
        @@ -1,6 +1,6 @@
         <?xml version="1.0" encoding="UTF-8"?><com.cloudbees.hudson.plugins.folder.Folder plugin="cloudbees-folder@6.1.2">
           <actions/>
        -  <description/>
        +  <description>A folder.</description>
           <properties/>
           <folderViews/>
           <healthMetrics/>

        Changed   {folder}/{job}
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

        """  # noqa: W291,E501
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        f"""\
        Updating {folder}
        Updating {folder}/{job}
        """
    )


@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_remove_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    job: str,
) -> None:
    local_jenkins_job(tmp_path / job)
    jenkinscfg('update', tmp_path)
    shutil.rmtree(tmp_path / job)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Removed   {job}
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        f"""\
        Deleting {job}
        """
    )


@pytest.mark.parametrize('folder', ['TestJobFolder', SUPPORTED_CHARS])
@pytest.mark.parametrize('job', ['TestJob', SUPPORTED_CHARS])
def test_remove_nested_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
    folder: str,
    job: str,
) -> None:
    local_jenkins_dir(tmp_path / folder)
    local_jenkins_job(tmp_path / folder / job)
    jenkinscfg('update', tmp_path)
    shutil.rmtree(tmp_path / folder)
    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        f"""\
        Removed   {folder}
        Removed   {folder}/{job}
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        f"""\
        Deleting {folder}/{job}
        Deleting {folder}
        """
    )
