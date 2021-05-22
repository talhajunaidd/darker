from argparse import ArgumentParser, Namespace
from textwrap import dedent

import pytest

from darker.config import (
    TomlArrayLinesEncoder,
    dump_config,
    get_effective_config,
    get_modified_config,
    load_config,
    replace_log_level_name,
)


@pytest.mark.kwparametrize(
    dict(list_value=[], expect="[\n]"),
    dict(list_value=["one value"], expect='[\n    "one value",\n]'),
    dict(list_value=["two", "values"], expect='[\n    "two",\n    "values",\n]'),
    dict(
        list_value=[
            "a",
            "dozen",
            "short",
            "string",
            "values",
            "in",
            "the",
            "list",
            "of",
            "strings",
            "to",
            "format",
        ],
        expect=(
            '[\n    "a",\n    "dozen",\n    "short",\n    "string",\n    "values"'
            ',\n    "in",\n    "the",\n    "list",\n    "of",\n    "strings"'
            ',\n    "to",\n    "format",\n]'
        ),
    ),
)
def test_toml_array_lines_encoder(list_value, expect):
    result = TomlArrayLinesEncoder().dump_list(list_value)

    assert result == expect


@pytest.mark.kwparametrize(
    dict(log_level=0, expect="NOTSET"),
    dict(log_level=10, expect="DEBUG"),
    dict(log_level=20, expect="INFO"),
    dict(log_level=30, expect="WARNING"),
    dict(log_level=40, expect="ERROR"),
    dict(log_level=50, expect="CRITICAL"),
    dict(log_level="DEBUG", expect=10),
    dict(log_level="INFO", expect=20),
    dict(log_level="WARNING", expect=30),
    dict(log_level="WARN", expect=30),
    dict(log_level="ERROR", expect=40),
    dict(log_level="CRITICAL", expect=50),
    dict(log_level="FOOBAR", expect="Level FOOBAR"),
)
def test_replace_log_level_name(log_level, expect):
    config = {} if log_level is None else {"log_level": log_level}
    replace_log_level_name(config)

    assert config["log_level"] == expect


@pytest.mark.kwparametrize(
    dict(),
    dict(cwd="level1"),
    dict(cwd="level1/level2"),
    dict(cwd="has_git", expect={}),
    dict(cwd="has_git/level1", expect={}),
    dict(cwd="has_pyproject", expect={"CONFIG_PATH": "has_pyproject"}),
    dict(cwd="has_pyproject/level1", expect={"CONFIG_PATH": "has_pyproject"}),
    dict(srcs=["root.py"]),
    dict(srcs=["../root.py"], cwd="level1"),
    dict(srcs=["../root.py"], cwd="has_git"),
    dict(srcs=["../root.py"], cwd="has_pyproject"),
    dict(srcs=["root.py", "level1/level1.py"]),
    dict(srcs=["../root.py", "level1.py"], cwd="level1"),
    dict(srcs=["../root.py", "../level1/level1.py"], cwd="has_git"),
    dict(srcs=["../root.py", "../level1/level1.py"], cwd="has_pyproject"),
    dict(srcs=["has_pyproject/pyp.py", "level1/level1.py"]),
    dict(srcs=["../has_pyproject/pyp.py", "level1.py"], cwd="level1"),
    dict(srcs=["../has_pyproject/pyp.py", "../level1/level1.py"], cwd="has_git"),
    dict(srcs=["pyp.py", "../level1/level1.py"], cwd="has_pyproject"),
    dict(
        srcs=["has_pyproject/level1/l1.py", "has_pyproject/level1b/l1b.py"],
        expect={"CONFIG_PATH": "has_pyproject"},
    ),
    dict(
        srcs=["../has_pyproject/level1/l1.py", "../has_pyproject/level1b/l1b.py"],
        cwd="level1",
        expect={"CONFIG_PATH": "has_pyproject"},
    ),
    dict(
        srcs=["../has_pyproject/level1/l1.py", "../has_pyproject/level1b/l1b.py"],
        cwd="has_git",
        expect={"CONFIG_PATH": "has_pyproject"},
    ),
    dict(
        srcs=["level1/l1.py", "level1b/l1b.py"],
        cwd="has_pyproject",
        expect={"CONFIG_PATH": "has_pyproject"},
    ),
    dict(
        srcs=["full_example/full.py"],
        expect={
            "check": True,
            "diff": True,
            "isort": True,
            "lint": ["flake8", "mypy", "pylint"],
            "log_level": 10,
            "revision": "main",
            "src": ["src", "tests"],
        },
    ),
    srcs=[],
    cwd=".",
    expect={"CONFIG_PATH": "."},
)
def test_load_config(
    find_project_root_cache_clear, tmp_path, monkeypatch, srcs, cwd, expect
):
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text('[tool.darker]\nCONFIG_PATH = "."\n')
    (tmp_path / "level1/level2").mkdir(parents=True)
    (tmp_path / "has_git/.git").mkdir(parents=True)
    (tmp_path / "has_git/level1").mkdir()
    (tmp_path / "has_pyproject/level1").mkdir(parents=True)
    (tmp_path / "has_pyproject/pyproject.toml").write_text(
        '[tool.darker]\nCONFIG_PATH = "has_pyproject"\n'
    )
    (tmp_path / "full_example").mkdir()
    (tmp_path / "full_example/pyproject.toml").write_text(
        dedent(
            """
            [tool.darker]
            src = [
                "src",
                "tests",
            ]
            revision = "main"
            diff = true
            check = true
            isort = true
            lint = [
                "flake8",
                "mypy",
                "pylint",
            ]
            log_level = "DEBUG"
            """
        )
    )
    monkeypatch.chdir(tmp_path / cwd)

    result = load_config(srcs)

    assert result == expect


@pytest.mark.kwparametrize(
    dict(args=Namespace(), expect={}),
    dict(args=Namespace(one="option"), expect={"one": "option"}),
    dict(args=Namespace(log_level=10), expect={"log_level": "DEBUG"}),
    dict(
        args=Namespace(two="options", log_level=20),
        expect={"two": "options", "log_level": "INFO"},
    ),
)
def test_get_effective_config(args, expect):
    """get_effective_config() resolves effective configuration correctly"""
    result = get_effective_config(args)

    assert result == expect


@pytest.mark.kwparametrize(
    dict(args=Namespace(), expect={}),
    dict(args=Namespace(unknown="option"), expect={"unknown": "option"}),
    dict(args=Namespace(log_level=10), expect={"log_level": "DEBUG"}),
    dict(args=Namespace(names=[], int=42, string="fourty-two"), expect={"names": []}),
    dict(
        args=Namespace(names=["bar"], int=42, string="fourty-two"),
        expect={"names": ["bar"]},
    ),
    dict(
        args=Namespace(names=["foo"], int=43, string="fourty-two"), expect={"int": 43}
    ),
    dict(args=Namespace(names=["foo"], int=42, string="one"), expect={"string": "one"}),
)
def test_get_modified_config(args, expect):
    parser = ArgumentParser()
    parser.add_argument("names", nargs="*", default=["foo"])
    parser.add_argument("--int", dest="int", default=42)
    parser.add_argument("--string", default="fourty-two")
    result = get_modified_config(parser, args)

    assert result == expect


@pytest.mark.kwparametrize(
    dict(config={}, expect="[tool.darker]\n"),
    dict(config={"str": "value"}, expect='[tool.darker]\nstr = "value"\n'),
    dict(config={"int": 42}, expect="[tool.darker]\nint = 42\n"),
    dict(config={"float": 4.2}, expect="[tool.darker]\nfloat = 4.2\n"),
    dict(
        config={"list": ["foo", "bar"]},
        expect=dedent(
            """\
            [tool.darker]
            list = [
                "foo",
                "bar",
            ]
            """
        ),
    ),
    dict(
        config={
            "src": ["main.py"],
            "revision": "master",
            "diff": False,
            "check": False,
            "isort": False,
            "lint": [],
            "config": None,
            "log_level": "DEBUG",
            "skip_string_normalization": None,
            "line_length": None,
        },
        expect=dedent(
            """\
            [tool.darker]
            src = [
                "main.py",
            ]
            revision = "master"
            diff = false
            check = false
            isort = false
            lint = [
            ]
            log_level = "DEBUG"
            """
        ),
    ),
)
def test_dump_config(config, expect):
    """dump_config() outputs configuration correctly in the TOML format"""
    result = dump_config(config)

    assert result == expect
