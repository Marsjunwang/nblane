import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { HealthPage } from './HealthPage';

const REPORT = {
  profile: 'alice',
  can_publish_context: false,
  summary_counts: { error: 1, warning: 1 },
  issues: [
    {
      severity: 'error',
      category: 'skill_tree',
      title: '技能树缺少节点',
      detail: 'skill-tree.yaml 为空',
      action: '运行 nblane ingest',
    },
    {
      severity: 'warning',
      category: 'evidence',
      title: '证据池为空',
      detail: '',
      action: '',
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('HealthPage', () => {
  it('renders the health report with severity badges grouped by category', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/profiles/alice/health')) {
          return jsonResponse(200, REPORT);
        }
        return jsonResponse(404, { code: 'not_found', message: 'not found' });
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/p/:name/health" element={<HealthPage />} />
      </Routes>,
      '/p/alice/health',
    );

    expect(await screen.findByText('alice · 健康检查')).toBeInTheDocument();
    // Issues grouped under their category headings.
    expect(screen.getByText('skill_tree')).toBeInTheDocument();
    expect(screen.getByText('evidence')).toBeInTheDocument();
    // Severity badges from the summary counts.
    expect(screen.getByText('error: 1')).toBeInTheDocument();
    expect(screen.getByText('warning: 1')).toBeInTheDocument();
    // Issue titles and the publish-blocked alert.
    expect(screen.getByText('技能树缺少节点')).toBeInTheDocument();
    expect(screen.getByText('证据池为空')).toBeInTheDocument();
    expect(screen.getByText('上下文暂不可发布')).toBeInTheDocument();
  });
});
