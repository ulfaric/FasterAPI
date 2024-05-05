import os
import pickle

import jinja2
import typer

from .. import core

template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)
module_cli = typer.Typer()


@module_cli.command()
def create(name: str):
    try:
        core._meta_data = pickle.loads(open(".meta", "rb").read())
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
    os.mkdir(f"modules/{name}")

    # Create module __init__.py
    module_init_py_template = templates.get_template("base_module/__init__.py.j2")
    module_init_py = module_init_py_template.render(module_name=name)
    with open(
        f"modules/{name}/__init__.py", "w"
    ) as output_file:
        output_file.write(module_init_py)

    # Create module models.py
    module_models_py_template = templates.get_template("base_module/model.py.j2")
    module_models_py = module_models_py_template.render(model_name=name.capitalize(), module_name=name)
    with open(
        f"modules/{name}/model.py", "w"
    ) as output_file:
        output_file.write(module_models_py)

    # Create module schemas.py
    module_schemas_py_template = templates.get_template("base_module/schema.py.j2")
    module_schemas_py = module_schemas_py_template.render(model_name=name.capitalize())
    with open(
        f"modules/{name}/schema.py", "w"
    ) as output_file:
        output_file.write(module_schemas_py)

    # Create module router.py
    module_router_py_template = templates.get_template("base_module/router.py.j2")
    module_router_py = module_router_py_template.render(model_name=name.capitalize(), module_name=name)
    with open(
        f"modules/{name}/router.py", "w"
    ) as output_file:
        output_file.write(module_router_py)

    # Create module dependencies.py
    module_dependencies_py_template = templates.get_template(
        "base_module/dependencies.py.j2"
    )
    module_dependencies_py = module_dependencies_py_template.render()
    with open(
        f"modules/{name}/dependencies.py", "w"
    ) as output_file:
        output_file.write(module_dependencies_py)

    # Create module utils.py
    module_utils_py_template = templates.get_template("base_module/utils.py.j2")
    module_utils_py = module_utils_py_template.render(model_name=name.capitalize(), module_name=name)
    with open(
        f"modules/{name}/utils.py", "w"
    ) as output_file:
        output_file.write(module_utils_py)

    # Update .modules file
    core.meta_data.modules.append(name)
    with open(f".meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))
        
    # Update serve.py
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules = core.meta_data.modules)
    with open(f"serve.py", "w") as output_file:
        output_file.write(serve_py)
        
    typer.echo(f"Module {name} added.")


@module_cli.command()
def migrate(name: str):
    try:
        core._meta_data = pickle.loads(open(".meta", "rb").read())
    except FileNotFoundError:
        raise typer.Abort(
            "Project meta file not found. Run `fasterapi create` to create a project."
        )
