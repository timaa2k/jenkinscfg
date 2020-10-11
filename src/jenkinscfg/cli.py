import click


@click.option(
    '-p',
    '--jobs-path',
    type=str,
)
@click.pass_context
def jenkinscfg(
    jobs_path: str,
) -> None:
    pass


if __name__ == '__main__':
    jenkinscfg()
