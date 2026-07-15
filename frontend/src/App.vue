<template>
  <!-- 根组件：只放一个 router-view，由路由决定显示哪个页面 -->
  <router-view />
</template>

<script setup>
// <script setup>：Vue 3 的编译宏语法，组件逻辑写在这里。
// 这个根组件没有逻辑，只做布局容器，所以是空的。
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
</style>
