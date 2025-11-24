import os
from pathlib import Path


class SystemdCreds:
    """Allow looking up systemd credentials with caching.

    Credentials are loaded on-demand from:
    1. Files in $CREDENTIALS_DIRECTORY/{name}
    2. Environment variables ${NAME} (uppercase)

    Values are cached for the program's runtime.
    """

    _instance: "SystemdCreds | None" = None
    _cache: dict[str, str] = {}

    def __new__(cls) -> "SystemdCreds":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    def __getattr__(self, name: str) -> str:
        """Look up a credential by attribute access.

        Args:
            name: The credential name (lowercase for files, uppercase for env vars)

        Returns:
            The credential value with whitespace trimmed

        Raises:
            AttributeError: If the credential is not found in files or environment
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Try to load from file in $CREDENTIALS_DIRECTORY
        creds_dir = os.environ.get("CREDENTIALS_DIRECTORY")
        if creds_dir:
            cred_file = Path(creds_dir) / name
            if cred_file.exists():
                value = cred_file.read_text().strip()
                self._cache[name] = value
                return value

        # Fall back to environment variable (uppercase)
        env_name = name.upper()
        if env_name in os.environ:
            value = os.environ[env_name].strip()
            self._cache[name] = value
            return value

        # Neither exists - raise error
        raise AttributeError(
            f"Credential '{name}' not found in $CREDENTIALS_DIRECTORY/{name} or ${env_name}"
        )

    def clear_cache(self) -> None:
        """Clear the credential cache. Useful for testing."""
        self._cache.clear()

    def cache_len(self) -> int:
        return len(self._cache)
