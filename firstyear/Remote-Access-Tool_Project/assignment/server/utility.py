def padstr(text: str, padding: int = 1, *, top: int = None, bottom: int = None) -> str:
    """return a string with spacing on the top and/or bottom

    Args:
        text (str): The string to pad.
        padding (int, optional): Amount of spacing to apply to the top and bottom. Defaults to 1.

    Returns:
        str: The padded string.
    """
    return "\n" * (top or padding) + text + "\n" * (bottom or padding)
