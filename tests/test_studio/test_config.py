"""Tests for studio configuration."""

from __future__ import annotations

from pathlib import Path

from fireflyframework_genai.studio.config import StudioConfig


class TestStudioConfigDefaults:
    def test_default_host(self) -> None:
        cfg = StudioConfig()
        assert cfg.host == "127.0.0.1"

    def test_default_port(self) -> None:
        cfg = StudioConfig()
        assert cfg.port == 8470

    def test_default_open_browser(self) -> None:
        cfg = StudioConfig()
        assert cfg.open_browser is True

    def test_default_dev_mode(self) -> None:
        cfg = StudioConfig()
        assert cfg.dev_mode is False

    def test_default_projects_dir(self) -> None:
        cfg = StudioConfig()
        assert cfg.projects_dir == Path.home() / ".firefly-studio" / "projects"

    def test_default_log_level(self) -> None:
        cfg = StudioConfig()
        assert cfg.log_level == "info"


class TestStudioConfigEnvOverrides:
    def test_host_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_HOST", "0.0.0.0")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.host == "0.0.0.0"

    def test_port_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_PORT", "9090")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.port == 9090

    def test_open_browser_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_OPEN_BROWSER", "false")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.open_browser is False

    def test_dev_mode_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_DEV_MODE", "true")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.dev_mode is True

    def test_log_level_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_LOG_LEVEL", "debug")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.log_level == "debug"

    def test_projects_dir_override(self, monkeypatch: object) -> None:
        monkeypatch.setenv("FIREFLY_STUDIO_PROJECTS_DIR", "/tmp/my-projects")  # type: ignore[attr-defined]
        cfg = StudioConfig()
        assert cfg.projects_dir == Path("/tmp/my-projects")
