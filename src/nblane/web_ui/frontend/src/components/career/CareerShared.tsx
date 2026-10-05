import { Badge, Box, Button, Loader, Menu, Text, Tooltip } from '@mantine/core';
import { IconDownload, IconFileTypeHtml, IconFileTypePdf, IconMarkdown } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { downloadCareerExport, previewCareer } from '../../api/hooks';
import type { ResumeDoc } from '../../api/types';
import { saveStateLabel, type SaveState } from './useAutosave';

const SAVE_COLORS: Record<SaveState, string> = {
  saved: 'gray',
  dirty: 'yellow',
  saving: 'blue',
  error: 'red',
  conflict: 'orange',
};

export function SaveBadge({ state, savedAt, testid }: { state: SaveState; savedAt: Date | null; testid: string }) {
  return (
    <Badge variant="light" color={SAVE_COLORS[state]} data-testid={testid} style={{ textTransform: 'none' }}>
      {saveStateLabel(state, savedAt)}
    </Badge>
  );
}

/** md / html / pdf download menu; rendering happens server-side in memory. */
export function ExportMenu({
  profile,
  pdfAvailable,
  source,
  beforeExport,
  label = '导出',
}: {
  profile: string;
  pdfAvailable: boolean;
  /** What to export: a saved draft id, explicit Markdown, or the master resume. */
  source: { draft_id?: string; markdown?: string };
  /** Flush pending edits first so the export matches the screen. */
  beforeExport?: () => Promise<unknown>;
  label?: string;
}) {
  const [busy, setBusy] = useState<string>('');
  const [error, setError] = useState('');
  const run = async (format: 'md' | 'html' | 'pdf') => {
    setBusy(format);
    setError('');
    try {
      await beforeExport?.();
      await downloadCareerExport(profile, { format, ...source });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy('');
    }
  };
  return (
    <Box>
      <Menu position="bottom-end" withinPortal>
        <Menu.Target>
          <Button
            size="xs"
            variant="default"
            leftSection={busy ? <Loader size={12} /> : <IconDownload size={15} />}
            data-testid="career-export"
          >
            {label}
          </Button>
        </Menu.Target>
        <Menu.Dropdown>
          <Tooltip label="服务器未找到 Chromium，可导出 HTML 后用浏览器打印" disabled={pdfAvailable} withinPortal>
            <div>
              <Menu.Item
                leftSection={<IconFileTypePdf size={15} />}
                disabled={!pdfAvailable}
                onClick={() => void run('pdf')}
                data-testid="career-export-pdf"
              >
                PDF（A4 一页纸）
              </Menu.Item>
            </div>
          </Tooltip>
          <Menu.Item leftSection={<IconFileTypeHtml size={15} />} onClick={() => void run('html')} data-testid="career-export-html">
            HTML（含照片，可打印）
          </Menu.Item>
          <Menu.Item leftSection={<IconMarkdown size={15} />} onClick={() => void run('md')} data-testid="career-export-md">
            Markdown
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
      {error && (
        <Text size="xs" c="red" mt={4}>
          {error}
        </Text>
      )}
    </Box>
  );
}

/**
 * Live A4 preview: renders the unsaved resume (or a Markdown draft) through
 * the same server renderer as HTML/PDF export, debounced while typing.
 */
export function ResumePreview({
  profile,
  resume,
  markdown,
  height = '100%',
}: {
  profile: string;
  resume?: ResumeDoc;
  markdown?: string;
  height?: number | string;
}) {
  const [html, setHtml] = useState('');
  const [error, setError] = useState('');
  const seq = useRef(0);
  const payload = JSON.stringify(resume ? { resume } : { markdown: markdown ?? '' });
  useEffect(() => {
    const id = ++seq.current;
    const timer = window.setTimeout(() => {
      previewCareer(profile, JSON.parse(payload))
        .then((result) => {
          if (id === seq.current) {
            setHtml(result.html);
            setError('');
          }
        })
        .catch((err: unknown) => id === seq.current && setError(err instanceof Error ? err.message : String(err)));
    }, 400);
    return () => window.clearTimeout(timer);
  }, [payload, profile]);
  return (
    <Box style={{ height, position: 'relative', background: '#e9ecf2', borderRadius: 8, overflow: 'hidden' }}>
      {error && (
        <Text size="xs" c="red" p="xs">
          预览失败：{error}
        </Text>
      )}
      {!html && !error && (
        <Box p="md">
          <Loader size="sm" />
        </Box>
      )}
      {html && (
        <iframe
          title="简历预览"
          srcDoc={html}
          sandbox="allow-same-origin"
          data-testid="career-preview"
          style={{ border: 0, width: '100%', height: '100%', display: 'block' }}
        />
      )}
    </Box>
  );
}
