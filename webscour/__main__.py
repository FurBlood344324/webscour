"""`python3 -m webscour`: the same entry point the `wsc` console script uses."""

import sys

from .cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
