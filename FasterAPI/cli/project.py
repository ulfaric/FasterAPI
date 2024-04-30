import os
import pickle
import secrets
import subprocess

import alembic
import jinja2
import typer

from .. import core

template_loader = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(__file__), "templates"), followlinks=True
)
templates = jinja2.Environment(loader=template_loader)
project_cli = typer.Typer()


@project_cli.command()
def create(project_name: str):

    with typer.progressbar(range(100), label="Creating project...") as progress:
        if os.path.isdir(project_name):
            typer.echo(f"Project {project_name} folder already exists.")
            raise typer.Abort()

        os.mkdir(project_name)
        os.mkdir(f"{project_name}/modules")
        with open(f"{project_name}/modules/__init__.py", "w") as output_file:
            output_file.write("")
        progress.update(10)

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
        progress.update(10)

        # Create configuration file
        typer.echo("Populate config.yaml...")
        config_yaml_template = templates.get_template("config.yaml.j2")
        config_yaml = config_yaml_template.render(
            project_name=project_name, secret_key=secrets.token_hex(32)
        )
        with open(f"{project_name}/config.yaml", "w") as output_file:
            output_file.write(config_yaml)
        progress.update(10)

        # copy user module
        typer.echo("Populate user module...")
        os.mkdir(f"{project_name}/modules/user")

        user_module_init_py_template = templates.get_template(
            "user_module/__init__.py.j2"
        )
        user_module_init_py = user_module_init_py_template.render()
        with open(f"{project_name}/modules/user/__init__.py", "w") as output_file:
            output_file.write(user_module_init_py)

        user_module_models_py_template = templates.get_template(
            "user_module/models.py.j2"
        )
        user_module_models_py = user_module_models_py_template.render()
        with open(f"{project_name}/modules/user/models.py", "w") as output_file:
            output_file.write(user_module_models_py)

        user_moudle_schemas_py_template = templates.get_template(
            "user_module/schemas.py.j2"
        )
        user_module_schemas_py = user_moudle_schemas_py_template.render()
        with open(f"{project_name}/modules/user/schemas.py", "w") as output_file:
            output_file.write(user_module_schemas_py)

        user_module_router_py_template = templates.get_template(
            "user_module/router.py.j2"
        )
        user_module_router_py = user_module_router_py_template.render()
        with open(f"{project_name}/modules/user/router.py", "w") as output_file:
            output_file.write(user_module_router_py)

        user_module_dependencies_py_template = templates.get_template(
            "user_module/dependencies.py.j2"
        )
        user_module_dependencies_py = user_module_dependencies_py_template.render()
        with open(f"{project_name}/modules/user/dependencies.py", "w") as output_file:
            output_file.write(user_module_dependencies_py)

        user_module_utils_py_template = templates.get_template(
            "user_module/utils.py.j2"
        )
        user_module_utils_py = user_module_utils_py_template.render()
        with open(f"{project_name}/modules/user/utils.py", "w") as output_file:
            output_file.write(user_module_utils_py)
        progress.update(10)
        
        # typer.echo("Initialize alembic...")
        # os.chdir(f"{project_name}/modules/")
        # subprocess.run(["alembic", "init", "user_alembic"])
        # progress.update(10)
        
        # typer.echo("Populate alembic env.py...")
        # alembic_ini_path = f"alembic.ini"
        # with open(alembic_ini_path, 'r') as file:
        #     config_contents = file.read()      
        # config_contents = config_contents.replace('sqlalchemy.url = driver://user:pass@localhost/dbname',
        #                                         f'sqlalchemy.url ={core.config.get("SQLALCHEMY_DATABASE_URL", "sqlite:///dev.db")}')
        # with open(alembic_ini_path, 'w') as file:
        #     file.write(config_contents)
        # progress.update(10)
        
        # typer.echo("Populate alembic env.py...")
        # alembic_env_path = f"user_alembic/env.py"
        # with open(alembic_env_path, 'r') as file:
        #     env_contents = file.read()
        # env_contents = env_contents.replace('target_metadata = None',
        #                                     'from user import user_module\ntarget_metadata = user_module.base.metadata')
        # with open(alembic_env_path, 'w') as file:
        #     file.write(env_contents)
        # progress.update(10)
        
        # typer.echo("Populate alembic script...")
        # subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial"])
        # progress.update(10)
        
        # typer.echo("Populate alembic upgrade...")
        # subprocess.run(["alembic", "upgrade", "head"])
        # progress.update(10)

@project_cli.command()
def update():
    core._meta_data = pickle.loads(open(".meta", "rb").read())
    serve_py_template = templates.get_template("serve.py.j2")
    serve_py = serve_py_template.render(modules=core.meta_data.modules)
    with open("serve.py", "w") as output_file:
        output_file.write(serve_py)
