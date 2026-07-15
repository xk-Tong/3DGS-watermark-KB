// 枚举选项配置——集中管理所有下拉选项的 value/label 映射。
//
// 后端枚举值是英文字符串（如 "watermarking"），前端展示用中文标签（如"水印"）。
// 把映射集中到一个文件，详情页编辑表单和新增表单都引用，避免重复定义。

export const taskTypeOptions = [
  { label: '水印', value: 'watermarking' },
  { label: '隐写', value: 'steganography' },
  { label: '篡改定位', value: 'tamper_localization' },
  { label: '编辑防护', value: 'editing_protection' },
  { label: '其他', value: 'other' },
]

export const attributeOptions = [
  { label: '仅SH系数', value: 'sh_only' },
  { label: '混合属性', value: 'mixed' },
  { label: '辅助属性', value: 'auxiliary' },
  { label: '其他', value: 'other' },
]

export const distributionOptions = [
  { label: '全局', value: 'global' },
  { label: '局部·频率引导', value: 'local_frequency' },
  { label: '局部·不确定性', value: 'local_uncertainty' },
  { label: '其他', value: 'other' },
]

export const injectionOptions = [
  { label: '逐资产微调', value: 'per_asset_finetune' },
  { label: '可泛化映射', value: 'generalizable_mapping' },
  { label: '生成内嵌入', value: 'generation_embedded' },
  { label: '其他', value: 'other' },
]

// robustness_targets 是多选，分组展示（2D / 3D）
export const robustness2DOptions = [
  { label: '几何变换', value: 'geometric_transform' },
  { label: '光度变换', value: 'photometric' },
  { label: '信号退化', value: 'signal_degradation' },
]

export const robustness3DOptions = [
  { label: '剪枝', value: 'pruning' },
  { label: '克隆', value: 'cloning' },
  { label: '空间变换', value: 'spatial_transform' },
  { label: '噪声注入', value: 'noise_injection' },
  { label: '量化', value: 'quantization' },
  { label: '参数合并', value: 'parameter_merging' },
]

export const readStatusOptions = [
  { label: '未读', value: 'unread' },
  { label: '在读', value: 'reading' },
  { label: '已读', value: 'read' },
]

export const curationStatusOptions = [
  { label: '⚠️ AI 未核实', value: 'auto' },
  { label: '已复核', value: 'reviewed' },
  { label: '已验证', value: 'verified' },
]

export const sourceOptions = [
  { label: '手动录入', value: 'manual' },
  { label: 'AI 自动抓取', value: 'arxiv_auto' },
  { label: '批量导入', value: 'imported' },
]

// 工具函数：枚举值 → 中文标签（用于展示）
export function labelOf(options, value) {
  const found = options.find((o) => o.value === value)
  return found ? found.label : value
}

// task_type 是多选数组，把数组里的每个值转成标签
export function taskTypeLabels(values) {
  return values.map((v) => labelOf(taskTypeOptions, v))
}
