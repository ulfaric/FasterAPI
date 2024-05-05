# Background Process

The `FastAPI` allows you to create the lifespan as a startup background process. However, some timees you may want to add additional background process during run time. To solve this problem, I itergeated the other open source project [`Akatosh`]( https://ulfaric.github.io/Akatosh/). To add a additional background process, simply user the `event` decorator with any functions!

for exmaple:

```py
from Akatosh.event import event

@event(at=Mundus.time, till=inf)
def your_function:
    pass
```

Add the above codes inside an endpoint function, then `your_function` will be run right away till forever! All event interaction supported by Akatosh applies!
