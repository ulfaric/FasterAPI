import os
import pickle
import secrets

import jinja2
import typer

from .. import core, Module

template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)
project_cli = typer.Typer()


@project_cli.command()
def create(project_name: str):

    if os.path.isdir(project_name):
        typer.echo(f"Project {project_name} folder already exists.")
        raise typer.Abort()

    os.mkdir(project_name)

    # Create server.py
    typer.echo("Populate serve.py...")
    core.meta_data.project_name = project_name
    core.meta_data.modules.append("user")
    with open(f"{project_name}/.meta", "wb") as output_file:
        output_file.write(pickle.dumps(core.meta_data))
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open(f"{project_name}/serve.py", "w") as output_file:
        output_file.write(serve_py)

    # Create configuration file
    typer.echo("Populate config.yaml...")
    config_yaml_template = templates.get_template("config.yaml.j2")
    config_yaml = config_yaml_template.render(project_name=project_name)
    with open(f"{project_name}/config.yaml", "w") as output_file:
        output_file.write(config_yaml)

    # copy user module
    typer.echo("Populate user module...")
    os.mkdir(f"{project_name}/user")
    os.mkdir(f"{project_name}/user/module")

    user_module_config_yaml_template = templates.get_template("user/config.yaml.j2")
    user_module_config_yaml = user_module_config_yaml_template.render(
        project_name=project_name, module_name="user", secret_key=secrets.token_hex(32)
    )
    with open(f"{project_name}/user/config.yaml", "w") as output_file:
        output_file.write(user_module_config_yaml)

    user_module_init_py_template = templates.get_template("user/__init__.py.j2")
    user_module_init_py = user_module_init_py_template.render()
    with open(f"{project_name}/user/module/__init__.py", "w") as output_file:
        output_file.write(user_module_init_py)

    user_moudle_schemas_py_template = templates.get_template("user/schemas.py.j2")
    user_module_schemas_py = user_moudle_schemas_py_template.render()
    with open(f"{project_name}/user/module/schemas.py", "w") as output_file:
        output_file.write(user_module_schemas_py)

    user_module_router_py_template = templates.get_template("user/router.py.j2")
    user_module_router_py = user_module_router_py_template.render()
    with open(f"{project_name}/user/module/router.py", "w") as output_file:
        output_file.write(user_module_router_py)

    user_module_dependencies_py_template = templates.get_template(
        "user/dependencies.py.j2"
    )
    user_module_dependencies_py = user_module_dependencies_py_template.render()
    with open(f"{project_name}/user/module/dependencies.py", "w") as output_file:
        output_file.write(user_module_dependencies_py)

    user_module_utils_py_template = templates.get_template("user/utils.py.j2")
    user_module_utils_py = user_module_utils_py_template.render()
    with open(f"{project_name}/user/module/utils.py", "w") as output_file:
        output_file.write(user_module_utils_py)
        
    # initialize alembic
    name = "user"
    os.chdir(f"{project_name}/{name}")
    module = Module(name, config_file="config.yaml")
    os.system("alembic init alembic")
    # Update alembic.ini
    with open("alembic.ini", "r") as file:
        alembic_ini_content = file.read()

    if "sqlite" in module._sql_url:
        alembic_ini_content = alembic_ini_content.replace(
            "sqlalchemy.url = driver://user:pass@localhost/dbname",
            f"sqlalchemy.url = sqlite:///{name}.db",
        )
    else:
        alembic_ini_content = alembic_ini_content.replace(
            "sqlalchemy.url = driver://user:pass@localhost/dbname",
            f"sqlalchemy.url = {module._sql_url}",
        )

    with open("alembic.ini", "w") as file:
        file.write(alembic_ini_content)
    with open("alembic/env.py", "r") as file:
        alembic_env_py_content = file.read()
    alembic_env_py_content = alembic_env_py_content.replace(
        "target_metadata = None",
        f"from module import user_module\ntarget_metadata = user_module.base.metadata",
    )
    os.remove("alembic/env.py")
    with open("alembic/env.py", "w") as file:
        file.write(alembic_env_py_content)

    message = "User Model Initial Migration"
    os.system(f"alembic revision --autogenerate")
    os.system("alembic upgrade head")

@project_cli.command()
def update():
    core._meta_data = pickle.loads(open(".meta", "rb").read())
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open("serve.py", "w") as output_file:
        output_file.write(serve_py)
