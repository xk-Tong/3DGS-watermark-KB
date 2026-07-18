<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="新增论文"
    width="800px"
    destroy-on-close
  >
    <el-form :model="form" label-width="100px" label-position="right">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="basic">
          <el-form-item label="标题" required>
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="作者">
            <el-select v-model="form.authors" multiple filterable allow-create default-first-option placeholder="输入作者名回车添加" style="width: 100%" />
          </el-form-item>
          <el-form-item label="arXiv ID">
            <el-input v-model="form.arxiv_id" placeholder="如 2410.03461" />
          </el-form-item>
          <el-form-item label="DOI">
            <el-input v-model="form.doi" />
          </el-form-item>
          <el-form-item label="会议/期刊">
            <el-input v-model="form.venue" placeholder="如 AAAI'26 或 arXiv preprint" />
          </el-form-item>
          <el-form-item label="发表日期">
            <el-date-picker v-model="form.pub_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
          </el-form-item>
          <el-form-item label="PDF URL">
            <el-input v-model="form.pdf_url" />
          </el-form-item>
          <el-form-item label="代码仓库">
            <el-input v-model="form.code_url" />
          </el-form-item>
          <el-form-item label="摘要" required>
            <el-input v-model="form.abstract" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="方法概述">
            <el-input v-model="form.method_summary" type="textarea" :rows="3" placeholder="可手填，Phase 2 后由 AI 抽取" />
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="分类信息" name="category">
          <el-form-item label="任务类型">
            <el-select v-model="form.task_type" multiple placeholder="选择任务类型" style="width: 100%">
              <el-option v-for="opt in taskTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="属性选择">
            <el-select v-model="form.attribute_selection" clearable placeholder="选择属性选择机制" style="width: 100%">
              <el-option v-for="opt in attributeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="分布策略">
            <el-select v-model="form.distribution_strategy" clearable placeholder="选择分布策略" style="width: 100%">
              <el-option v-for="opt in distributionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="注入管道">
            <el-select v-model="form.injection_pipeline" clearable placeholder="选择注入管道" style="width: 100%">
              <el-option v-for="opt in injectionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="鲁棒性">
            <el-select v-model="form.robustness_targets" multiple placeholder="选择评估的攻击类型" style="width: 100%">
              <el-option-group label="2D 失真（渲染图像）">
                <el-option v-for="opt in robustness2DOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-option-group>
              <el-option-group label="3D 失真（高斯参数空间）">
                <el-option v-for="opt in robustness3DOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-option-group>
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <el-select v-model="form.tags" multiple filterable allow-create default-first-option placeholder="输入标签回车添加" style="width: 100%" />
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="实验数据" name="metrics">
          <el-form-item label="PSNR (dB)">
            <el-input-number v-model="form.psnr" :precision="2" :step="0.1" controls-position="right" />
          </el-form-item>
          <el-form-item label="SSIM">
            <el-input-number v-model="form.ssim" :precision="4" :step="0.001" :min="0" :max="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="Bit Accuracy">
            <el-input-number v-model="form.bit_accuracy" :precision="4" :step="0.01" :min="0" :max="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="容量">
            <el-input v-model="form.capacity" placeholder="如 256 bits/model" />
          </el-form-item>
          <el-form-item label="数据集">
            <el-select v-model="form.datasets_used" multiple filterable allow-create default-first-option placeholder="输入数据集名回车添加" style="width: 100%" />
          </el-form-item>
          <el-form-item label="基线对比">
            <el-select v-model="form.baselines_compared" multiple filterable allow-create default-first-option placeholder="输入基线方法名回车添加" style="width: 100%" />
          </el-form-item>
          <el-form-item label="其他指标 JSON">
            <el-input v-model="extraMetricsText" type="textarea" :rows="4" placeholder='{"lpips": 0.15, "capacity_bpp": 0.5}' />
            <div class="hint">输入合法 JSON 对象，留空表示不填</div>
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="个人使用" name="personal">
          <el-form-item label="阅读状态">
            <el-radio-group v-model="form.read_status">
              <el-radio v-for="opt in readStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="数据状态">
            <el-radio-group v-model="form.curation_status">
              <el-radio v-for="opt in curationStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="关键贡献">
            <el-select v-model="form.key_contributions" multiple filterable allow-create default-first-option placeholder="输入贡献点回车添加" style="width: 100%" />
          </el-form-item>
          <el-form-item label="个人批注">
            <el-input v-model="form.personal_notes" type="textarea" :rows="5" placeholder="你对这篇论文的批注、想法、评价" />
          </el-form-item>
        </el-tab-pane>
      </el-tabs>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleCreate">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { papersApi } from '../api/papers'
import {
  taskTypeOptions, attributeOptions, distributionOptions, injectionOptions,
  robustness2DOptions, robustness3DOptions, readStatusOptions,
  curationStatusOptions,
} from '../api/options'

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['update:visible', 'created'])

// 表单状态
const form = ref({})
const extraMetricsText = ref('')
const saving = ref(false)
const activeTab = ref('basic')

// 默认表单数据工厂函数。
// 用工厂函数而非直接写对象，是为了每次打开对话框都拿到全新的默认值，
// 避免上次填的数据残留（destroy-on-close 会销毁组件，但 watch 会重新初始化）。
function defaultForm() {
  return {
    title: '',
    authors: [],
    arxiv_id: '',
    doi: '',
    venue: '',
    pub_date: null,
    abstract: '',
    pdf_url: '',
    code_url: '',
    method_summary: '',
    key_contributions: [],
    task_type: ['watermarking'],   // 默认水印，因为 KB 主要关注水印
    attribute_selection: null,
    distribution_strategy: null,
    injection_pipeline: null,
    robustness_targets: [],
    tags: [],
    capacity: '',
    datasets_used: [],
    baselines_compared: [],
    psnr: null,
    ssim: null,
    bit_accuracy: null,
    extra_metrics: null,
    read_status: 'unread',
    personal_notes: '',
    curation_status: 'reviewed',  // 手动录入默认 reviewed
  }
}

// watch visible：对话框打开时初始化默认表单。
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      form.value = defaultForm()
      extraMetricsText.value = ''
      activeTab.value = 'basic'
    }
  },
  { immediate: true }
)

/**
 * 作用：提交创建论文。
 * 使用场景：用户点击"创建"按钮。
 */
async function handleCreate() {
  // 前端校验必填字段。
  if (!form.value.title || !form.value.abstract) {
    ElMessage.warning('标题和摘要为必填项')
    return
  }

  saving.value = true
  try {
    const data = { ...form.value }

    // 处理 extra_metrics JSON
    if (extraMetricsText.value.trim()) {
      try {
        data.extra_metrics = JSON.parse(extraMetricsText.value)
      } catch (e) {
        ElMessage.error('其他指标 JSON 格式错误：' + e.message)
        saving.value = false
        return
      }
    } else {
      data.extra_metrics = null
    }

    // 清理空字符串字段，避免传一堆空字符串给后端。
    // 这里只删 arxiv_id/doi/venue 等可选字段，title/abstract 必填不删。
    ;['arxiv_id', 'doi', 'venue', 'pdf_url', 'code_url', 'method_summary', 'capacity', 'personal_notes'].forEach((f) => {
      if (data[f] === '') delete data[f]
    })

    await papersApi.create(data)
    ElMessage.success('创建成功')
    emit('created')
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    ElMessage.error('创建失败：' + msg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
</style>
