from FasterAPI.utils import create_superuser
from FasterAPI.app import app

create_superuser(
    username="admin",
    password="admin",
    email="ryf0510@live.com",
    first_name="admin",
    last_name="admin",
)

Myapp = app