import uuid
from pathlib import Path
from typing import Any, Dict, List

import jenkins

from jenkinscfg import cli


class StubJenkins(jenkins.Jenkins):

    def __init__(self, jobs: List[Dict[str, Any]], config: str) -> None:
        self.jobs = jobs
        self.config = config

    def get_jobs(self) -> List[Dict[str, Any]]:
        return self.jobs

    def get_job_config(self, job: str) -> str:
        return f'{job}-{self.config}'


SERVER_JOBS = {'s': 'a', 's/n': 'b', 't': 'c'}
LOCAL_JOBS = {'s': 'a', 's/m': 'b', 't': 'd'}


def test_write_jobs_to_filesystem(tmp_path: Path) -> None:
    cli.write_jobs_to_filesystem(SERVER_JOBS, tmp_path)
    for j in SERVER_JOBS:
        config = Path(tmp_path / j / 'config.xml').read_text()
        assert config == SERVER_JOBS[j]


def test_get_local_jobs(tmp_path: Path) -> None:
    cli.write_jobs_to_filesystem(LOCAL_JOBS, tmp_path)
    jobs = cli.get_local_jobs(tmp_path)
    assert jobs == LOCAL_JOBS


def test_get_server_jobs() -> None:
    conf = str(uuid.uuid4())
    server = StubJenkins(
        jobs=[{'name': 'a', 'jobs': [{'name': 'b'}]}, {'name': 'c'}],
        config=conf,
    )
    jobs = cli.get_server_jobs(server)
    assert jobs == {'a': f'a-{conf}', 'a/b': f'a/b-{conf}', 'c': f'c-{conf}'}


def test_compare_jobs() -> None:
    removed, common, added = cli.compare_jobs(SERVER_JOBS, LOCAL_JOBS)
    assert removed == {'s/n'}
    assert common == {'s', 't'}
    assert added == {'s/m'}


def test_changed_jobs() -> None:
    removed, common, added = cli.compare_jobs(SERVER_JOBS, LOCAL_JOBS)
    changed, unchanged = cli.changed_jobs(common, SERVER_JOBS, LOCAL_JOBS)
    assert unchanged == {'s'}
    assert changed == {'t': '--- \n+++ \n@@ -1 +1 @@\n-c\n+d'}
