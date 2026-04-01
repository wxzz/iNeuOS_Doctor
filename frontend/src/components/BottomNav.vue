<template>
  <div>
    <div class="bottom-nav">
      <button class="nav-btn" :class="{ active: active === 'home' }" @click="goTo('/')">
        医学诊室
      </button>
      <div class="nav-menu-wrapper">
        <button class="nav-btn" :class="{ active: isBusinessActive }" @click="toggleBusinessMenu">
          业务管理
          <span class="menu-arrow" :class="{ open: showBusinessMenu }">▲</span>
        </button>
        <div v-if="showBusinessMenu" class="business-menu">
          <button
            class="menu-item"
            :class="{ 'active-menu-item': active === 'history' }"
            @click="goTo('/medical-record')"
          >
            分析记录
          </button>
          <button
            class="menu-item"
            :class="{ 'active-menu-item': active === 'chat-history' }"
            @click="goTo('/medical-chat-record')"
          >
            问诊记录
          </button>
          <button
            class="menu-item"
            :class="{ 'active-menu-item': active === 'invite' }"
            @click="goTo('/invite-record')"
          >
            邀请记录
          </button>
          <button
            class="menu-item"
            :class="{ 'active-menu-item': active === 'pay' }"
            @click="goTo('/wechat-pay-record')"
          >
            赞助记录
          </button>
          <button
            class="menu-item"
            :class="{ 'active-menu-item': active === 'withdraw' }"
            @click="goTo('/wechat-withdraw-record')"
          >
            提现记录
          </button>
        </div>
      </div>
      <button class="nav-btn" :class="{ active: active === 'mine' }" @click="goTo('/my-info')">
        我的
      </button>
    </div>
    <div class="icp-footer">
      <span v-if="icpPrefix" class="icp-prefix">{{ icpPrefix }}&nbsp;|</span>
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">京ICP备2020048381号-3</a>&nbsp;|
      <span v-if="appVersion" class="version-text">版本:v{{ appVersion }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = withDefaults(
  defineProps<{
    active: 'home' | 'history' | 'chat-history' | 'invite' | 'pay' | 'withdraw' | 'mine'
    icpPrefix?: string
  }>(),
  {
    icpPrefix: ''
  }
)

const router = useRouter()
const appVersion = (window as { VERSION?: string }).VERSION || ''
const showBusinessMenu = ref(false)

const isBusinessActive = computed(() =>
  ['history', 'chat-history', 'invite', 'pay', 'withdraw'].includes(props.active)
)

const toggleBusinessMenu = () => {
  showBusinessMenu.value = !showBusinessMenu.value
}

const goTo = (path: string) => {
  showBusinessMenu.value = false
  router.push(path)
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 24px;
  left: 0;
  right: 0;
  display: flex;
  background-color: #fff;
  border-top: 1px solid #ddd;
  padding: 8px 0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.icp-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  background-color: #fff;
  color: #666;
  border-top: 1px solid #eee;
  z-index: 999;
}

.icp-footer a {
  color: #666;
  text-decoration: none;
}

.icp-footer a:hover {
  color: #4a90e2;
  text-decoration: underline;
}

.icp-prefix {
  margin-right: 6px;
}

.version-text {
  margin-left: 2px;
  font-size: 12px;
  color: #666;
  line-height: 24px;
}

.nav-menu-wrapper {
  flex: 1;
  position: relative;
}

.nav-btn {
  flex: 1;
  width: 100%;
  padding: 12px;
  border: none;
  background-color: transparent;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 500;
}

.nav-btn:hover {
  color: #4a90e2;
  background-color: rgba(74, 144, 226, 0.08);
}

.nav-btn.active {
  color: #4a90e2;
  font-weight: bold;
}

.menu-arrow {
  display: inline-block;
  margin-left: 2px;
  font-size: 10px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: rotate(180deg);
}

.menu-arrow.open {
  transform: rotate(0deg);
}

.business-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, #ffffff, #fafafa);
  border: 2px solid #4a90e2;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -8px 24px rgba(74, 144, 226, 0.15), 0 -4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  animation: slideUpMenu 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 100;
}

@keyframes slideUpMenu {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-item {
  width: 100%;
  padding: 14px 16px;
  border: none;
  background-color: transparent;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  border-bottom: 1px solid #e8f0ff;
  font-weight: 500;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.12), rgba(118, 75, 162, 0.08));
  color: #4a90e2;
  padding-left: 20px;
  padding-right: 12px;
  font-weight: 600;
}

.menu-item.active-menu-item {
  color: #4a90e2;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.12), rgba(118, 75, 162, 0.08));
}

@media (max-width: 640px) {
  .nav-btn {
    padding: 10px;
    font-size: 14px;
    gap: 4px;
  }

  .business-menu {
    bottom: 100%;
  }

  .menu-item {
    padding: 12px 12px;
    font-size: 13px;
  }
}
</style>
