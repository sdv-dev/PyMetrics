"""Invoke task definitions."""

from invoke import task


@task
def lint(c):
    """Run lint checks using ruff."""
    c.run('ruff check .')
    c.run('ruff format --check --diff .')


@task
def fix_lint(c):
    """Automatically fix lint issues using ruff."""
    c.run('ruff check --fix .')
    c.run('ruff format .')
