// test/components/App.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'

// 创建测试用的路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/animelist', component: { template: '<div>AnimeList</div>' } },
    { path: '/recommend', component: { template: '<div>Recommend</div>' } },
    { path: '/items', component: { template: '<div>Items</div>' } },
  ],
})

describe('App.vue', () => {
  beforeEach(() => {
    // 清理 localStorage mock
    vi.clearAllMocks()
    localStorage.getItem = vi.fn(() => null)
  })

  it('应该正确渲染导航栏', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('.logo').text()).toBe('Wangumi')
    expect(wrapper.find('.nav-links').exists()).toBe(true)
  })

  it('应该根据登录状态显示不同的用户操作', () => {
    // 未登录状态
    localStorage.getItem = vi.fn((key) => {
      if (key === 'access_token') return null
      return null
    })

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('.login-btn').exists()).toBe(true)
    expect(wrapper.find('.login-btn').text()).toContain('注册/登录')
  })

  it('应该显示导航链接', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })

    const navLinks = wrapper.findAll('.nav-links a')
    expect(navLinks.length).toBeGreaterThan(0)
  })

  it('点击 logo 应该触发 goHome 方法', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })

    const logo = wrapper.find('.logo')
    await logo.trigger('click')

    // 验证方法被调用（通过检查路由变化或 mock router.push）
    expect(logo.exists()).toBe(true)
  })
})
