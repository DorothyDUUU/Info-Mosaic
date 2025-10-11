import re

# ------- helpers -------
def load_json(path):
    """
    Load the JSON file from the specified path and return its content.
    """
    with open(path, "r", encoding="utf-8") as f:
        import json
        return json.load(f)

def dict_to_args_str(d: dict) -> str:
    """
    Convert a parameter dictionary to a string like (key1=val1, key2=val2, ...).
    Rules:
    - str: Wrap with quotes, e.g., "abc"
    - int/float/bool: Output as-is
    - None: Output None
    - list/tuple: Use [ ... ], format inner elements recursively
    - dict: Use { ... }, format inner elements recursively
    - Other types: Use repr()
    """
    # Remove non-printable characters from strings
    def clean_string(s):
        if isinstance(s, str):
            # Remove U+00A0 non-breaking space and other possible non-printable characters
            s = s.replace('\u00a0', ' ')
            # 只保留可打印字符
            s = ''.join(c for c in s if c.isprintable() or c in '\t\n\r')
        return s
        
    def format_val(v):
        if isinstance(v, str):
            v = clean_string(v)
            return repr(v)  # Add quotes and support escape characters
        elif isinstance(v, (int, float, bool)) or v is None:
            return str(v)
        elif isinstance(v, (list, tuple)):
            return "[" + ", ".join(format_val(x) for x in v) + "]"
        elif isinstance(v, dict):
            # Clean the keys of the dictionary
            cleaned_dict = {clean_string(k): val for k, val in v.items()}
            return "{" + ", ".join(f"{repr(clean_string(k))}: {format_val(val)}" for k, val in cleaned_dict.items()) + "}"
        else:
            return repr(v)

    # First clean the dictionary keys
    cleaned_dict = {clean_string(k): v for k, v in d.items()}
    parts = [f"{clean_string(k)}={format_val(v)}" for k, v in cleaned_dict.items()]
    result = "(" + ", ".join(parts) + ")"
    # Clean the entire generated string one last time
    return clean_string(result)


_SIMPLE_TYPE_MAP = {
    "string": "string", "str": "string",
    "int": "integer", "integer": "integer",
    "float": "number", "number": "number",
    "bool": "boolean", "boolean": "boolean",
    "null": "null", "none": "null",
}

def _normalize_enum_tokens(type_expr: str):
    """
    Extract explicit enums: "A"|"B"|None/Null
    返回 (enum_values, has_null, is_enum)
    """
    parts = [p.strip() for p in type_expr.split("|")]
    enum_vals, has_null, saw_quoted = [], False, False
    for p in parts:
        if p.lower() in {"none", "null"}:
            has_null = True
            continue
        m = re.fullmatch(r'"([^"]+)"', p) or re.fullmatch(r"'([^']+)'", p)
        if m:
            saw_quoted = True
            enum_vals.append(m.group(1))
    return enum_vals, has_null, saw_quoted

def _parse_param_line_strict(line: str):
    """
    Strictly parse a line of parameter definition:
      name(type_union): description
    - Supports union types: string|int|list[string]|null, etc.
    - Supports explicit enums: "OPEN"|"CLOSED"|None
    Returns: (param_name, param_schema)
    """
    line = str(line).strip()
    m = re.match(r'^([^(:\s]+)\(([^)]+)\):\s*(.*)$', line)
    if not m:
        # Fallback: When the type cannot be parsed, treat it as a string.
        name = re.sub(r'[:\s].*$', '', line).strip() or "param"
        return name, {"type": "string", "description": line}

    name, type_expr, desc = m.group(1).strip(), m.group(2).strip(), (m.group(3) or "").strip()

    # --- First check if it's an explicit enum ---
    enum_vals, has_null, is_enum = _normalize_enum_tokens(type_expr)
    if is_enum:
        schema = {"type": ["string", "null"] if has_null else "string", "enum": enum_vals + ([None] if has_null else [])}
        if desc:
            schema["description"] = desc
        return name, schema

    # --- Parse union basic types / list[...] ---
    tokens = [t.strip() for t in type_expr.split("|")] if "|" in type_expr else [type_expr.strip()]
    simple_types = set()     # 非数组的基本类型集合（string/integer/number/boolean/null）
    arrays_inner = set()     # 数组的元素类型集合（string/integer/...）

    for t in tokens:
        tl = t.lower()
        if tl.startswith("list[") and tl.endswith("]"):
            inner = tl[5:-1].strip().lower()
            arrays_inner.add(_SIMPLE_TYPE_MAP.get(inner, "string"))
        else:
            simple_types.add(_SIMPLE_TYPE_MAP.get(tl, "string"))

    # Schema construction rules:
    # 1) If there is only one array element type and any number of non-array types:
    #    Use "type": [..] + top-level "items" (the validator will ignore "items" when the type is not "array")
    if len(arrays_inner) <= 1:
        types = set(simple_types)
        if arrays_inner:
            types.add("array")
        # Generate schema
        if len(types) == 1:
            schema: dict = {"type": list(types)[0]}
        else:
            schema = {"type": sorted(list(types))}  # Order does not affect semantics

        # If the type set contains "array", add the "items" field
        if "array" in types and arrays_inner:
            # If there is no inner type, use "string" as default; otherwise, use the only inner type
            inner_t = list(arrays_inner)[0] if arrays_inner else "string"
            schema["items"] = {"type": inner_t}

        if desc:
            schema["description"] = desc
        return name, schema

    # 2) If there are multiple array element types (e.g., list[string]|list[int]), use "oneOf" to distinguish branches
    one_of = []
    # Array branches
    for inner_t in sorted(list(arrays_inner)):
        one_of.append({"type": "array", "items": {"type": inner_t}})
    # Non-array branches
    for st in sorted(list(simple_types)):
        one_of.append({"type": st})
    schema = {"oneOf": one_of}
    if desc:
        schema["description"] = desc
    return name, schema

# ------- main converters (STRICT JSON Schema) -------

def tool_to_function_strict(tool: dict):
    """
    Strict JSON Schema:
      - Do not determine optionality based on None; 'required' is determined only by 'required_params'
      - Union types -> Use "type":[...] or oneOf (when there are multiple array element types)
      - Enum contains null -> The 'enum' includes null, and 'type' includes "null"
      - Do not remove duplicate names
    Expected input fields:
      - tool["name"]: Function name
      - tool["description"]: Description
      - tool["required_params"]: list[str], in the format of 'foo(string|None): desc'
    """
    fn_name = str(tool.get("name", "tool")).strip()
    description = (tool.get("description") or "").strip()
    required_params = tool.get("required_params") or []

    properties, required = {}, []
    for line in required_params:
        pname, pschema = _parse_param_line_strict(line)
        properties[pname] = pschema
        # Strict: Whether a parameter is required is determined only by 'required_params' 
        # (since the line appears, mark it as required)
        required.append(pname)

    params_obj = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        params_obj["required"] = required

    return {
        "type": "function",
        "function": {
            "name": fn_name,
            "description": description,
            "parameters": params_obj,
        },
    }

def convert_tools_to_schema_list(tools_list):
    """
    Strict JSON Schema conversion:
      - Do not handle duplicate names (output as-is)
      - Do not treat |None as optional
      - Strictly express union/enum/null
    Returns: List of function schemas
    """
    out = []
    for tool in tools_list:
        try:
            out.append(tool_to_function_strict(tool))
        except Exception as e:
            raw_name = str(tool.get("name", "tool")).strip()
            # Minimum fault tolerance: Degrade to a function with no parameters
            out.append({
                "type": "function",
                "function": {
                    "name": raw_name,
                    "description": (tool.get("description") or "").strip(),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            })
            print(f"[WARN] Failed to convert {raw_name}: {e}")
    return out
