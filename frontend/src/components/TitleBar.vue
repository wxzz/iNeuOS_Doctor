<template>
  <div class="title-wrapper">
    <div class="title-section">
      <h1 class="title">{{ title }}</h1>
      <p class="title-subtitle">{{ subtitle }}</p>
    </div>
    <div class="user-status" @click="handleStatusClick" :title="userStatusTitle">
      <span v-if="!isLoggedIn" class="login-text">登录</span>
      <img v-else :src="userAvatar" alt="头像" class="user-avatar" />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    isLoggedIn: boolean
    userAvatar: string
    userStatusTitle: string
  }>(),
  {
    subtitle: '• 让医疗更智慧，让健康更普惠 •'
  }
)

const emit = defineEmits<{ statusClick: [] }>()

const handleStatusClick = () => {
  emit('statusClick')
}
</script>

<style scoped>
.title-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 16px 0;
  padding: 4px 10px;
  background: linear-gradient(135deg, #667eea 0%, #667eea 100%);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.title-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  letter-spacing: 1px;
  margin: 0;
}

.title-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  margin: 3px 0 0 0;
  font-weight: 400;
  letter-spacing: 0.5px;
  flex: 1;
}

.user-status {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
  margin-left: 10px;
}

.user-status:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.login-text {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.user-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.5);
}
</style>
