// 文件说明：全站 Provider 配置。Provider 是 React 的上下文提供者写法；QueryClientProvider 来自 TanStack React Query，用来把接口缓存能力传给所有子组件。
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

// AppProviders 的作用：把“全站都要用到的能力”包在最外层。
// children 代表被它包住的页面内容；在 main.tsx 里，children 就是 <AppRouter />。
export function AppProviders({ children }: { children: ReactNode }) {
  // QueryClient 是 React Query 的核心对象。
  // 你可以把它理解成“前端接口数据管家”：负责请求、缓存、刷新、错误状态等。
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // staleTime 表示：请求成功后的 60 秒内，数据先当作“新鲜数据”。
            // 这样用户切换页面回来时，不会每次都立刻重新请求，页面会更快。
            staleTime: 60_000,
            // retry: false 表示接口失败后不自动重试。
            // 这样错误会直接展示给用户或开发者，不会悄悄多发请求。
            retry: false,
            // refetchOnWindowFocus: false 表示用户切回浏览器窗口时不自动刷新。
            // 这是为了避免用户正在看页面时，焦点切换导致数据突然变化。
            refetchOnWindowFocus: false,
          },
        },
      }),
  )

  // QueryClientProvider 把 queryClient 放进 React 上下文。
  // 被它包住的所有组件，都可以通过 useQuery / useMutation 使用同一个接口数据管家。
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
