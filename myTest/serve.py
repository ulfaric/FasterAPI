from FasterAPI import core

from user.module.router import user_router



core.app.include_router(user_router)


if __name__ == "__main__":
    core.serve()