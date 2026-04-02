"""Entry point for `python -m src.pipeline` — avoids RuntimeWarning from running main_pipeline as __main__."""
from src.pipeline.main_pipeline import main

if __name__ == "__main__":
    main()
