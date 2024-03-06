# Create Model

`FasterAPI` created a `Declarative Base` instance of SQLAlchemy for you, and all built-in models are linked with this `Base`. Therefore, your models must be created based on it. Otherwise, the corresponded table will not be created.

To do so, follow the below example:

```python
from FasterAPI import Base

class MyModel(Base):
    __tablename__ = "mymodels"
    # attributes
```

Upon on starting the server, a lifespan function will create all tables for you.
