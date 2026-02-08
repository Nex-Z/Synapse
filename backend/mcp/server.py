# backend/mcp/server.py
"""
MCP Server 核心逻辑
处理工具列表、工具调用等
"""
import re
from typing import Dict, List, Any, Optional
import httpx
from mcp.protocol import (
    McpTool,
    convert_openapi_endpoint_to_mcp_tool,
    create_error_response,
    create_success_response,
    McpError
)
from core.auth_handler import AuthHandler


class McpServerHandler:
    """MCP Server 请求处理器"""

    def __init__(
        self,
        server_config: Dict[str, Any],
        combinations: List[Dict[str, Any]]
    ):
        """
        初始化 MCP Server

        Args:
            server_config: MCP Server 配置（包含 id, name, prefix, combination_ids 等）
            combinations: 所有组合的列表
        """
        self.server_config = server_config
        self.combinations = combinations
        self.prefix = server_config.get("prefix", "")
        self._tools_cache: Optional[List[McpTool]] = None

    def invalidate_cache(self):
        """使工具缓存失效（当配置变更时调用）"""
        self._tools_cache = None

    def get_tools(self) -> List[McpTool]:
        """
        获取所有可用工具列表
        聚合所有组合中的接口并转换为 MCP 工具
        """
        # 使用缓存提高性能
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []
        combination_ids = self.server_config.get("combination_ids", [])

        for combination in self.combinations:
            # 只处理当前 MCP Server 包含的组合
            if combination.get("id") not in combination_ids:
                continue

            # 只处理 active 状态的组合
            if combination.get("status") != "active":
                continue

            # 遍历组合中的所有端点
            endpoints = combination.get("endpoints", [])
            for endpoint in endpoints:
                try:
                    tool = convert_openapi_endpoint_to_mcp_tool(
                        endpoint,
                        prefix=self.prefix
                    )
                    tools.append(tool)
                except Exception as e:
                    print(f"Failed to convert endpoint to tool: {e}")
                    continue

        self._tools_cache = tools
        return tools

    async def handle_tools_list(self, request_id: Optional[int | str] = None) -> Dict[str, Any]:
        """
        处理 tools/list 请求

        Returns:
            JSON-RPC 响应
        """
        try:
            tools = self.get_tools()
            tools_dict = [tool.model_dump() for tool in tools]

            return create_success_response(
                result={"tools": tools_dict},
                id=request_id
            )
        except Exception as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"Failed to list tools: {str(e)}",
                id=request_id
            )

    async def handle_tools_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Optional[int | str] = None
    ) -> Dict[str, Any]:
        """
        处理 tools/call 请求
        实际调用后端 API

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            request_id: 请求 ID

        Returns:
            JSON-RPC 响应
        """
        try:
            # Copy arguments to avoid modifying the original
            args = arguments.copy()

            # 从参数中提取必要信息
            method = args.get("_method", "GET")
            path_template = args.get("_path", "")
            service_url = args.get("_serviceUrl", "")
            auth_type = args.get("_authType", "none")
            auth_config = args.get("_authConfig", {})

            if not service_url or not path_template:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing required parameters: _serviceUrl or _path",
                    id=request_id
                )

            # 1. 处理路径参数 (Path Parameters)
            # 查找路径中的参数，如 /pet/{petId}
            path_params = re.findall(r"\{([a-zA-Z0-9_]+)\}", path_template)
            actual_path = path_template

            for param_name in path_params:
                if param_name in args:
                    val = args.pop(param_name)  # 从参数中移除，避免重复发送
                    actual_path = actual_path.replace(f"{{{param_name}}}", str(val))
                else:
                    # 如果缺少路径参数，可能导致调用失败，但暂时不做严格校验
                    pass

            # 构建完整 URL
            base_url = service_url.replace("/openapi.json", "").replace("/swagger.json", "")
            full_url = f"{base_url}{actual_path}"

            # 2. 处理请求体 (Request Body)
            json_body = None
            if "body" in args:
                json_body = args.pop("body")

            # 3. 准备剩余参数 (Query Params)
            # 过滤掉内部参数（以 _ 开头的）
            request_params = {
                k: v for k, v in args.items()
                if not k.startswith("_")
            }

            # 4. 应用认证配置
            headers = {}
            await AuthHandler.apply_auth(auth_type, auth_config, headers, request_params)

            # 执行 HTTP 请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(full_url, params=request_params, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(full_url, params=request_params, headers=headers)
                elif method.upper() in ["POST", "PUT", "PATCH"]:
                    # 如果有显式的 body 参数，使用它作为 JSON body
                    # 剩余的 request_params 作为 query params
                    if json_body is not None:
                        response = await client.request(
                            method, 
                            full_url, 
                            json=json_body, 
                            params=request_params,
                            headers=headers
                        )
                    else:
                        # 否则，将所有参数作为 JSON body
                        response = await client.request(
                            method, 
                            full_url, 
                            json=request_params,
                            headers=headers
                        )
                else:
                    return create_error_response(
                        code=McpError.INVALID_PARAMS,
                        message=f"Unsupported HTTP method: {method}",
                        id=request_id
                    )

            # 返回 API 响应
            try:
                result_data = response.json()
            except Exception:
                result_data = {"text": response.text, "status_code": response.status_code}

            return create_success_response(
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": str(result_data)
                        }
                    ]
                },
                id=request_id
            )

        except httpx.TimeoutException:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message="API request timeout",
                id=request_id
            )
        except httpx.RequestError as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"API request failed: {str(e)}",
                id=request_id
            )
        except Exception as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"Tool execution failed: {str(e)}",
                id=request_id
            )

    async def handle_initialize(self, params: Optional[Dict[str, Any]] = None, request_id: Optional[int | str] = None) -> Dict[str, Any]:
        """
        处理 initialize 请求

        Args:
            params: 初始化参数
            request_id: 请求 ID

        Returns:
            JSON-RPC 响应
        """
        # 提取客户端协议版本
        client_protocol_version = params.get("protocolVersion", "2024-11-05") if params else "2024-11-05"

        return create_success_response(
            result={
                "protocolVersion": client_protocol_version,  # 回显客户端版本
                "capabilities": {
                    "tools": {
                        "listChanged": True  # 支持工具列表变更通知
                    },
                },
                "serverInfo": {
                    "name": self.server_config.get("name", "Synapse MCP Server"),
                    "version": "0.4.0"
                }
            },
            id=request_id
        )

    async def handle_request(self, method: str, params: Optional[Dict[str, Any]], request_id: Optional[int | str]) -> Dict[str, Any]:
        """
        统一处理 MCP 请求

        Args:
            method: RPC 方法名
            params: 请求参数
            request_id: 请求 ID

        Returns:
            JSON-RPC 响应
        """
        if method == "initialize":
            return await self.handle_initialize(params, request_id)
        elif method == "tools/list":
            return await self.handle_tools_list(request_id)
        elif method == "tools/call":
            if not params:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing params for tools/call",
                    id=request_id
                )
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not tool_name:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing tool name",
                    id=request_id
                )
            return await self.handle_tools_call(tool_name, arguments, request_id)
        else:
            return create_error_response(
                code=McpError.METHOD_NOT_FOUND,
                message=f"Method not found: {method}",
                id=request_id
            )

