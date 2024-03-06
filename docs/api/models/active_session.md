# Active Session

This model is used to store active session for users. It has a one-to-one relationship with `User` model. If multiple session is not allowed, user has to login again on any new device.

::: FasterAPI.models.ActiveSession
    options:
        members: true
