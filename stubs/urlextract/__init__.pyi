from typing import Literal

class URLExtract:
    def __init__(
        self,
        extract_email: bool = False,
        cache_dns: bool = True,
        extract_localhost: bool = True,
        limit: int = 10000,
        allow_mixed_case_hostname: bool = True,
    ) -> None: ...
    def find_urls(
        self,
        text: str,
        only_unique: bool = False,
        check_dns: bool = False,
        *,
        get_indices: Literal[False] = False,
        with_schema_only: bool = False,
    ) -> list[str]: ...
