<template>
  <div class="app-layout">
    <!-- 轻量导航栏：替代原来的 el-menu
         左边站名 + 右边文字链接，当前页加下划线
         滚动时加 backdrop-blur 增强可读性 -->
    <nav class="nav-bar" :class="{ scrolled: isScrolled }">
      <div class="nav-inner">
        <!-- 站名：Space Grotesk 字体 -->
        <router-link to="/" class="brand">
          <span class="brand-name">3DGS-KB</span>
          <span class="brand-sub">IP Protection</span>
        </router-link>

        <!-- 导航链接 -->
        <div class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: isHome }">首页</router-link>
          <router-link to="/papers" class="nav-link" :class="{ active: isPapers }">论文</router-link>
          <router-link to="/dashboard" class="nav-link" :class="{ active: isDashboard }">仪表盘</router-link>
          <router-link to="/compare" class="nav-link compare-link" :class="{ active: isCompare }">
            对比
            <span v-if="store.selectedForCompare.length" class="compare-count">{{ store.selectedForCompare.length }}</span>
          </router-link>
        </div>
      </div>
    </nav>

    <!-- 路由出口 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePapersStore } from './stores/papers'

const route = useRoute()
const store = usePapersStore()

// 滚动监听：导航栏在滚动时加 backdrop-blur。
// scrollY > 10 视为已滚动。
const isScrolled = ref(false)
function handleScroll() {
  isScrolled.value = window.scrollY > 10
}
onMounted(() => window.addEventListener('scroll', handleScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))

// 当前路由高亮判断
// route.path 可能是 /papers 或 /papers/123，都用 startsWith 判断
const isHome = computed(() => route.path === '/')
const isPapers = computed(() => route.path.startsWith('/papers'))
const isDashboard = computed(() => route.path.startsWith('/dashboard'))
const isCompare = computed(() => route.path.startsWith('/compare'))
</script>

<style scoped>
/* 导航栏：透明背景 + 滚动时 backdrop-blur */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: transparent;
  transition: background var(--transition), backdrop-filter var(--transition);
}

/* 滚动后：半透明背景 + 毛玻璃模糊 */
.nav-bar.scrolled {
  background: color-mix(in srgb, var(--bg-base) 80%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 0.5px solid var(--border-subtle);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 品牌区 */
.brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
  text-decoration: none;
}
.brand-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 16px;
  color: var(--accent);
  letter-spacing: -0.02em;
}
.brand-sub {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

/* 导航链接组 */
.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 单个链接 */
.nav-link {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: color var(--transition), background var(--transition);
  position: relative;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

/* 当前页高亮：底部下划线 */
.nav-link.active {
  color: var(--accent);
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 12px;
  right: 12px;
  height: 1.5px;
  background: var(--accent);
  border-radius: 1px;
}

/* 对比数量徽章 */
.compare-count {
  display: inline-block;
  margin-left: 4px;
  padding: 0 6px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  font-size: 11px;
  font-family: var(--font-mono);
  background: var(--accent);
  color: var(--text-inverse);
  border-radius: 9px;
}

/* 主内容区 */
.main-content {
  min-height: calc(100vh - 56px);
}
</style>
