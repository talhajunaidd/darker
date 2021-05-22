from pathlib import Path

import pytest

from darker.black_diff import BlackArgs, read_black_config, run_black
from darker.utils import TextDocument


@pytest.mark.kwparametrize(
    dict(
        config_path=None, config_lines=["line-length = 79"], expect={"line_length": 79}
    ),
    dict(
        config_path="custom.toml",
        config_lines=["line-length = 99"],
        expect={"line_length": 99},
    ),
    dict(
        config_path="custom.toml",
        config_lines=["skip-string-normalization = true"],
        expect={"skip_string_normalization": True},
    ),
    dict(
        config_path="custom.toml",
        config_lines=["skip-string-normalization = false"],
        expect={"skip_string_normalization": False},
    ),
    dict(
        config_path="custom.toml", config_lines=["target-version = ['py37']"], expect={}
    ),
    dict(config_path="custom.toml", config_lines=["include = '\\.pyi$'"], expect={}),
    dict(config_path="custom.toml", config_lines=["exclude = '\\.pyx$'"], expect={}),
)
def test_black_config(tmpdir, config_path, config_lines, expect):
    tmpdir = Path(tmpdir)
    src = tmpdir / "src.py"
    toml = tmpdir / (config_path or "pyproject.toml")

    toml.write_text("[tool.black]\n{}\n".format("\n".join(config_lines)))

    config = read_black_config(src, config_path and str(toml))
    assert config == expect


@pytest.mark.parametrize("encoding", ["utf-8", "iso-8859-1"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_run_black(tmpdir, encoding, newline):
    """Running Black through its Python internal API gives correct results"""
    src = TextDocument.from_lines(
        [f"# coding: {encoding}", "print ( 'touché' )"],
        encoding=encoding,
        newline=newline,
    )

    result = run_black(Path(tmpdir / "src.py"), src, BlackArgs())

    assert result.lines == (
        f"# coding: {encoding}",
        'print("touché")',
    )
    assert result.encoding == encoding
    assert result.newline == newline
