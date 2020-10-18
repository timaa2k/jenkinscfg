import textwrap
from pathlib import Path

import click.testing
import docker
import jenkins
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
    assert result.exit_code == 0
    return result.output


def local_jenkins_job(path: Path) -> None:
    Path(path).mkdir()
    Path(path / 'config.xml').write_text(jenkins.EMPTY_CONFIG_XML)


def local_jenkins_dir(path: Path) -> None:
    Path(path).mkdir()
    Path(path / 'config.xml').write_text(jenkins.EMPTY_FOLDER_XML)


def test_add_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    local_jenkins_job(tmp_path / 'DemoJob')

    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Added     DemoJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Creating DemoJob
        """
    )


def test_add_nested_job(
    empty_jenkins_server: 'docker.models.Container',
    tmp_path: Path,
) -> None:
    local_jenkins_dir(tmp_path / 'DemoJobFolder')
    local_jenkins_job(tmp_path / 'DemoJobFolder' / 'DemoJob')

    assert jenkinscfg('diff', tmp_path) == textwrap.dedent(
        """\
        Added     DemoJobFolder
        Added     DemoJobFolder/DemoJob
        """
    )
    assert jenkinscfg('update', tmp_path) == textwrap.dedent(
        """\
        Creating DemoJobFolder
        Creating DemoJobFolder/DemoJob
        """
    )
