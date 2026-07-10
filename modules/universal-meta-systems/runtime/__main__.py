"""Enable `python -m runtime` from the module dir."""
from .runtime import main

if __name__ == "__main__":
    raise SystemExit(main())
