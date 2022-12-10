import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, cast

from glom import glom  # type: ignore
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel

from py2tf import validators

env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))

SETTINGS = {
    "hcl": {
        "template": cast(Template, env.get_template("hcl.tf")),
        "delimiter": "\n\n",
    },
    "tfvars": {
        "template": cast(Template, env.get_template("variable.tfvars")),
        "delimiter": "\n",
    },
    "module": {
        "template": cast(Template, env.get_template("module_params.tf")),
        "delimiter": "\n",
        "wrapper": cast(Template, env.get_template("module_wrapper.tf")),
    },
}


class JinjaConverter:

    numbers: List[str] = ["int", "float", "integer"]
    objects: List[str] = ["dict", "object"]
    pass_through_fields: List[str] = ["string"]

    def __init__(self, format="hcl") -> None:
        if format not in SETTINGS:
            raise ValueError(f"Format must be hcl or tfvars")
        self.template = SETTINGS[format]["template"]
        self.delimiter = SETTINGS[format]["delimiter"]
        self.wrapper = cast(Template, SETTINGS[format]["wrapper"]) if "wrapper" in SETTINGS[format] else None

    def convert(self, model: BaseModel) -> str:
        schema = model.schema()
        output = ""
        for field_name, field_data in schema["properties"].items():
            output += self.convert_field(schema, field_name, field_data)
            output += self.delimiter  # type: ignore

        if self.wrapper:
            output = self.wrapper.render(parameters=output)

        return output.strip()

    def _get_reference(self, schema, reference):
        # Convert reference into glom format.
        path = reference.strip("#/").replace("/", ".")
        return glom(schema, path)

    def convert_field(self, schema, field_name, field_data) -> Any:
        field_data = self.get_field_data(schema, field_name, field_data)
        return self.template.render(**field_data)  # type: ignore

    def get_field_data(self, schema, field_name, field_data) -> Dict[str, Any]:
        # This field references another field. Swap the field_data out.
        if "$ref" in field_data:
            field_data = self._get_reference(schema, field_data["$ref"])

        if "allOf" in field_data:
            for parent_model in field_data["allOf"]:
                # Attempt to keep any existing descriptions instead of using the enum descriptions.
                field_description = False
                if "description" in field_data:
                    field_description = field_data["description"]

                if "$ref" in parent_model:
                    parent_model = self._get_reference(schema, parent_model["$ref"])
                field_data |= parent_model

                # If there was a field description add it back.
                if field_description:
                    field_data["description"] = field_description

        type, type_rules = self.get_type(field_name, field_data)

        # Since "null" and "false" are valid defaults we can't rely on default being defined.
        # To get around that we have `has_default`.

        has_default = False
        default = None
        required = field_name in schema.get("required", {})
        if "default" in field_data or not required:
            has_default = True
            default = self.get_default(type, field_data.get("default"))

        rules = self.get_validation_list(field_name, field_data, allow_none=not required)
        if type_rules:
            rules += type_rules

        return {
            "name": field_name,
            "type": type,
            "description": field_data.get("description"),
            "has_default": has_default,
            "default": default,
            "sensitive": "writeOnly" in field_data,
            "required": required,
            "validation_rules": rules,
        }

    def get_type(self, field_name, field_data):

        type_validators = []

        if "enum" in field_data:
            if "type" not in field_data:
                field_data["type"] = "string"
            type_validators.append(validators.oneof(field_name, field_data["enum"], allow_none=False))

        if "type" not in field_data:
            print(field_data)
            raise ValueError(f"Unknown type for {field_name}")

        field_type = field_data["type"].lower()

        if field_type in self.pass_through_fields:
            return field_type, type_validators

        if field_type in self.numbers:
            return "number", type_validators

        if field_type == "array":
            subtype = self.get_subtype(field_name, field_data)
            return f"list({subtype})", None

        if field_type in self.objects:
            subtype = self.get_subtype(field_name, field_data)
            return f"map({subtype})", None

        if field_type == "boolean":
            return "bool", None

        return "string", None

    def get_subtype(self, field_name, field_data):
        subtype = "any"
        if "items" in field_data:
            if "type" in field_data["items"]:
                subtype, rules = self.get_type(field_name, field_data["items"])
        if "additionalProperties" in field_data and "type" in field_data["additionalProperties"]:
            subtype = field_data["additionalProperties"]["type"]
        return subtype

    def get_default(self, type, value):
        if type.startswith("list"):
            return textwrap.indent(json.dumps(value, indent=2), "  ").strip() if value else "[]"
        if type.startswith("map"):
            return textwrap.indent(json.dumps(value, indent=2), "  ").strip() if value else "{}"

        # Custom Nulls above this line

        if value == None:
            return "null"
        if type == "number":
            return value
        if type == "string":
            escaped_value = str(value).replace('"', '\\"')
            return f'"{escaped_value}"'
        if type == "bool":
            return "true" if value else "false"

        if value:
            return value

        return "null"

    def get_validation_list(self, field_name, field_data, allow_none):
        tf_rules = []
        for key, value in field_data.items():
            if not hasattr(validators, key.lower()):
                continue
            rule = getattr(validators, key.lower())(field_name, value, allow_none)
            if rule:
                tf_rules.append(rule)

        return tf_rules
