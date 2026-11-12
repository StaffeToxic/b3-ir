import pytest

from b3_ir import __version__
from b3_ir.cli import EXIT_USAGE, main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_shows_help_and_disclaimer(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert "não é consultoria tributária" in captured.err
    assert "COMANDO" in captured.out


def test_disclaimer_can_be_suppressed(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--sem-aviso"])
    assert "consultoria" not in capsys.readouterr().err
