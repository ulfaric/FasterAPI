# import uvicorn
# from modules.user.router import auth_router
from FasterAPI import core

# core.app.include_router(auth_router)



# if __name__ == "__main__":
#     uvicorn.run(core.app, host="127.0.0.1", port=9000, log_level="info")
core.serve(port=9000, debug=True)