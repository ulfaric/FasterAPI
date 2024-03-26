import typer
from .project import project

cli = typer.Typer()
cli.add_typer(project, name="project")
