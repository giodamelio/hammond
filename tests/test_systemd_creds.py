"""Tests for the SystemdCreds singleton class."""

import pytest
from pathlib import Path
from collections.abc import Generator
from hammond.systemd_creds import SystemdCreds


@pytest.fixture
def clean_creds() -> Generator[SystemdCreds, None, None]:
    """Fixture to ensure a clean SystemdCreds instance for each test."""
    # Clear cache before each test
    creds = SystemdCreds()
    creds.clear_cache()
    yield creds
    # Clean up after test
    creds.clear_cache()


@pytest.fixture
def temp_creds_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to create a temporary credentials directory."""
    creds_dir = tmp_path / "credentials"
    creds_dir.mkdir()
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(creds_dir))
    return creds_dir


class TestSystemdCredsSingleton:
    """Test the singleton pattern behavior."""

    def test_singleton_same_instance(self, clean_creds: SystemdCreds) -> None:
        """Test that multiple calls return the same instance."""
        creds1 = SystemdCreds()
        creds2 = SystemdCreds()
        assert creds1 is creds2

    def test_singleton_shared_cache(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test that the cache is shared across instances."""
        # Create a credential file
        _ = (temp_creds_dir / "api_key").write_text("test_value")

        creds1 = SystemdCreds()
        value1 = creds1.api_key

        creds2 = SystemdCreds()

        # Ensure it hits the cache by changing the file
        # The value should stay the same
        _ = (temp_creds_dir / "api_key").write_text("another_value")

        assert creds2.api_key == value1


class TestFileCredentials:
    """Test loading credentials from files."""

    def test_load_from_file(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test loading a credential from a file."""
        _ = (temp_creds_dir / "database_password").write_text("secret123")

        creds = SystemdCreds()
        assert creds.database_password == "secret123"

    def test_trim_whitespace_from_file(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test that whitespace is trimmed from file contents."""
        _ = (temp_creds_dir / "api_token").write_text("  token_value  \n\t")

        creds = SystemdCreds()
        assert creds.api_token == "token_value"

    def test_empty_file(self, clean_creds: SystemdCreds, temp_creds_dir: Path) -> None:
        """Test handling of empty credential files."""
        _ = (temp_creds_dir / "empty_cred").write_text("")

        creds = SystemdCreds()
        assert creds.empty_cred == ""

    def test_multiline_file_trimmed(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test that multiline content is trimmed properly."""
        _ = (temp_creds_dir / "multiline").write_text("\n\nvalue\n\n")

        creds = SystemdCreds()
        assert creds.multiline == "value"


class TestEnvironmentVariables:
    """Test loading credentials from environment variables."""

    def test_load_from_env(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading a credential from an environment variable."""
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgres://localhost")

        creds = SystemdCreds()
        assert creds.database_url == "postgres://localhost"

    def test_trim_whitespace_from_env(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that whitespace is trimmed from env vars."""
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
        monkeypatch.setenv("API_KEY", "  key123  \n")

        creds = SystemdCreds()
        assert creds.api_key == "key123"

    def test_env_fallback_when_file_missing(
        self,
        clean_creds: SystemdCreds,
        temp_creds_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that env vars are used as fallback when file doesn't exist."""
        monkeypatch.setenv("BACKUP_TOKEN", "env_token")

        creds = SystemdCreds()
        assert creds.backup_token == "env_token"


class TestPriority:
    """Test priority between file and environment variables."""

    def test_file_takes_priority_over_env(
        self,
        clean_creds: SystemdCreds,
        temp_creds_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that file credentials take priority over environment variables."""
        _ = (temp_creds_dir / "secret").write_text("file_value")
        monkeypatch.setenv("SECRET", "env_value")

        creds = SystemdCreds()
        assert creds.secret == "file_value"


class TestCaching:
    """Test credential caching behavior."""

    def test_caching_file_credential(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test that file credentials are cached."""
        cred_file = temp_creds_dir / "cached_cred"
        _ = cred_file.write_text("original")

        creds = SystemdCreds()
        assert creds.cached_cred == "original"

        # Modify the file
        _ = cred_file.write_text("modified")

        # Should still return cached value
        assert creds.cached_cred == "original"

    def test_caching_env_credential(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that env credentials are cached."""
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
        monkeypatch.setenv("CACHED_ENV", "original")

        creds = SystemdCreds()
        assert creds.cached_env == "original"

        # Modify env var
        monkeypatch.setenv("CACHED_ENV", "modified")

        # Should still return cached value
        assert creds.cached_env == "original"

    def test_clear_cache(self, clean_creds: SystemdCreds, temp_creds_dir: Path) -> None:
        """Test clearing the cache."""
        cred_file = temp_creds_dir / "clearable"
        _ = cred_file.write_text("original")

        creds = SystemdCreds()
        assert creds.clearable == "original"

        # Modify and clear cache
        _ = cred_file.write_text("modified")
        creds.clear_cache()

        # Should read the new value
        assert creds.clearable == "modified"


class TestErrorHandling:
    """Test error handling for missing credentials."""

    def test_missing_credential_raises_error(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that accessing a missing credential raises AttributeError."""
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)

        creds = SystemdCreds()
        with pytest.raises(AttributeError) as exc_info:
            _ = creds.nonexistent_cred

        assert "nonexistent_cred" in str(exc_info.value)
        assert "NONEXISTENT_CRED" in str(exc_info.value)

    def test_error_message_includes_both_sources(
        self, clean_creds: SystemdCreds, temp_creds_dir: Path
    ) -> None:
        """Test that error message mentions both file and env var."""
        creds = SystemdCreds()
        with pytest.raises(AttributeError) as exc_info:
            _ = creds.missing

        error_msg = str(exc_info.value)
        assert "missing" in error_msg  # file name
        assert "MISSING" in error_msg  # env var name


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_mixed_credentials_scenario(
        self,
        clean_creds: SystemdCreds,
        temp_creds_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test a realistic scenario with mixed file and env credentials."""
        # Set up some file-based credentials
        _ = (temp_creds_dir / "db_password").write_text("  db_secret  ")
        _ = (temp_creds_dir / "api_key").write_text("file_api_key")

        # Set up some env-based credentials
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        monkeypatch.setenv("API_KEY", "env_api_key")  # Should be overridden by file

        creds = SystemdCreds()

        # File credentials should work
        assert creds.db_password == "db_secret"
        assert creds.api_key == "file_api_key"  # File takes priority

        # Env credentials should work
        assert creds.redis_url == "redis://localhost:6379"

        # All should be cached
        assert creds.cache_len() == 3

    def test_no_credentials_directory_set(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test behavior when CREDENTIALS_DIRECTORY is not set."""
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
        monkeypatch.setenv("FALLBACK_SECRET", "env_only")

        creds = SystemdCreds()
        # Should still work with env vars only
        assert creds.fallback_secret == "env_only"

    def test_credentials_directory_is_empty_string(
        self, clean_creds: SystemdCreds, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test behavior when CREDENTIALS_DIRECTORY is an empty string."""
        monkeypatch.setenv("CREDENTIALS_DIRECTORY", "")
        monkeypatch.setenv("BACKUP_VAL", "from_env")

        creds = SystemdCreds()
        # Should fall back to env var
        assert creds.backup_val == "from_env"
