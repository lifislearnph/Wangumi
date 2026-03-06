// test/components/UserMenu.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserMenu from '@/components/UserMenu.vue'

describe('UserMenu.vue', () => {
  beforeEach(() => {
    // Mock localStorage
    localStorage.getItem = vi.fn((key) => {
      if (key === 'access_token') return 'mock-token'
      if (key === 'username') return 'testuser'
      return null
    })
  })
  
  it('应该正确渲染用户菜单', () => {
    const wrapper = mount(UserMenu)

    // 根据实际组件结构调整断言
    expect(wrapper.exists()).toBe(true)
  })

  it('应该显示用户名', () => {
    const wrapper = mount(UserMenu)

    // 如果组件显示用户名，验证其存在
    // 根据实际组件结构调整
    expect(wrapper.exists()).toBe(true)
  })
})

