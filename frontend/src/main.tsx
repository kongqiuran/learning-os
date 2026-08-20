// 文件说明：React 前端启动入口。createRoot 来自 react-dom/client；StrictMode 来自 React；它把应用挂载到 index.html 的 root 节点。
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { AppProviders } from './app/providers'
import { AppRouter } from './app/router'
import './styles/index.css'

// 这个文件是整个 React 前端的“启动入口”。浏览器先加载 index.html，
// index.html 里有一个 id="root" 的空节点；下面这段代码会把 React 应用挂到这个节点里。
createRoot(document.getElementById('root')!).render(
  // StrictMode 是 React 提供的开发期检查工具：它不会显示在页面上，
  // 只是在开发环境帮助发现不安全的组件写法。
  <StrictMode>
    {/*
      AppProviders 负责给全站提供公共能力。
      当前最重要的是 React Query：它帮我们缓存接口数据、管理加载状态和错误状态。
    */}
    <AppProviders>
      {/*
        AppRouter 负责根据浏览器地址显示不同页面。
        例如 /login 显示登录页，/dashboard 显示课程列表页。
      */}
      <AppRouter />
    </AppProviders>
  </StrictMode>,
)
