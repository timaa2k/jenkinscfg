import difflib
import json
from pathlib import Path

import click
import jenkins


def server_job_paths(job_array, path):
    paths = []
    for job in job_array:
        new_path = Path(path / job['name'])
        children = job.get('jobs')
        if children is not None:
            paths += server_job_paths(children, new_path)
        paths.append(new_path)
    return paths


def get_server_jobs(server):
    json_blob = server.get_jobs()
    job_paths = server_job_paths(json_blob, Path(''))
    server_jobs = dict([])
    for job_path in job_paths:
        xml_config = server.get_job_config(str(job_path))
        server_jobs[str(job_path)] = xml_config
    return server_jobs


def get_local_jobs(jobs_path):
    local_jobs = dict([])
    for config_path in jobs_path.glob('**/config.xml'):
        job = str(config_path.relative_to(jobs_path).parent)
        local_jobs[job] = config_path.read_text()
    return local_jobs


def print_diff(changed_jobs, not_yet_updated_existing_jobs):
    for job in not_yet_updated_existing_jobs:
        if job not in changed_jobs:
            print('Unchanged ' + job)
        else:
            a = not_yet_updated_existing_jobs[job].xml.splitlines()
            b = changed_jobs[job].xml.splitlines()
            print('Changed ' + job)
            for line in difflib.unified_diff(a, b, lineterm=''):
                print(line)
                print('')


def changed_jobs(common, server_jobs, local_jobs):
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


@click.group()
def jenkinscfg() -> None:
    pass


@click.argument(
    'jobs-path',
    type=click.Path(
        exists=True,
        file_okay=False,
    ),
)
@jenkinscfg.command()
def diff(jobs_path) -> None:
    server = jenkins.Jenkins('http://localhost:8080', username='admin', password='admin')
    server_jobs = get_server_jobs(server)
    local_jobs = get_local_jobs(Path(jobs_path))
    removed = server_jobs.keys() - local_jobs.keys()
    added = local_jobs.keys() - server_jobs.keys()
    common = server_jobs.keys() & local_jobs.keys()
    changed, unchanged = changed_jobs(common, server_jobs, local_jobs)
    [print('Changed   ' + job + '\n' + changed[job] + '\n') for job in sorted(changed)]
    [print('Unchanged ' + job) for job in sorted(unchanged)]
    [print('Removed   ' + job) for job in sorted(removed)]
    [print('Added     ' + job) for job in sorted(added)]


@click.argument(
    'jobs-path',
    type=click.Path(
        exists=True,
        file_okay=False,
    ),
)
@click.option(
    '--dry-run/--no-dry-run',
    default=False,
)
@jenkinscfg.command()
def update(jobs_path, dry_run) -> None:
    server = jenkins.Jenkins('http://localhost:8080', username='admin', password='admin')
    server_jobs = get_server_jobs(server)
    local_jobs = get_local_jobs(Path(jobs_path))
    removed = server_jobs.keys() - local_jobs.keys()
    added = local_jobs.keys() - server_jobs.keys()
    common = server_jobs.keys() & local_jobs.keys()
    changed, _ = changed_jobs(common, server_jobs, local_jobs)
    for job in sorted(removed, reverse=True):
        print('Deleting ' + job + ('' if not dry_run else '(dry-run)'))
        if not dry_run:
            server.delete_job(job)
    for job in sorted(changed):
        print('Updating ' + job + ('' if not dry_run else '(dry-run)'))
        if not dry_run:
            server.reconfig_job(job, local_jobs[job])
    for job in sorted(added):
        print('Creating ' + job + ('' if not dry_run else '(dry-run)'))
        if not dry_run:
            server.create_job(job, local_jobs[job])


@click.argument(
    'jobs-path',
    type=click.Path(
        exists=True,
        file_okay=False,
    ),
)
@jenkinscfg.command()
def dump(jobs_path) -> None:
    server = jenkins.Jenkins('http://localhost:8080', username='admin', password='admin')
    server_jobs = get_server_jobs(server)
    for job in sorted(server_jobs.keys()):
        Path(jobs_path / Path(job)).mkdir(exist_ok=True)
        Path(jobs_path / Path(job) / 'config.xml').write_text(server_jobs[job])


if __name__ == '__main__':
    jenkinscfg()
