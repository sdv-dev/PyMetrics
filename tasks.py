from invoke import task


@task
def lint(c):
    c.run('flake8 download_analytics')
    c.run('pydocstyle download_analytics')
    c.run('isort -c download_analytics')
    c.run('pylint download_analytics --rcfile=setup.cfg')
