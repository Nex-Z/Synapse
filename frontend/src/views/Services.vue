<!-- frontend/src/views/Services.vue -->
<template>
  <div class="services-page">
    <div class="page-header">
      <n-button type="primary" @click="showAddModal = true">
        添加服务
      </n-button>
    </div>

    <n-spin :show="loading">
      <n-data-table
          :columns="columns"
          :data="services"
          :pagination="false"
          :bordered="false"
          :max-height="400"
      />
    </n-spin>

    <!-- Add Service Modal -->
    <n-modal v-model:show="showAddModal">
      <n-card
          style="width: 650px"
          title="添加新服务"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <n-form ref="formRef" :model="newService" :rules="rules">
          <n-form-item path="name" label="服务名称">
            <n-input v-model:value="newService.name" placeholder="例如：用户中心"/>
          </n-form-item>
          <n-form-item path="type" label="文档类型">
            <n-select v-model:value="newService.type" :options="docTypeOptions" placeholder="选择文档类型"/>
          </n-form-item>
          <n-form-item path="url" label="文档地址">
            <n-input v-model:value="newService.url" placeholder="http://.../openapi.json 或 http://.../swagger.yaml"/>
          </n-form-item>
          
          <!-- 认证配置 -->
          <n-divider>认证配置（可选）</n-divider>
          <n-form-item label="认证类型">
            <n-select v-model:value="newService.auth_type" :options="authTypeOptions" placeholder="选择认证类型"/>
          </n-form-item>
          
          <!-- API Key 配置 -->
          <template v-if="newService.auth_type === 'api_key'">
            <n-form-item label="Key 名称">
              <n-input v-model:value="newService.auth_config.key_name" placeholder="例如：X-API-Key 或 Authorization"/>
            </n-form-item>
            <n-form-item label="Key 值">
              <n-input v-model:value="newService.auth_config.key_value" type="password" show-password-on="click" placeholder="API Key 值"/>
            </n-form-item>
            <n-form-item label="Key 位置">
              <n-select v-model:value="newService.auth_config.key_location" :options="keyLocationOptions" placeholder="选择 Key 位置"/>
            </n-form-item>
          </template>
          
          <!-- Basic Auth 配置 -->
          <template v-if="newService.auth_type === 'basic'">
            <n-form-item label="用户名">
              <n-input v-model:value="newService.auth_config.username" placeholder="用户名"/>
            </n-form-item>
            <n-form-item label="密码">
              <n-input v-model:value="newService.auth_config.password" type="password" show-password-on="click" placeholder="密码"/>
            </n-form-item>
          </template>
          
          <!-- OAuth2 配置 -->
          <template v-if="newService.auth_type === 'oauth2'">
            <n-form-item label="Token URL">
              <n-input v-model:value="newService.auth_config.token_url" placeholder="https://auth.example.com/oauth/token"/>
            </n-form-item>
            <n-form-item label="Client ID">
              <n-input v-model:value="newService.auth_config.client_id" placeholder="Client ID"/>
            </n-form-item>
            <n-form-item label="Client Secret">
              <n-input v-model:value="newService.auth_config.client_secret" type="password" show-password-on="click" placeholder="Client Secret"/>
            </n-form-item>
          </template>
        </n-form>
        <template #footer>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddService" :loading="submitting" style="margin-left: 12px;">确定</n-button>
        </template>
      </n-card>
    </n-modal>

    <n-modal v-model:show="showApisModal">
      <n-card
          style="width: 900px"
          :title="`'${selectedService?.name}' 的 API 列表`"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <template #header-extra>
          <n-button-group>
            <n-input v-model:value="searchQuery" placeholder="搜索 API/描述" clearable style="margin-right: 12px;"/>
            <n-button @click="showApisModal = false" text>
              <n-icon :size="20">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59L7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12L5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z" fill="currentColor"></path></svg>
              </n-icon>
            </n-button>
          </n-button-group>
        </template>
        <n-spin :show="loadingApis">
          <n-data-table
              :columns="apiColumns"
              :data="filteredApiEndpoints"
              :max-height="400"
          />
        </n-spin>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {computed, h, onMounted, ref} from 'vue';
import type {DataTableColumns, FormInst, FormValidationError} from 'naive-ui';
import {
  NButton,
  NButtonGroup,
  NCard,
  NDataTable,
  NDivider,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSpin,
  useDialog,
  useMessage
} from 'naive-ui';
import {
  getApiEndpoints,
  getServices,
  createService as createServiceApi,
  deleteService as deleteServiceApi,
  type Service,
  type AuthType,
  type AuthConfig
} from '../services/api';

// --- Interfaces ---
interface ApiEndpoint {
  path: string;
  method: string;
  summary: string;
}

interface ServiceActions {
  viewApis: (row: Service) => void;
  deleteService: (row: Service) => void;
}

// --- Data & State ---
const message = useMessage();
const dialog = useDialog();
const formRef = ref<FormInst | null>(null);

// Service management state
const loading = ref(false);
const submitting = ref(false);
const showAddModal = ref(false);
const services = ref<Service[]>([]);

// New service form state with auth configuration
const newService = ref<{
  name: string;
  url: string;
  type: string;
  auth_type: AuthType;
  auth_config: AuthConfig;
}>({
  name: '',
  url: '',
  type: '',
  auth_type: 'none',
  auth_config: {}
});

// API viewing state
const showApisModal = ref(false);
const loadingApis = ref(false);
const selectedService = ref<Service | null>(null);
const apiEndpoints = ref<ApiEndpoint[]>([]);
const searchQuery = ref('');

const filteredApiEndpoints = computed(() => {
  if (!searchQuery.value) {
    return apiEndpoints.value;
  }
  return apiEndpoints.value.filter(api =>
      api.path.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      api.summary.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

// Document Type Options
const docTypeOptions = [
  {label: 'OpenAPI 3.0', value: 'OpenAPI 3.0'},
  {label: 'Swagger 2.0', value: 'Swagger 2.0'},
  {label: 'AsyncAPI', value: 'AsyncAPI'},
];

// Auth Type Options
const authTypeOptions = [
  {label: '无认证', value: 'none'},
  {label: 'API Key', value: 'api_key'},
  {label: 'Basic Auth', value: 'basic'},
  {label: 'OAuth2 Client Credentials', value: 'oauth2'},
];

// Key Location Options (for API Key auth)
const keyLocationOptions = [
  {label: 'Header', value: 'header'},
  {label: 'Query Parameter', value: 'query'},
];

// --- Form Rules ---
const rules = {
  name: {required: true, message: '请输入服务名称', trigger: 'blur'},
  type: {required: true, message: '请选择文档类型', trigger: ['blur', 'change']},
  url: {required: true, message: '请输入文档地址', trigger: 'blur'},
};

// --- Table Columns ---
// Main services table
const serviceTableColumns = ({viewApis, deleteService}: ServiceActions): DataTableColumns<Service> => [
  {title: '服务名称', key: 'name'},
  {title: '文档类型', key: 'type'},
  {title: 'OpenAPI URL', key: 'url'},
  {
    title: '状态',
    key: 'status',
    render: (row) => h('span', {style: {color: row.status === 'healthy' ? '#63e2b7' : '#e88080'}}, row.status === 'healthy' ? '健康' : '异常')
  },
  {
    title: '操作', key: 'actions', render: (row) => h('div', {style: {display: 'flex', gap: '8px'}}, [
      h(NButton, {size: 'small', onClick: () => viewApis(row)}, {default: () => '查看 API'}),
      h(NButton, {
        size: 'small',
        type: 'error',
        ghost: true,
        onClick: () => deleteService(row)
      }, {default: () => '删除'}),
    ])
  },
];
// API details table (in modal)
const apiColumns: DataTableColumns<ApiEndpoint> = [
  {title: '路径', key: 'path'},
  {title: '方法', key: 'method'},
  {title: '描述', key: 'summary'},
];

const columns = serviceTableColumns({
  viewApis: (row: Service) => {
    selectedService.value = row;
    showApisModal.value = true;
    handleViewApis(row.url);
  },
  deleteService: (row: Service) => {
    dialog.warning({
      title: '确认删除',
      content: `确定要删除服务 "${row.name}" 吗？此操作不可恢复。`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteServiceApi(row.id);
          message.success(`服务 "${row.name}" 已删除`);
          await loadServices();
        } catch (error) {
          message.error(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
        }
      }
    });
  }
});

// --- Methods ---
const loadServices = async () => {
  loading.value = true;
  try {
    services.value = await getServices();
  } catch (error) {
    console.error('Failed to load services:', error);
    message.error('加载服务列表失败');
  } finally {
    loading.value = false;
  }
};

const handleAddService = () => {
  formRef.value?.validate(async (errors: Array<FormValidationError> | undefined) => {
    if (!errors) {
      submitting.value = true;
      try {
        await createServiceApi({
          name: newService.value.name,
          url: newService.value.url,
          type: newService.value.type,
          auth_type: newService.value.auth_type,
          auth_config: newService.value.auth_config,
        });
        message.success('服务添加成功');
        showAddModal.value = false;
        // Reset form with auth fields
        newService.value = {
          name: '',
          url: '',
          type: '',
          auth_type: 'none',
          auth_config: {}
        };
        await loadServices();
      } catch (error) {
        message.error(`添加失败: ${error instanceof Error ? error.message : '未知错误'}`);
      } finally {
        submitting.value = false;
      }
    } else {
      message.error('请填写所有必填项');
    }
  });
};

const handleViewApis = async (url: string) => {
  loadingApis.value = true;
  apiEndpoints.value = [];
  try {
    apiEndpoints.value = await getApiEndpoints(url);
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`获取 API 失败: ${error.message}`);
    } else {
      message.error('获取 API 失败: 未知错误');
    }
    showApisModal.value = false; // Close modal on error
  } finally {
    loadingApis.value = false;
  }
};

onMounted(() => {
  loadServices();
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h1 {
  margin: 0;
}
</style>
