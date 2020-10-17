import shutil
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
def jenkins_server() -> docker.models.Container:
    docker_client = docker.from_env()
    jenkins_image, _ = docker_client.images.build(
        path='tests/artifacts/docker/',
        dockerfile='jenkins.dockerfile',
        tag='jenkins:jenkinscfg_integration_test',
    )
    try:
        jenkins_container = docker_client.containers.run(
            image=jenkins_image,
            detach=True,
            ports={'8080/tcp': (LOCALHOST, 8080)},
        )
        http = http_retry_session()
        http.get(f'http://{LOCALHOST}:8080')
        yield jenkins_container
    finally:
        jenkins_container.remove(force=True)


def test_diff_cmd(
    jenkins_server: docker.models.Container,
    tmp_path: Path,
) -> None:
    jobs_path = tmp_path / 'jobs'
    shutil.copytree(Path('tests/artifacts/jobs'), jobs_path)
    runner = click.testing.CliRunner()
    res = runner.invoke(cli.cli, ['diff', str(jobs_path)])
    assert res.exit_code == 0
    assert 'HelloWorldFolder/NestedHelloWorldFolder/HelloWorldJob' in res.output
