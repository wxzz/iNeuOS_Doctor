import { createRouter, createWebHistory } from 'vue-router'
import Medical from '../views/Medical.vue'
import MedicalRecord from '../views/MedicalRecord.vue'
import MedicalChatRecord from '../views/MedicalChatRecord.vue'
import MyInfo from '../views/MyInfo.vue'
import InviteRecord from '../views/InviteRecord.vue'
import WechatPayRecord from '../views/WechatPayRecord.vue'
import WechatWithdrawRecord from '../views/WechatWithdrawRecord.vue'
import Login from '../views/Login.vue'
import RegisterUser from '../views/RegisterUser.vue'
import { useAuth } from '../composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/',
      name: 'medical',
      component: Medical,
    },
    {
      path: '/medical-record',
      name: 'medical-record',
      component: MedicalRecord,
    },
    {
      path: '/medical-chat-record',
      name: 'medical-chat-record',
      component: MedicalChatRecord,
    },
    {
      path: '/my-info',
      name: 'my-info',
      component: MyInfo,
      meta: { requiresAuth: true },
    },
    {
      path: '/invite-record',
      name: 'invite-record',
      component: InviteRecord,
      meta: { requiresAuth: true },
    },
    {
      path: '/wechat-pay-record',
      name: 'wechat-pay-record',
      component: WechatPayRecord,
      meta: { requiresAuth: true },
    },
    {
      path: '/wechat-withdraw-record',
      name: 'wechat-withdraw-record',
      component: WechatWithdrawRecord,
      meta: { requiresAuth: true },
    },
    {
      path: '/register-user',
      name: 'register-user',
      component: RegisterUser,
    },
  ],
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const { checkLogin } = useAuth()
  
  if (to.meta.requiresAuth && !checkLogin()) {
    // 需要登录但未登录，重定向到登录页
    next('/login')
  } else {
    next()
  }
})

export default router
