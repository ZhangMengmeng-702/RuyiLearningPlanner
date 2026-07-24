# -*- coding: utf-8 -*-
"""
Tool Registry — 工具注册表

参考 RuyiDailyStockAnalysis 的 registry.py，提供：
- ToolParameter / ToolDefinition 数据类
- @tool 装饰器自动注册
- OpenAI tools format Schema 生成
- 工具注册、发现和调用功能
"""

import importlib
import inspect
import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass(frozen=True)
class ToolPolicy:
    read_only: Optional[bool] = None
    side_effects: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    policy_status: str = "unknown"

    @classmethod
    def unknown(cls) -> "ToolPolicy":
        return cls()

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "read_only": self.read_only,
            "side_effects": list(self.side_effects),
            "permissions": list(self.permissions),
            "policy_status": self.policy_status,
        }


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable
    toolset: str = "default"
    policy: ToolPolicy = field(default_factory=ToolPolicy.unknown)
    emoji: str = ""
    max_result_size_chars: int = 100000

    def _params_json_schema(self) -> dict:
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in self.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        return schema

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._params_json_schema(),
            },
        }

    def to_public_descriptor(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "toolset": self.toolset,
            "emoji": self.emoji,
            "parameters": self._params_json_schema(),
            "policy": self.policy.to_public_dict(),
        }


class ToolRegistry:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._toolset_tools: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

    def register(self, name: str, toolset: str, schema: dict, handler: Callable,
                 check_fn: Optional[Callable] = None, emoji: str = "",
                 max_result_size_chars: int = 100000):
        parameters = _parse_schema_to_parameters(schema)
        tool_def = ToolDefinition(
            name=name,
            description=schema.get("description", ""),
            parameters=parameters,
            handler=handler,
            toolset=toolset,
            emoji=emoji,
            max_result_size_chars=max_result_size_chars,
        )

        with self._lock:
            self._tools[name] = tool_def

            if toolset not in self._toolset_tools:
                self._toolset_tools[toolset] = []
            if name not in self._toolset_tools[toolset]:
                self._toolset_tools[toolset].append(name)

        logger.info(f"工具已注册: {emoji} {name} (toolset: {toolset})")

    def register_definition(self, tool_def: ToolDefinition) -> None:
        with self._lock:
            self._tools[tool_def.name] = tool_def

            if tool_def.toolset not in self._toolset_tools:
                self._toolset_tools[tool_def.toolset] = []
            if tool_def.name not in self._toolset_tools[tool_def.toolset]:
                self._toolset_tools[tool_def.toolset].append(tool_def.name)

        logger.info(f"工具已注册: {tool_def.emoji} {tool_def.name} (toolset: {tool_def.toolset})")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def call_tool(self, name: str, args: dict) -> str:
        tool_def = self.get_tool(name)
        if not tool_def:
            return json.dumps({"success": False, "error": f"工具 {name} 不存在"}, ensure_ascii=False)

        try:
            result = tool_def.handler(**args)
            return result
        except Exception as e:
            logger.error(f"工具 {name} 调用失败: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def to_openai_tools(self, toolsets: Optional[List[str]] = None) -> List[dict]:
        tools = []
        for name, tool_def in self._tools.items():
            if toolsets and tool_def.toolset not in toolsets:
                continue
            tools.append(tool_def.to_openai_tool())
        return tools

    def get_definitions(self, toolsets: Optional[List[str]] = None) -> List[dict]:
        definitions = []
        for name, tool_def in self._tools.items():
            if toolsets and tool_def.toolset not in toolsets:
                continue
            definitions.append(tool_def.to_public_descriptor())
        return definitions

    def get_tool_names(self, toolsets: Optional[List[str]] = None) -> List[str]:
        if toolsets:
            result = []
            for ts in toolsets:
                result.extend(self._toolset_tools.get(ts, []))
            return list(set(result))
        return list(self._tools.keys())

    def discover_and_load(self, tools_dir: Optional[Path] = None):
        if tools_dir is None:
            tools_dir = Path(__file__).resolve().parent.parent.parent / "tools"

        if not tools_dir.exists():
            logger.warning(f"工具目录不存在: {tools_dir}")
            return

        for path in sorted(tools_dir.glob("*.py")):
            if path.name in {"__init__.py", "registry.py"}:
                continue

            module_name = f"tools.{path.stem}"
            try:
                importlib.import_module(module_name)
                logger.info(f"已加载工具模块: {module_name}")
            except Exception as e:
                logger.warning(f"加载工具模块失败 {module_name}: {e}")


def _parse_schema_to_parameters(schema: dict) -> List[ToolParameter]:
    params = []
    properties = schema.get("parameters", {}).get("properties", {})
    required = schema.get("parameters", {}).get("required", [])

    for name, prop in properties.items():
        params.append(ToolParameter(
            name=name,
            type=prop.get("type", "string"),
            description=prop.get("description", ""),
            required=name in required,
            enum=prop.get("enum"),
            default=prop.get("default"),
        ))
    return params


def _infer_parameters(func: Callable) -> List[ToolParameter]:
    sig = inspect.signature(func)
    hints = getattr(func, '__annotations__', {})
    params: List[ToolParameter] = []

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls", "args", "kwargs"):
            continue

        hint = hints.get(param_name, str)
        origin = getattr(hint, '__origin__', None)

        if origin is not None:
            if origin is list:
                param_type = "array"
            elif origin is dict:
                param_type = "object"
            else:
                args = getattr(hint, '__args__', ())
                for a in args:
                    if a is not type(None):
                        param_type = type_map.get(a, "string")
                        break
                else:
                    param_type = "string"
        else:
            param_type = type_map.get(hint, "string")

        has_default = param.default is not inspect.Parameter.empty
        tp = ToolParameter(
            name=param_name,
            type=param_type,
            description=f"Parameter: {param_name}",
            required=not has_default,
            default=param.default if has_default else None,
        )
        params.append(tp)

    return params


_default_registry: Optional[ToolRegistry] = None


def get_default_registry() -> ToolRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def tool(
    name: str,
    description: str,
    toolset: str = "default",
    parameters: Optional[List[ToolParameter]] = None,
    emoji: str = "",
    registry: Optional[ToolRegistry] = None,
):
    def decorator(func: Callable) -> Callable:
        params = parameters
        if params is None:
            params = _infer_parameters(func)

        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=params,
            handler=func,
            toolset=toolset,
            emoji=emoji,
        )

        target_registry = registry or get_default_registry()
        target_registry.register_definition(tool_def)

        func._tool_definition = tool_def
        return func

    return decorator


registry = get_default_registry()