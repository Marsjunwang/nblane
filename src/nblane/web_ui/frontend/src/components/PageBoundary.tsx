import { Alert, Button, Center, Group, Loader, Stack, Text } from '@mantine/core';
import { Component, createContext, createElement, lazy, Suspense, useContext } from 'react';
import type { ComponentPropsWithRef, ComponentType, ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

const RetryGeneration = createContext(0);

/** Recreate React.lazy on retry; rejected imports otherwise stay cached. */
export function retryableLazy<T extends ComponentType<any>>(load: () => Promise<{ default: T }>) {
  // A suspended initial render discards hook state, including useMemo.
  // Keep lazy identities outside the component until it can actually mount.
  const pages = new Map<number, ReturnType<typeof lazy<T>>>();
  return function RetryablePage(props: ComponentPropsWithRef<T>) {
    const generation = useContext(RetryGeneration);
    let Page = pages.get(generation);
    if (!Page) {
      Page = lazy(load);
      pages.set(generation, Page);
    }
    return createElement(Page, props);
  };
}

export class PageBoundary extends Component<{ children: ReactNode }, { failed: boolean; generation: number }> {
  state = { failed: false, generation: 0 };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <Stack p="md" gap="md" role="alert">
          <Alert color="red" title="页面暂时无法打开">
            请检查网络后重试。你也可以通过导航打开其他页面。
          </Alert>
          <Text size="sm" c="dimmed">先重试当前页面。如果仍打不开，可以刷新整个应用；刷新前请确认其他页面没有未保存的编辑。</Text>
          <Group>
            <Button onClick={() => this.setState(({ generation }) => ({ failed: false, generation: generation + 1 }))}>
              重新加载页面
            </Button>
            <Button variant="subtle" onClick={() => window.location.reload()}>刷新整个应用</Button>
          </Group>
        </Stack>
      );
    }
    return (
      <RetryGeneration.Provider value={this.state.generation}>
        <Suspense fallback={<Center py="xl"><Loader aria-label="正在打开页面" /></Center>}>
          {this.props.children}
        </Suspense>
      </RetryGeneration.Provider>
    );
  }
}

/** Keep the shell mounted, but reset a failed page when navigation changes. */
export function RouteContent({ children }: { children: ReactNode }) {
  const location = useLocation();
  return <PageBoundary key={location.pathname}>{children}</PageBoundary>;
}
