<template>
  <div class="app-layout">
    <!-- 轻量导航栏：替代原来的 el-menu
         左边站名 + 右边文字链接，当前页加下划线
         滚动时加 backdrop-blur 增强可读性
         <1024px 时 nav-links 折叠为汉堡按钮 + el-drawer -->
    <nav class="nav-bar" :class="{ scrolled: isScrolled }">
      <div class="nav-inner">
        <!-- 站名 -->
        <router-link to="/" class="brand">
          <span class="brand-name">3DGS·KB</span>
          <span v-show="!isMobile" class="brand-sub">IP Protection Archive</span>
        </router-link>

        <!-- 导航链接（桌面端） -->
        <div v-show="!isMobile" class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: isHome }">首页</router-link>
          <router-link to="/papers" class="nav-link" :class="{ active: isPapers }">论文</router-link>
          <router-link to="/dashboard" class="nav-link" :class="{ active: isDashboard }">仪表盘</router-link>
          <router-link to="/compare" class="nav-link compare-link" :class="{ active: isCompare }">
            对比
            <span v-if="store.selectedForCompare.length" class="compare-count">{{ store.selectedForCompare.length }}</span>
          </router-link>
        </div>

        <!-- 移动端汉堡按钮 -->
        <button
          v-show="isMobile"
          class="menu-trigger"
          type="button"
          aria-label="打开菜单"
          @click="drawerOpen = true"
        >
          <span class="bar"></span>
          <span class="bar"></span>
          <span class="bar"></span>
        </button>
      </div>
    </nav>

    <!-- 移动端抽屉菜单 -->
    <el-drawer
      v-model="drawerOpen"
      direction="rtl"
      :size="280"
      :with-header="false"
      class="nav-drawer"
    >
      <nav class="drawer-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="drawer-link"
          :class="{ active: item.isActive }"
          @click="drawerOpen = false"
        >
          <span>{{ item.label }}</span>
          <span
            v-if="item.badge"
            class="compare-count"
          >{{ item.badge }}</span>
        </router-link>
      </nav>
    </el-drawer>

    <!-- 路由出口 -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- 页脚题跋：archive 的 colophon -->
    <footer class="colophon">
      <span>3DGS·KB — 3D Gaussian Splatting 水印与 IP 保护论文档案</span>
      <span class="colophon-note">arXiv × DeepSeek Pipeline</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePapersStore } from './stores/papers'
import { useMediaQuery } from './composables/useMediaQuery'

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

// 移动端 <1024px 触发汉堡 + drawer
const isMobile = useMediaQuery('(max-width: 1023px)')
const drawerOpen = ref(false)
// 切到桌面时关闭 drawer，避免状态错位
watch(isMobile, (v) => { if (!v) drawerOpen.value = false })

// 抽屉中的导航项（与桌面链接同构）
const navItems = computed(() => [
  { path: '/', label: '首页', isActive: isHome.value },
  { path: '/papers', label: '论文', isActive: isPapers.value },
  { path: '/dashboard', label: '仪表盘', isActive: isDashboard.value },
  {
    path: '/compare',
    label: '对比',
    isActive: isCompare.value,
    badge: store.selectedForCompare.length || 0,
  },
])
</script>

<style scoped>
/* 导航栏：常驻 hairline 底边（编目卡头感），滚动时毛玻璃 */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: transparent;
  border-bottom: 0.5px solid var(--border-subtle);
  transition: background var(--transition), backdrop-filter var(--transition);
}

/* 滚动后：半透明背景 + 毛玻璃模糊 */
.nav-bar.scrolled {
  background: color-mix(in srgb, var(--bg-base) 82%, transparent);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 品牌区 */
.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
  text-decoration: none;
}
.brand-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 17px;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.brand-sub {
  font-size: 10px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
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

/* 当前页高亮：底部墨线 */
.nav-link.active {
  color: var(--text-primary);
  font-weight: 500;
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 12px;
  right: 12px;
  height: 1.5px;
  background: var(--text-primary);
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

/* 移动端汉堡按钮 */
.menu-trigger {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 40px;
  height: 40px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background var(--transition);
}
.menu-trigger:hover { background: var(--bg-hover); }
.menu-trigger .bar {
  display: block;
  width: 20px;
  height: 1.5px;
  margin: 0 auto;
  background: var(--text-primary);
  border-radius: 1px;
  transition: transform var(--transition), opacity var(--transition);
}

/* 抽屉导航 */
.drawer-nav {
  display: flex;
  flex-direction: column;
  padding: var(--space-lg) 0;
}
.drawer-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  font-size: 15px;
  color: var(--text-primary);
  text-decoration: none;
  border-bottom: 0.5px solid var(--border-subtle);
  transition: background var(--transition);
  min-height: 48px; /* 触控目标 ≥44px */
}
.drawer-link:hover { background: var(--bg-hover); }
.drawer-link.active {
  color: var(--accent);
  font-weight: 500;
  background: var(--accent-soft);
}

/* 主内容区 */
.main-content {
  min-height: calc(100vh - 60px);
}

/* 页脚题跋 */
.colophon {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
  border-top: 0.5px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-tertiary);
}
.colophon-note {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
}

/* footer 移动端堆叠 */
@media (max-width: 639px) {
  .colophon {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
}

/* 导航内边距移动端收紧 */
@media (max-width: 639px) {
  .nav-inner { padding: 0 var(--space-md); }
}
</style>
