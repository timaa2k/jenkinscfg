import difflib
import os
from pathlib import Path

import click
import jenkins


JENKINS_HOST = str(os.getenv('JENKINS_HOST', 'http://localhost:8080'))
JENKINS_USERNAME = str(os.getenv('JENKINS_USERNAME', 'admin'))
JENKINS_PASSWORD = str(os.getenv('JENKINS_PASSWORD', 'admin'))


@click.group()
@click.option('-h', '--host', type=str, default=JENKINS_HOST)
@click.option('-u', '--username', type=str, default=JENKINS_USERNAME)
@click.option('-p', '--password', type=str, default=JENKINS_PASSWORD)
@click.pass_context
def cli(ctx, host, username, password) -> None:
    ctx.obj = jenkins.Jenkins(host, username=username, password=password)


@cli.command()
@click.argument('jobs-path', type=click.Path(exists=True, file_okay=False))
@click.pass_obj
def diff(server, jobs_path) -> None:
    local_jobs = get_local_jobs(Path(jobs_path))
    server_jobs = get_server_jobs(server)
    removed, unchanged, changed, added = compare_jobs(server_jobs, local_jobs)
    [print('Changed   ' + job + '\n' + changed[job] + '\n') for job in sorted(changed)]
    [print('Unchanged ' + job) for job in sorted(unchanged)]
    [print('Removed   ' + job) for job in sorted(removed)]
    [print('Added     ' + job) for job in sorted(added)]


@cli.command()
@click.argument('jobs-path', type=click.Path(exists=True, file_okay=False))
@click.option('--dry-run/--no-dry-run', default=False)
@click.pass_obj
def update(server, jobs_path, dry_run) -> None:
    local_jobs = get_local_jobs(Path(jobs_path))
    server_jobs = get_server_jobs(server)
    removed, unchanged, changed, added = compare_jobs(server_jobs, local_jobs)
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


@cli.command()
@click.argument('jobs-path', type=click.Path(file_okay=False))
@click.pass_obj
def dump(server, jobs_path) -> None:
    server_jobs = get_server_jobs(server)
    for job in sorted(server_jobs.keys()):
        Path(jobs_path / Path(job)).mkdir(exist_ok=True)
        Path(jobs_path / Path(job) / 'config.xml').write_text(server_jobs[job])


def get_local_jobs(jobs_path):
    local_jobs = dict([])
    for config_path in jobs_path.glob('**/config.xml'):
        job = str(config_path.relative_to(jobs_path).parent)
        local_jobs[job] = config_path.read_text()
    return local_jobs


def get_server_jobs(server):
    json_blob = server.get_jobs()
    job_paths = server_job_paths(json_blob, Path(''))
    server_jobs = dict([])
    for job_path in job_paths:
        xml_config = server.get_job_config(str(job_path))
        server_jobs[str(job_path)] = xml_config
    return server_jobs


def server_job_paths(job_array, path):
    paths = []
    for job in job_array:
        new_path = Path(path / job['name'])
        children = job.get('jobs')
        if children is not None:
            paths += server_job_paths(children, new_path)
        paths.append(new_path)
    return paths


def compare_jobs(server_job_configs, local_job_configs):
    removed_jobs = server_job_configs.keys() - local_job_configs.keys()
    added_jobs = local_job_configs.keys() - server_job_configs.keys()
    common = server_job_configs.keys() & local_job_configs.keys()
    changed_job_diffs, unchanged_jobs = changed_jobs(common, server_job_configs, local_job_configs)
    return removed_jobs, unchanged_jobs, changed_job_diffs, added_jobs


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


if __name__ == '__main__':
    cli()
