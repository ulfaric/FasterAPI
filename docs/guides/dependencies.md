# Dependencies

`FasterAPI` comes with multiple pre-built dependencies for assisting user authentication.

## autenticated

::: FasterAPI.dependencies.authenticated

This dependency can be used on any FastAPI endpoints to secure it that only authenticated user can access. To be authenticated, the user request must contains "Authorization: Bear XXXX", where "XXXX" is the JWT token obtained after login.

## is_superuser

::: FasterAPI.dependencies.is_superuser

This dependency will secure the endpoint that only authenticated user can access, and the user also must be a superuser.

## scope

FasterAPI implemented the Oauth2 scope but it is verified against the user privileges. It means the scopes inside the JWT will always be the user's privileges. Therefore, you can use the scope header to verify against the user privilege. For example:

```python
@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Security(authenticated, scopes=["items"])]
):
    return [{"item_id": "Foo", "owner": current_user.username}]
```

If the user does not have priviledge "items", then it will be refused to access endpoint "/users/me/items/". Dependency "is_superuser" works in the similar manner.
