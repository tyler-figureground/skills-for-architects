"""Atlas - map-driven tooling for studio shared drives."""

from importlib.metadata import PackageNotFoundError, version

# Read from the installed package, never typed here: a literal went stale across
# two releases - the 0.4.0 wheel shipped to the studio drive still said 0.3.0.
try:
    __version__ = version("studio-atlas")
except PackageNotFoundError:    # a source tree that was never installed
    __version__ = "0.0.0+unknown"
