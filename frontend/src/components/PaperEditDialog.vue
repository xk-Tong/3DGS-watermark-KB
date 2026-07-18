<template>
  <!-- el-dialog：Element Plus 的对话框组件。
       :model-value / @update：通过 v-model:visible 实现双向绑定控制显示隐藏。
       title：对话框标题。width：宽度百分比。
       destroy-on-close：关闭时销毁内容，避免下次打开还是上次的数据。 -->
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="编辑论文"
    width="800px"
    destroy-on-close
  >
    <el-form :model="form" label-width="100px" label-position="right">
      <!-- el-tabs：标签页，把编辑表单分组，避免一个长表单滚动到底。
           v-model 绑定当前激活的 tab 名。 -->
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="basic">
          <el-form-item label="标题">
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="作者">
            <!-- 动态标签输入：用 el-select multiple + filterable + allow-create 模拟"可输入标签"。
                 这是 Element Plus 处理"字符串列表"字段的常见技巧。 -->
            <el-select
              v-model="form.authors"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入作者名回车添加"
              style="width: 100%"
            />
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
            <!-- el-date-picker：日期选择器。value-format 指定传给后端的格式（YYYY-MM-DD）。 -->
            <el-date-picker v-model="form.pub_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
          </el-form-item>
          <el-form-item label="PDF URL">
            <el-input v-model="form.pdf_url" />
          </el-form-item>
          <el-form-item label="代码仓库">
            <el-input v-model="form.code_url" />
          </el-form-item>
          <el-form-item label="摘要">
            <el-input v-model="form.abstract" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="方法概述">
            <el-input v-model="form.method_summary" type="textarea" :rows="3" placeholder="AI 抽取的方法概述" />
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="分类信息" name="category">
          <el-form-item label="任务类型">
            <!-- 多选：task_type 是数组，multiple 让 el-select 支持多选 -->
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
              <!-- el-option-group：分组下拉，把 2D/3D 攻击分开展示更清晰 -->
              <el-option-group label="2D 失真（渲染图像）">
                <el-option v-for="opt in robustness2DOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-option-group>
              <el-option-group label="3D 失真（高斯参数空间）">
                <el-option v-for="opt in robustness3DOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-option-group>
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <!-- 自由标签：allow-create 允许输入自定义值 -->
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
            <!-- extra_metrics 是 JSON 对象，用 textarea 让用户写 JSON 字符串，提交时 parse。 -->
            <el-input v-model="extraMetricsText" type="textarea" :rows="4" placeholder='{"lpips": 0.15, "capacity_bpp": 0.5}' />
            <div class="hint">输入合法 JSON 对象，留空表示不修改</div>
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
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
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

// props：父组件传进来的数据。
// defineProps 是 Vue 3 的编译宏，声明组件接收的属性。
const props = defineProps({
  visible: Boolean,   // 对话框显示状态
  paper: Object,     // 要编辑的论文对象（可能为 null）
})

// emit：子组件向父组件发事件。
// 'update:visible'：配合 v-model:visible 实现 .sync 双向绑定。
// 'saved'：保存成功后通知父组件刷新数据。
const emit = defineEmits(['update:visible', 'saved'])

// 表单数据和状态
const form = ref({})             // 表单数据，从 paper 复制过来
const extraMetricsText = ref('') // extra_metrics 的文本形式（textarea 绑定字符串）
const saving = ref(false)        // 保存中状态
const activeTab = ref('basic')   // 当前激活的 tab

// watch：监听 props.paper 变化，当父组件传入论文数据时，复制到表单。
// 注意：必须用结构化克隆（{...paper}），不能直接 form.value = props.paper，
// 否则改表单会直接改父组件的数据（引用共享）。
// immediate: true：立即执行一次，组件初始化时就同步。
watch(
  () => props.paper,
  (newPaper) => {
    if (newPaper) {
      // 浅拷贝基本字段。对于数组字段（authors/task_type 等），需要深拷贝避免引用共享。
      // JSON.parse(JSON.stringify())：简单粗暴的深拷贝方式，对纯数据对象够用。
      form.value = JSON.parse(JSON.stringify(newPaper))
      // extra_metrics 转成 JSON 字符串供 textarea 显示
      extraMetricsText.value = newPaper.extra_metrics
        ? JSON.stringify(newPaper.extra_metrics, null, 2)
        : ''
    }
  },
  { immediate: true }
)

/**
 * 作用：保存表单数据到后端。
 * 使用场景：用户点击"保存"按钮。
 */
async function handleSave() {
  saving.value = true
  try {
    // 构造要更新的字段。
    // ...form.value 展开所有字段，然后覆盖 extra_metrics（从文本 parse）。
    const data = { ...form.value }

    // 处理 extra_metrics：如果用户输入了文本，parse 成对象；空字符串设为 null（清空）。
    if (extraMetricsText.value.trim()) {
      try {
        data.extra_metrics = JSON.parse(extraMetricsText.value)
      } catch (e) {
        // JSON.parse 失败说明格式不对，提示用户并中止保存。
        ElMessage.error('其他指标 JSON 格式错误：' + e.message)
        saving.value = false
        return
      }
    } else {
      data.extra_metrics = null
    }

    // 删除不该传给 PATCH 的字段（id、added_at、last_reviewed_at 是后端管理的）。
    // delete 操作符删除对象属性。
    delete data.id
    delete data.added_at
    delete data.last_reviewed_at
    delete data.source  // source 不可改

    await papersApi.update(props.paper.id, data)
    ElMessage.success('保存成功')
    emit('saved')  // 通知父组件刷新
  } catch (e) {
    // axios 错误：response.data.detail 是后端返回的错误信息。
    const msg = e.response?.data?.detail || e.message
    ElMessage.error('保存失败：' + msg)
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
