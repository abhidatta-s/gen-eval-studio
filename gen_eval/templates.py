"""Node 2: render_template.

Turns a template like "Caption for {product}" plus variables into plain text.
"""

from typing import Dict


def render_template(template: str, variables: Dict[str, str]) -> str:
    """Fill the {placeholders} in `template` using `variables`.

    Python's str.format raises KeyError when a variable is missing. That
    message is hard to read, so we catch it and explain what went wrong.
    """
    try:
        return template.format(**variables)
    except KeyError as error:
        missing_name = error.args[0]
        raise ValueError(
            "Template needs the variable '" + str(missing_name)
            + "' but it was not provided. Template: " + template
        )
