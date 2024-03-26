import os


import typer
import jinja2

project = typer.Typer()


@project.command()
def new(project_name: str, tls: bool = typer.Option(False)):

    if os.path.isdir(project_name):
        typer.echo(f"Project {project_name} folder already exists.")
        raise typer.Abort()

    os.mkdir(project_name)
    os.mkdir(f"{project_name}/models")

    
    template_loader = jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
    template_env = jinja2.Environment(loader=template_loader)
    serve_py_template = template_env.get_template("serve.py.j2")
    serve_py = serve_py_template.render()

    with open(f"{project_name}/serve.py", "w") as output_file:
        output_file.write(serve_py)
