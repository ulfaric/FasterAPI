import os
import pickle

import jinja2
import typer
import shutil

from .. import core

template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)
module_cli = typer.Typer()


@module_cli.command()
def create(name: str):
    """Create a new module."""
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
    os.mkdir(f"{name}")
    os.mkdir(f"{name}/module")

    # Create module __init__.py
    module_init_py_template = templates.get_template("module/__init__.py.j2")
    module_init_py = module_init_py_template.render(
        module_name=name, model_name=name.capitalize()
    )
    with open(f"{name}/module/__init__.py", "w") as output_file:
        output_file.write(module_init_py)

    # Create module schemas.py
    module_schemas_py_template = templates.get_template("module/schema.py.j2")
    module_schemas_py = module_schemas_py_template.render(model_name=name.capitalize())
    with open(f"{name}/module/schema.py", "w") as output_file:
        output_file.write(module_schemas_py)

    # Create module router.py
    module_router_py_template = templates.get_template("module/router.py.j2")
    module_router_py = module_router_py_template.render(
        model_name=name.capitalize(), module_name=name
    )
    with open(f"{name}/module/router.py", "w") as output_file:
        output_file.write(module_router_py)

    # Create module dependencies.py
    module_dependencies_py_template = templates.get_template(
        "module/dependencies.py.j2"
    )
    module_dependencies_py = module_dependencies_py_template.render()
    with open(f"{name}/module/dependencies.py", "w") as output_file:
        output_file.write(module_dependencies_py)

    # Create module utils.py
    module_utils_py_template = templates.get_template("module/utils.py.j2")
    module_utils_py = module_utils_py_template.render(
        model_name=name.capitalize(), module_name=name
    )
    with open(f"{name}/module/utils.py", "w") as output_file:
        output_file.write(module_utils_py)
        
    # create config.yaml
    config_yaml_template = templates.get_template("config.yaml.j2")
    config_yaml = config_yaml_template.render()
    with open(f"{name}/config.yaml", "w") as output_file:
        output_file.write(config_yaml)

    # Update .meta file
    if name not in core.meta_data.modules:
        core.meta_data.modules.append(name)
    with open(f".meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))

    # Update serve.py
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open(f"serve.py", "w") as output_file:
        output_file.write(serve_py)

    typer.echo(f"Module {name} added.")

    # initialize alembic
    os.chdir(name)
    os.system("alembic init alembic")
    # Update alembic.ini
    with open("alembic.ini", "r") as file:
        alembic_ini_content = file.read()

    alembic_ini_content = alembic_ini_content.replace(
        "sqlalchemy.url = driver://user:pass@localhost/dbname",
        f"sqlalchemy.url = sqlite:///{name}.db",
    )

    with open("alembic.ini", "w") as file:
        file.write(alembic_ini_content)


@module_cli.command()
def migrate(module_name: str, message: str="Initial migration"):
    """Migratie models of the module by alembic."""
    
    module_name = module_name.lower()

    try:
        core._meta_data = pickle.loads(open(".meta", "rb").read())
    except FileNotFoundError:
        raise typer.Abort(
            "Project meta file not found. Run `fasterapi create` to create a project."
        )

    if module_name not in core.meta_data.modules:
        raise typer.BadParameter(f"Module {module_name} not found in meta data.")

    os.chdir(module_name)
    with open("alembic/env.py", "r") as file:
        alembic_env_py_content = file.read()
    alembic_env_py_content = alembic_env_py_content.replace(
        "target_metadata = None",
        f"from module import {module_name}_module\ntarget_metadata = {module_name}_module.base.metadata",
    )
    os.remove("alembic/env.py")
    with open("alembic/env.py", "w") as file:
        file.write(alembic_env_py_content)
        
    os.system(f"alembic revision -m {message} --autogenerate")
    os.system("alembic upgrade head")

@module_cli.command()
def remove(name: str):
    """remove a module."""
    
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

    typer.echo(f"Remove module {name}...")

    # archieve module directory
    if not os.path.exists(".archieve"):
        os.mkdir(".archieve")
    shutil.move(name, f".archieve/{name}")

    # Update .modules file
    if name in core.meta_data.modules:
        core.meta_data.modules.remove(name)
    with open(f".meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))

    # Update serve.py
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open(f"serve.py", "w") as output_file:
        output_file.write(serve_py)

    typer.echo(f"Module {name} removed.")
    
@module_cli.command()
def restore(name: str):
    """restore a module."""
    
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

    typer.echo(f"Restore module {name}...")

    # archieve module directory
    if not os.path.exists(".archieve"):
        raise typer.Abort("No module to restore.")
    shutil.move(f".archieve/{name}", name)

    # Update .modules file
    if name not in core.meta_data.modules:
        core.meta_data.modules.append(name)
    with open(f".meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))

    # Update serve.py
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open(f"serve.py", "w") as output_file:
        output_file.write(serve_py)

    typer.echo(f"Module {name} restored.")