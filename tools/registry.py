import inspect
from typing import Any, Dict

_JSON_SCHEMA_TYPE_MAP = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Any] = {}

    def register(self, tool: Any):
        """Register a tool instance under its name"""
        self._tools[tool.__name__] = tool

    def run(self, name: str, arg: Any) -> Any:
        """Run a tool by name with the given argument"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        return self._tools[name](**arg)

    @property
    def tools(self) -> Dict[str, Any]:
        return self._tools

    def get_tools(self):
        res = []
        for func_name, tool in self._tools.items():
            sig = inspect.signature(tool)
            params = {}
            required = []
            for name, param in sig.parameters.items():
                json_type_str = ""

                annotation = param.annotation
                assert (
                    annotation is not inspect.Parameter.empty
                    and hasattr(annotation, "__name__")
                    and annotation.__name__ in _JSON_SCHEMA_TYPE_MAP
                ), f"Unsupported type: {annotation.__name__}"

                json_type_str = _JSON_SCHEMA_TYPE_MAP[annotation.__name__]

                params[name] = {
                    "type": json_type_str,
                }
                if param.default is inspect.Parameter.empty:
                    required.append(name)

            res.append(
                {
                    "type": "function",
                    "name": func_name,
                    "description": tool.__doc__.strip(),
                    "parameters": {
                        "type": "object",
                        "properties": params,
                        "required": required,
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            )
        return res
