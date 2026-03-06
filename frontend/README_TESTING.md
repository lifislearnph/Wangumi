# 测试快速开始
## 1. 安装依赖
```bash
cd frontend
npm install
```
这将安装所有测试相关的依赖，包括：
- `vitest` - 测试框架
- `@vue/test-utils` - Vue 组件测试工具
- `jsdom` - DOM 环境模拟
- `@vitest/ui` - 测试 UI 界面
- `@vitest/coverage-v8` - 代码覆盖率工具

## 2. 运行测试
### 方式一：命令行模式
```bash
# 运行所有测试
npm test
# 监听模式（文件变化时自动重新运行）
npm test -- --watch
```

### 方式二：UI 界面模式（推荐）
```bash
npm run test:ui
```
这会打开一个浏览器界面，可以：
- 查看所有测试用例
- 查看测试结果
- 查看代码覆盖率
- 过滤和搜索测试

## 3. GitLab CI 集成
前端测试已集成到项目根目录的 `.gitlab-ci.yml` 中。当推送代码到 `dev` 分支或创建合并请求时，会自动运行：
- **django-tests**: 后端 Django 测试
- **frontend-tests**: 前端 Vitest 测试（包括覆盖率报告）
测试结果和覆盖率报告会在 GitLab CI/CD 界面中显示。

## 4. 编写新测试

### 组件测试示例
在 `test/components` 目录下创建测试文件：
```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '../MyComponent.vue'

describe('MyComponent', () => {
  it('应该正确渲染', () => {
    const wrapper = mount(MyComponent)
    expect(wrapper.find('.my-class').exists()).toBe(true)
  })
})
```

### 服务测试示例
在 `test/services` 目录下创建测试文件：
```typescript
import { describe, it, expect, vi } from 'vitest'
import axios from 'axios'
import { myService } from '../myService'

vi.mock('axios')

describe('myService', () => {
  it('应该成功获取数据', async () => {
    axios.get = vi.fn().mockResolvedValue({ data: { code: 0 } })
    const result = await myService.getData()
    expect(result.code).toBe(0)
  })
})
```

## 5. 测试文件命名规范
- 组件测试：`ComponentName.test.ts` 或 `ComponentName.spec.ts`
- 服务测试：`serviceName.test.ts` 或 `serviceName.spec.ts`


