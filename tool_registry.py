import inspect
from typing import get_type_hints, get_origin, get_args, Union, Literal

tools = []
tool_functions = {}

json_schema_types = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null"
}




def get_tool_metadata(func):
    signature = inspect.signature(func)
    parameters_needed = signature.parameters
    parameter_types = get_type_hints(func)

    properties = {}
    required = []
    docstring = inspect.getdoc(func) or ""
    parameter_descriptions = {}
    
    if docstring and "Args:" in docstring:
        description_lines = docstring.split("Args:")[1].strip().splitlines()

        for line in description_lines:
            parts = line.split(":", 1)
            parameter_name = parts[0].strip()
            parameter_discription = parts[1].strip()
            parameter_descriptions[parameter_name] = parameter_discription


    for parameter in parameters_needed:
        if parameter == "json_songs":
            continue

        python_type = parameter_types[parameter]

        if get_origin(python_type) == list:
            item_type = get_args(python_type)[0]

            if get_origin(item_type) == Literal:
                properties[parameter] = {
                    "type": "array",
                    "items": {
                        "type": json_schema_types[type(get_args(item_type)[0])],
                        "enum": get_args(item_type)
                    }
                }

            else:
                properties[parameter] = {
                    "type": "array",
                    "items": {"type": json_schema_types[item_type]}
                }

        elif get_origin(python_type) == Union:
            python_types = []

            for data_type in get_args(python_type):
                python_types.append(json_schema_types[data_type])

            properties[parameter] = {
                "type": python_types
            }

        elif get_origin(python_type) == Literal:
            properties[parameter] = {
                "type": json_schema_types[type(get_args(python_type)[0])],
                "enum": get_args(python_type)}
            
        else:
            properties[parameter] = {
                "type": json_schema_types[python_type]
            }

        if parameter in parameter_descriptions:
            properties[parameter]["description"] = parameter_descriptions[parameter]


        if parameters_needed[parameter].default == inspect.Parameter.empty:
            required.append(parameter)

    parameters_schema = {
        "type": "object",
        "properties": properties,
        "required": required
    }

    return parameters_schema




def register_tool(func):
    tool_functions[func.__name__] = func
    parameters_schema = get_tool_metadata(func=func)
    docstring = inspect.getdoc(func) or ""
    tool_schema = {
    "type": "function",
    "function": {
        "name": func.__name__, 
        "description": docstring.split("Args:")[0].strip(),
        "parameters": parameters_schema
    }
}
    tools.append(tool_schema)
    return func


