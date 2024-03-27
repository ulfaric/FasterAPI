import os
import secrets

import jinja2
import typer

cli = typer.Typer()

project = typer.Typer()
template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)


@cli.command()
def new(project_name: str, tls: bool = typer.Option(False)):

    if os.path.isdir(project_name):
        typer.echo(f"Project {project_name} folder already exists.")
        raise typer.Abort()

    os.mkdir(project_name)
    os.mkdir(f"{project_name}/modules")

    # Create server.py
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render()
    with open(f"{project_name}/serve.py", "w") as output_file:
        output_file.write(serve_py)

    # Create configuration file
    config_yaml_template = templates.get_template("config.yaml.j2")
    config_yaml = config_yaml_template.render(
        project_name=project_name, secret_key=secrets.token_hex(32)
    )
    with open(f"{project_name}/config.yaml", "w") as output_file:
        output_file.write(config_yaml)

    # copy user module
    os.mkdir(f"{project_name}/modules/user")

    user_module_init_py_template = templates.get_template("user_module/__init__.py.j2")
    user_module_init_py = user_module_init_py_template.render()
    with open(f"{project_name}/modules/user/__init__.py", "w") as output_file:
        output_file.write(user_module_init_py)

    user_module_models_py_template = templates.get_template("user_module/models.py.j2")
    user_module_models_py = user_module_models_py_template.render()
    with open(f"{project_name}/modules/user/models.py", "w") as output_file:
        output_file.write(user_module_models_py)

    user_moudle_schemas_py_template = templates.get_template(
        "user_module/schemas.py.j2"
    )
    user_module_schemas_py = user_moudle_schemas_py_template.render()
    with open(f"{project_name}/modules/user/schemas.py", "w") as output_file:
        output_file.write(user_module_schemas_py)

    user_module_router_py_template = templates.get_template("user_module/router.py.j2")
    user_module_router_py = user_module_router_py_template.render()
    with open(f"{project_name}/modules/user/router.py", "w") as output_file:
        output_file.write(user_module_router_py)

    user_module_dependencies_py_template = templates.get_template(
        "user_module/dependencies.py.j2"
    )
    user_module_dependencies_py = user_module_dependencies_py_template.render()
    with open(f"{project_name}/modules/user/dependencies.py", "w") as output_file:
        output_file.write(user_module_dependencies_py)

    user_module_utils_py_template = templates.get_template("user_module/utils.py.j2")
    user_module_utils_py = user_module_utils_py_template.render()
    with open(f"{project_name}/modules/user/utils.py", "w") as output_file:
        output_file.write(user_module_utils_py)
