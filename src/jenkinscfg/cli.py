import difflib
import os
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import click
import jenkins
from click.core import Context

from . import __version__


@click.group()
@click.option('-h', '--host', type=str, default='http://localhost:8080')
@click.option('-u', '--username', type=str, default='admin')
@click.option('-p', '--password', type=str, default='admin')
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: Context, host: str, username: str, password: str) -> None:
    host = str(os.getenv('JENKINS_HOST', host))
    username = str(os.getenv('JENKINS_USERNAME', username))
    password = str(os.getenv('JENKINS_PASSWORD', password))
    ctx.obj = jenkins.Jenkins(host, username=username, password=password)


@cli.command()
@click.argument('jobs-path', type=click.Path(exists=True, file_okay=False))
@click.pass_obj
def diff(server: jenkins.Jenkins, jobs_path: Path) -> None:
    local_jobs = get_local_jobs(Path(jobs_path))
    server_jobs = get_server_jobs(server)
    removed, common, added = compare_jobs(server_jobs, local_jobs)
    changed, unchanged = changed_jobs(common, server_jobs, local_jobs)
    print_diff(changed, unchanged, removed, added)


@cli.command()
@click.argument('jobs-path', type=click.Path(exists=True, file_okay=False))
@click.option('--dry-run/--no-dry-run', default=False)
@click.pass_obj
def update(server: jenkins.Jenkins, jobs_path: Path, dry_run: bool) -> None:
    local_jobs = get_local_jobs(Path(jobs_path))
    server_jobs = get_server_jobs(server)
    removed, common, added = compare_jobs(server_jobs, local_jobs)
    diffs, unchanged = changed_jobs(common, server_jobs, local_jobs)
    changed = set(diffs.keys())
    apply_update(server, removed, changed, added, local_jobs, dry_run)


@cli.command()
@click.argument('jobs-path', type=click.Path(file_okay=False))
@click.pass_obj
def dump(server: jenkins.Jenkins, jobs_path: Path) -> None:
    server_jobs = get_server_jobs(server)
    write_jobs_to_filesystem(server_jobs, jobs_path)


def write_jobs_to_filesystem(jobs: Dict[str, str], path: Path) -> None:
    for job in sorted(jobs.keys()):
        Path(path / Path(job)).mkdir(exist_ok=True)
        Path(path / Path(job) / 'config.xml').write_text(jobs[job])


def get_local_jobs(jobs_path: Path) -> Dict[str, str]:
    local_jobs = dict([])
    for config_path in jobs_path.glob('**/config.xml'):
        job = str(config_path.relative_to(jobs_path).parent)
        local_jobs[job] = config_path.read_text()
    return local_jobs


def get_server_jobs(server: jenkins.Jenkins) -> Dict[str, str]:
    json_blob = server.get_jobs()
    job_paths = server_job_paths(json_blob, Path(''))
    server_jobs = dict([])
    for job_path in job_paths:
        xml_config = server.get_job_config(str(job_path))
        server_jobs[str(job_path)] = xml_config
    return server_jobs


def server_job_paths(job_array: List[Dict[str, Any]], path: Path) -> List[Path]:
    paths = []
    for job in job_array:
        new_path = Path(path / job['name'])
        children = job.get('jobs')
        if children is not None:
            paths += server_job_paths(children, new_path)
        paths.append(Path(new_path))
    return paths


def compare_jobs(
    server_jobs: Dict[str, str],
    local_jobs: Dict[str, str],
) -> Tuple[Set[str], Set[str], Set[str]]:
    removed = server_jobs.keys() - local_jobs.keys()
    added = local_jobs.keys() - server_jobs.keys()
    common = server_jobs.keys() & local_jobs.keys()
    return removed, common, added


def changed_jobs(
    common: Set[str],
    server_jobs: Dict[str, str],
    local_jobs: Dict[str, str],
) -> Tuple[Dict[str, str], Set[str]]:
    changed = dict([])
    unchanged = set([])
    for job in common:
        a = server_jobs[job].splitlines()
        b = local_jobs[job].splitlines()
        diff = list(difflib.unified_diff(a, b, lineterm=''))
        if len(diff) > 0:
            changed[job] = '\n'.join(diff)
        else:
            unchanged.add(job)
    return changed, unchanged


def print_diff(
    changed: Dict[str, str],
    unchanged: Set[str],
    removed: Set[str],
    added: Set[str],
) -> None:
    for job in sorted(changed):
        print('Changed   ' + job + '\n' + changed[job] + '\n')
    for job in sorted(unchanged):
        print('Unchanged ' + job)
    for job in sorted(removed):
        print('Removed   ' + job)
    for job in sorted(added):
        print('Added     ' + job)


def apply_update(
    server: jenkins.Jenkins,
    removed: Set[str],
    changed: Set[str],
    added: Set[str],
    local_jobs: Dict[str, str],
    dry_run: bool,
) -> None:
    for job in sorted(removed, reverse=True):
        print('Deleting ' + job + ('' if not dry_run else ' (dry-run)'))
        if not dry_run:
            server.delete_job(job)
    for job in sorted(changed):
        print('Updating ' + job + ('' if not dry_run else ' (dry-run)'))
        if not dry_run:
            server.reconfig_job(job, local_jobs[job])
    for job in sorted(added):
        print('Creating ' + job + ('' if not dry_run else ' (dry-run)'))
        if not dry_run:
            server.create_job(job, local_jobs[job])


if __name__ == '__main__':
    cli()
