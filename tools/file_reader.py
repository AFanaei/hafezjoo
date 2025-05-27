def read_file(path: str) -> str:
    """
    Read the contents of a file at the given path.
    """
    with open(path, "r") as f:
        return f.read()
