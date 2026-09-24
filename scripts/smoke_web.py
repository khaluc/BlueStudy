"""Live browser regression entry point for the current notebook interface."""
from scripts.smoke_notebook import main as notebook_main


def main():
    notebook_main(run_live=True)


if __name__ == "__main__":
    main()
