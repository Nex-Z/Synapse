# backend/mcp/protocol.py
"""
MCP (Model Context Protocol) 协议实现
支持 JSON-RPC 2.0 格式的 MCP 通信
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 请求格式"""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int | str] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 响应格式"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int | str] = None


class McpTool(BaseModel):
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class McpError:
    """MCP 错误代码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


def create_error_response(code: int, message: str, id: Optional[int | str] = None) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": id
    }


def create_success_response(result: Any, id: Optional[int | str] = None) -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": id
    }


def convert_openapi_endpoint_to_mcp_tool(
    endpoint: Dict[str, Any],
    prefix: str = ""
) -> McpTool:
    """
    将 OpenAPI 端点转换为 MCP 工具

    Args:
        endpoint: 组合中的端点信息
        prefix: 工具名称前缀（用于避免冲突）

    Returns:
        MCP 工具定义
    """
    # 生成工具名称：prefix_method_path
    path = endpoint.get("path", "").replace("/", "_").replace("{", "").replace("}", "").strip("_")
    method = endpoint.get("method", "GET").lower()
    tool_name = f"{prefix}_{method}_{path}" if prefix else f"{method}_{path}"

    # 工具描述
    description = endpoint.get("summary", "") or endpoint.get("description", "") or f"{method.upper()} {endpoint.get('path', '')}"

    # 输入 schema
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    # 处理参数 (Query, Path, Header, Cookie)
    for param in endpoint.get("parameters", []):
        param_name = param.get("name")
        if not param_name:
            continue

        param_schema = param.get("schema", {})
        description = param.get("description", "")
        
        # 添加参数到 schema
        input_schema["properties"][param_name] = {
            "type": param_schema.get("type", "string"),
            "description": description,
            # 复制其他 schema 属性 (format, enum, etc.)
            **{k: v for k, v in param_schema.items() if k not in ["type", "description"]}
        }
        
        if param.get("required", False):
            input_schema["required"].append(param_name)

    # 处理请求体 (Request Body)
    req_body = endpoint.get("requestBody")
    if req_body:
        content = req_body.get("content", {})
        # 优先处理 application/json
        json_content = content.get("application/json")
        if json_content and "schema" in json_content:
            body_schema = json_content["schema"]
            body_desc = req_body.get("description", "Request body")
            
            # 将请求体作为一个名为 'body' 的参数
            input_schema["properties"]["body"] = {
                "type": "object",
                "description": body_desc,
                **body_schema
            }
            if req_body.get("required", False):
                input_schema["required"].append("body")

    # 添加基本元数据（隐藏参数）
    input_schema["properties"]["_method"] = {
        "type": "string",
        "description": "HTTP method",
        "enum": [method.upper()],
        "default": method.upper()
    }
    input_schema["properties"]["_path"] = {
        "type": "string",
        "description": "API path",
        "default": endpoint.get("path", "")
    }
    input_schema["properties"]["_serviceUrl"] = {
        "type": "string",
        "description": "Service base URL",
        "default": endpoint.get("serviceUrl", "")
    }
    # 认证配置（隐藏参数）
    input_schema["properties"]["_authType"] = {
        "type": "string",
        "description": "Authentication type",
        "default": endpoint.get("authType", "none")
    }
    input_schema["properties"]["_authConfig"] = {
        "type": "object",
        "description": "Authentication configuration",
        "default": endpoint.get("authConfig", {})
    }

    return McpTool(
        name=tool_name,
        description=description,
        inputSchema=input_schema
    )
