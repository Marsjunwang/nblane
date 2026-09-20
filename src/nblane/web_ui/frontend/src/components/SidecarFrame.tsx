// Iframe embed for Reader API sidecar pages (Paper Library / 3D dashboard).
//
// When the backend mints a `handoffToken` (auth-on deployments), the sidecar
// session cookie is bootstrapped first: a hidden form POSTs the token to the
// sidecar's /auth/session endpoint inside a hidden iframe, and the content
// iframe only gets its `src` after that bootstrap settles — the same flow the
// Streamlit pages use (`research_ui._helpers._render_authenticated_iframe`).
// With auth off (default single-user mode) the iframe loads directly.
//
// The content frame shows a loading state until its onLoad fires, and the
// 重新加载 button re-runs the whole bootstrap (form POST + fresh iframe) —
// the escape hatch when a slow network or an expired sidecar session would
// otherwise leave a blank frame with no way out.

import { Button, Center, Group, Loader, Text } from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';
import { useEffect, useId, useRef, useState } from 'react';

interface SidecarFrameProps {
  /** Accessible iframe title. */
  title: string;
  /** Full sidecar page URL to embed. */
  url: string;
  /** Sidecar origin ('' means same-origin; the auth URL is then relative). */
  base: string;
  /** Short-lived handoff token; empty when the sidecar needs no session. */
  handoffToken?: string;
  height?: number;
}

export function SidecarFrame({
  title,
  url,
  base,
  handoffToken = '',
  height = 720,
}: SidecarFrameProps) {
  const targetName = `sidecar-auth-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const formRef = useRef<HTMLFormElement>(null);
  const [ready, setReady] = useState(!handoffToken);
  const [loaded, setLoaded] = useState(false);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    setReady(!handoffToken);
    setLoaded(false);
    if (!handoffToken) {
      return;
    }
    const form = formRef.current;
    if (form) {
      try {
        form.submit();
      } catch {
        // jsdom does not implement form submission; the test only cares
        // that the bootstrap attempt happens before the iframe src is set.
      }
    }
    // The hidden auth iframe has no reliable cross-origin load signal; give
    // the cookie bootstrap a short head start, then load the content frame.
    const timer = window.setTimeout(() => setReady(true), 800);
    return () => window.clearTimeout(timer);
  }, [handoffToken, url, reloadNonce]);

  return (
    <>
      {handoffToken ? (
        <>
          <iframe
            name={targetName}
            title={`${title} auth`}
            aria-hidden
            style={{ display: 'none', width: 0, height: 0, border: 0 }}
          />
          <form
            ref={formRef}
            action={`${base}/auth/session`}
            method="post"
            target={targetName}
            style={{ display: 'none' }}
          >
            <input type="hidden" name="token" value={handoffToken} />
          </form>
        </>
      ) : null}
      <Group justify="flex-end" mb={4}>
        <Button
          size="compact-xs"
          variant="default"
          leftSection={<IconRefresh size={14} />}
          onClick={() => setReloadNonce((nonce) => nonce + 1)}
        >
          重新加载
        </Button>
      </Group>
      {ready ? (
        <div style={{ position: 'relative' }}>
          <iframe
            key={reloadNonce}
            title={title}
            src={url}
            data-testid="sidecar-frame"
            onLoad={() => setLoaded(true)}
            style={{ width: '100%', height, border: 0, borderRadius: 8 }}
          />
          {!loaded && (
            <Center
              data-testid="sidecar-loading"
              style={{
                position: 'absolute',
                inset: 0,
                background: 'var(--mantine-color-body)',
              }}
            >
              <Loader size="sm" />
              <Text size="sm" c="dimmed" ml="xs">
                加载中…长时间无响应请点击「重新加载」。
              </Text>
            </Center>
          )}
        </div>
      ) : (
        <Center style={{ height }} data-testid="sidecar-loading">
          <Loader size="sm" />
        </Center>
      )}
    </>
  );
}
