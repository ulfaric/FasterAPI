import typer

from .module import module_cli
from .project import project_cli

cli = typer.Typer()
cli.add_typer(project_cli, name="project")
cli.add_typer(module_cli, name="module")
