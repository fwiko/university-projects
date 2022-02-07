"""Module containing many multi-purpose functions.
"""


def padded(text: str, padding: int = 1, **kwargs) -> str:
    """Adds 'padding' to the top and bottop of a string

    Args:
        text (str): The string to pad.
        padding (int, optional): Amount of padding on top and bottom. Defaults to 1.

    Returns:
        str: The padded string.
    """
    return (
        "\n" * kwargs.get("top", padding) + text + "\n" * kwargs.get("bottom", padding)
    )
