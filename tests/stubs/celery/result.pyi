from typing import Any

class AsyncResult:
    def __init__(self, id: str) -> None: ...
    def ready(self) -> bool: ...
    def successful(self) -> bool: ...
    result: Any
