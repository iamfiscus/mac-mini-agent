"""Marionette connection management."""

import sys
from contextlib import contextmanager

from marionette_driver.marionette import Marionette


@contextmanager
def connect(host: str = "127.0.0.1", port: int = 2828):
    """Connect to a running Firefox instance via Marionette.

    Firefox must be started with --marionette flag.
    """
    client = Marionette(host=host, port=port)
    try:
        client.start_session()
        yield client
    except ConnectionRefusedError:
        print(
            "Error: Cannot connect to Firefox on "
            f"{host}:{port}. Is Firefox running with --marionette?",
            file=sys.stderr,
        )
        raise SystemExit(1)
    finally:
        try:
            client.delete_session()
        except Exception:
            pass
