// frontend/src/services/api.ts

import { getToken } from '../utils/auth';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''; // 生产环境使用相对路径

/**
 * 创建请求头，自动添加 Authorization
 */
function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

/**
 * 执行 fetch 请求并处理错误
 */
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = getHeaders();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  });

  // 如果返回 401，可能是 Token 过期，跳转到登录页
  if (response.status === 401) {
    // 清除 Token 并跳转到登录页
    localStorage.removeItem('synapse_access_token');
    localStorage.removeItem('synapse_current_user');
    window.location.href = '/login';
    throw new Error('Unauthorized - please login again');
  }

  return response;
}

// ============= Authentication API =============

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

/**
 * 用户登录
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUserInfo(): Promise<User> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/auth/me`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get user info' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 用户登出
 */
export async function logout(): Promise<void> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/auth/logout`, {
    method: 'POST',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Logout failed' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

// ============= User Management API (Admin Only) =============

export interface UserCreate {
  username: string;
  password: string;
  role: 'admin' | 'user';
}

export interface UserUpdate {
  password?: string;
  role?: 'admin' | 'user';
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
}

/**
 * 获取用户列表（仅管理员）
 */
export async function getUsers(skip: number = 0, limit: number = 100): Promise<UserListResponse> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/users?skip=${skip}&limit=${limit}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get users' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 获取单个用户（仅管理员）
 */
export async function getUser(id: number): Promise<User> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/users/${id}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'User not found' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建新用户（仅管理员）
 */
export async function createUser(user: UserCreate): Promise<User> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/users`, {
    method: 'POST',
    body: JSON.stringify(user),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create user' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新用户（仅管理员）
 */
export async function updateUser(id: number, user: UserUpdate): Promise<User> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(user),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to update user' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 删除用户（仅管理员）
 */
export async function deleteUser(id: number): Promise<void> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/users/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete user' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

// ============= Service API =============

export interface Service {
  id: number;
  name: string;
  url: string;
  type: string;
  status: 'healthy' | 'unhealthy';
  createdAt: string;
  updatedAt: string;
}

export interface ServiceCreate {
  name: string;
  url: string;
  type: string;
}

export interface ServiceUpdate {
  name?: string;
  url?: string;
  type?: string;
}

/**
 * 获取所有服务列表
 */
export async function getServices(): Promise<Service[]> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/services`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 根据 ID 获取单个服务
 */
export async function getService(id: number): Promise<Service> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/services/${id}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建新服务
 */
export async function createService(service: ServiceCreate): Promise<Service> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/services`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(service),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新服务
 */
export async function updateService(id: number, service: ServiceUpdate): Promise<Service> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/services/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(service),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 删除服务
 */
export async function deleteService(id: number): Promise<void> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/services/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

/**
 * Fetches the MCP tools for a given OpenAPI specification URL.
 *
 * @param openapiUrl The URL of the OpenAPI spec.
 * @returns A promise that resolves to the MCP tools definition.
 */
export async function getMcpTools(openapiUrl: string) {
  const response = await fetchWithAuth(`${BASE_URL}/mcp/v1/tools?openapi_url=${encodeURIComponent(openapiUrl)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Fetches the API endpoints for a given OpenAPI specification URL.
 *
 * @param url The URL of the OpenAPI spec.
 * @returns A promise that resolves to a list of API endpoints.
 */
export async function getApiEndpoints(url: string) {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/endpoints?url=${encodeURIComponent(url)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// ============= Combination API =============

export interface CombinationEndpoint {
  serviceName: string;
  serviceUrl: string;
  path: string;
  method: string;
  summary: string;
}

export interface Combination {
  id: number;
  name: string;
  description: string;
  status: 'active' | 'inactive';
  endpoints: CombinationEndpoint[];
  createdAt: string;
  updatedAt: string;
}

export interface CombinationCreate {
  name: string;
  description: string;
  endpoints: CombinationEndpoint[];
}

export interface CombinationUpdate {
  name?: string;
  description?: string;
  endpoints?: CombinationEndpoint[];
}

/**
 * 获取所有组合列表
 */
export async function getCombinations(): Promise<Combination[]> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 根据 ID 获取单个组合
 */
export async function getCombination(id: number): Promise<Combination> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations/${id}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建新组合
 */
export async function createCombination(combination: CombinationCreate): Promise<Combination> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(combination),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新组合
 */
export async function updateCombination(id: number, combination: CombinationUpdate): Promise<Combination> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(combination),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 切换组合状态
 */
export async function toggleCombinationStatus(id: number, status: 'active' | 'inactive'): Promise<Combination> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations/${id}/status?status=${status}`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 删除组合
 */
export async function deleteCombination(id: number): Promise<void> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/combinations/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

// ============= MCP Server API =============

export interface McpServer {
  id: number;
  name: string;
  prefix: string;
  description: string;
  status: 'active' | 'inactive';
  combination_ids: number[];
  createdAt: string;
  updatedAt: string;
}

export interface McpServerCreate {
  name: string;
  prefix: string;
  description: string;
  combination_ids: number[];
}

export interface McpServerUpdate {
  name?: string;
  description?: string;
  combination_ids?: number[];
}

/**
 * 获取所有 MCP 服务列表
 */
export async function getMcpServers(): Promise<McpServer[]> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 根据 ID 获取单个 MCP 服务
 */
export async function getMcpServer(id: number): Promise<McpServer> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers/${id}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建新 MCP 服务
 */
export async function createMcpServer(server: McpServerCreate): Promise<McpServer> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(server),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新 MCP 服务
 */
export async function updateMcpServer(id: number, server: McpServerUpdate): Promise<McpServer> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(server),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 切换 MCP 服务状态
 */
export async function toggleMcpServerStatus(id: number, status: 'active' | 'inactive'): Promise<McpServer> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers/${id}/status?status=${status}`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 删除 MCP 服务
 */
export async function deleteMcpServer(id: number): Promise<void> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/mcp-servers/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

/**
 * 获取 MCP 服务的配置信息
 */
export async function getMcpServerConfig(prefix: string): Promise<any> {
  const response = await fetchWithAuth(`${BASE_URL}/mcp/${prefix}/config`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// ============= Dashboard API =============

export interface DashboardStats {
  services: {
    total: number;
  };
  combinations: {
    total: number;
    active: number;
    inactive: number;
  };
  mcp_servers: {
    total: number;
    active: number;
    inactive: number;
  };
  endpoints: {
    total: number;
  };
  recent_items: Array<{
    id: number;
    name: string;
    type: 'combination' | 'mcp_server';
    status: string;
    created_at: string;
  }>;
}

/**
 * 获取仪表盘统计数据
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await fetchWithAuth(`${BASE_URL}/api/v1/dashboard/stats`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}
