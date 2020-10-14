import shutil
from pathlib import Path

import click.testing
import docker

from jenkinscfg import cli


def jenkins_container() -> docker.Container:
    try:

    finally:


def test_diff_cmd(tmp_path: Path) -> None:
    jobs_path = tmp_path / 'jobs'
    shutil.copytree(Path('tests/artifacts/jobs'), jobs_path)
    runner = click.testing.CliRunner()
    res = runner.invoke(cli.cli, ['diff', str(jobs_path)])
    assert res.exit_code == 0
    assert 'HelloWorldFolder/NestedHelloWorldFolder/HelloWorldJob' in res.output
