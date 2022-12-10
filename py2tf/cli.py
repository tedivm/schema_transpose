from importlib import import_module
from typing import Union

import typer

from .converters.jinja import JinjaConverter
from .converters.markdown import MarkdownConverter

app = typer.Typer()


@app.command()
def main(model_path, format: str = typer.Option("hcl")):
    module_path, class_name = model_path.split(":", 2)
    module = import_module(module_path)
    model = getattr(module, class_name)

    converter: Union[JinjaConverter, MarkdownConverter]
    if format == "markdown":
        converter = MarkdownConverter(format=format)
    else:
        converter = JinjaConverter(format=format)

    print(converter.convert(model))


if __name__ == "__main__":
    app()
