<template>
  <!-- 根组件：顶部导航栏 + 路由出口 -->
  <div class="app-layout">
    <!-- el-menu：Element Plus 的菜单组件。
         mode="horizontal"：水平横向菜单。
         router：开启路由模式，menu-item 的 index 就是跳转路径。
         :default-active：高亮当前路由对应的菜单项。 -->
    <el-menu mode="horizontal" router :default-active="route.path" class="nav-menu">
      <div class="logo">3DGS-KB</div>
      <!-- el-menu-item：菜单项。index 是路由路径（因为开了 router 模式） -->
      <el-menu-item index="/papers">论文列表</el-menu-item>
      <el-menu-item index="/dashboard">统计仪表盘</el-menu-item>
      <el-menu-item index="/compare">
        对比
        <!-- 对比菜单显示选中数量徽章 -->
        <el-badge v-if="store.selectedForCompare.length" :value="store.selectedForCompare.length" class="compare-badge" />
      </el-menu-item>
    </el-menu>

    <!-- router-view：路由出口，当前路由匹配的页面组件在这里渲染 -->
    <router-view />
  </div>
</template>

<script setup>
// useRoute：拿到当前路由信息（用于高亮当前菜单项）。
import { useRoute } from 'vue-router'
import { usePapersStore } from './stores/papers'

const route = useRoute()
const store = usePapersStore()
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;  /* border-box：宽度包含 padding 和 border，布局更直观 */
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;     /* Element Plus 推荐的浅灰背景 */
  color: #303133;
}

/* 导航栏样式 */
.nav-menu {
  padding: 0 24px;
  position: sticky;    /* sticky：滚动时吸顶 */
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);  /* 底部阴影 */
}

.logo {
  font-weight: 700;
  font-size: 18px;
  color: #409eff;
  margin-right: 32px;
  line-height: 60px;   /* 和菜单项高度对齐 */
}

.compare-badge {
  margin-left: 4px;
}
</style>
