"""Package version information sourced from setuptools_scm."""

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover - occurs in editable installs before build
    try:
        from importlib.metadata import PackageNotFoundError, version as _pkg_version
    except ImportError:  # pragma: no cover - very old Python
        __version__ = "0.0.0"
    else:
        try:
            __version__ = _pkg_version("agent-ethan2")
        except PackageNotFoundError:
            __version__ = "0.0.0"
