from pathlib import PurePath

import pytest


@pytest.fixture()
def root_path() -> PurePath:
    return PurePath(__file__).parent.parent


@pytest.fixture()
def chdir_to_root(root_path: PurePath, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(root_path)


@pytest.fixture()
def app(chdir_to_root):
    from src.web.app import app
    return app
