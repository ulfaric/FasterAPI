import os
import pickle

import jinja2
import typer

from .. import Module, core

module_cli = typer.Typer()

template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)


@module_cli.command()
def create(name: str):

    # Load meta data
    try:
        core._meta_data = pickle.loads(open(".meta", "rb").read())
        project_name = core.meta_data.project_name
    except FileNotFoundError:
        raise typer.Abort(
            "Project meta file not found. Run `fasterapi create` to create a project."
        )

    # Check if name is valid
    if not name.isalpha():
        raise typer.BadParameter("Name must contain letters only.")

    # convert name to lowercase
    name = name.lower()

    typer.echo(f"Add module {name}...")

    # Create module directory
    os.mkdir(f"{project_name}/modules/{name}")

    # Create module __init__.py
    module_init_py_template = templates.get_template("base_module/__init__.py.j2")
    module_init_py = module_init_py_template.render(module_name=name)
    with open(f"{project_name}/modules/{name}/__init__.py", "w") as output_file:
        output_file.write(module_init_py)

    # Create module models.py
    module_models_py_template = templates.get_template("base_module/models.py.j2")
    module_models_py = module_models_py_template.render(module_name=name.capitalize())
    with open(f"{project_name}/modules/{name}/models.py", "w") as output_file:
        output_file.write(module_models_py)

    # Create module schemas.py
    module_schemas_py_template = templates.get_template("base_module/schemas.py.j2")
    module_schemas_py = module_schemas_py_template.render(module_name=name.capitalize())
    with open(f"{project_name}/modules/{name}/schemas.py", "w") as output_file:
        output_file.write(module_schemas_py)

    # Create module router.py
    module_router_py_template = templates.get_template("base_module/router.py.j2")
    module_router_py = module_router_py_template.render(module_name=name)
    with open(f"{project_name}/modules/{name}/router.py", "w") as output_file:
        output_file.write(module_router_py)

    # Create module dependencies.py
    module_dependencies_py_template = templates.get_template(
        "base_module/dependencies.py.j2"
    )
    module_dependencies_py = module_dependencies_py_template.render()
    with open(f"{project_name}/modules/{name}/dependencies.py", "w") as output_file:
        output_file.write(module_dependencies_py)

    # Create module utils.py
    module_utils_py_template = templates.get_template("base_module/utils.py.j2")
    module_utils_py = module_utils_py_template.render()
    with open(f"{project_name}/modules/{name}/utils.py", "w") as output_file:
        output_file.write(module_utils_py)

    # Update .modules file
    core.meta_data.modules.append(name)
    with open(f"{project_name}/.meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))

    typer.echo(f"Module {name} added.")

@module_cli.command()
def migrate(name: str):
    # Load meta data
    try:
        core._meta_data = pickle.loads(open(".meta", "rb").read())
        project_name = core.meta_data.project_name
    except FileNotFoundError:
        raise typer.Abort(
            "Project meta file not found. Run `fasterapi create` to create a project."
        )
    
    # initialize module
    try:
        module = Module(config_file=f"{project_name}/modules/{name}/config.yml")
    except FileNotFoundError:
        raise typer.Abort(f"Module {name} config file not found.")
    
    
    