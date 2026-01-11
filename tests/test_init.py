import os

def test_project_structure():
    assert os.path.exists("app")
    assert os.path.exists("requirements.txt")
    assert os.path.exists("pyproject.toml")
    assert os.path.exists(".env")
    assert os.path.exists("tests")

def test_app_structure():
    assert os.path.exists("app/core")
    assert os.path.exists("app/bot")
    assert os.path.exists("app/utils")
