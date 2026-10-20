import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { ImportResumeModal } from './ImportResumeModal';
import { TargetWorkspace } from './TargetWorkspace';

// Each test drives the job promises by hand to check stale-result guarding.
type Pending = { kind: string; resolve: (value: unknown) => void; reject: (error: unknown) => void; cancel: ReturnType<typeof vi.fn> };
const jobs = vi.hoisted(() => ({ list: [] as Pending[] }));
vi.mock('../content/contentJobs', () => ({
  runContentJob: (_profile: string, kind: string) => {
    let resolve!: (value: unknown) => void;
    let reject!: (error: unknown) => void;
    const result = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    const cancel = vi.fn();
    jobs.list.push({ kind, resolve, reject, cancel });
    return { result, cancel };
  },
}));

const RESUME = {
  profile: 'alice', visibility: 'private', summary: '', skills: [], skill_groups: [], experiences: [], projects: [],
  outputs: [], education: [], honors: [], extra_sections: [], section_titles: {},
  basics: { name: '王某', title: '', tagline: '', location: '', phone: '', email: '', links: [] },
};

const MATCH = {
  method: 'llm', score: 72, summary: '匹配度中上', requirements: [], strengthen: [], gaps: [], keywords: [],
  de_emphasize: [], interview_questions: [], evidence: [], evidence_used: 0,
};

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      if (url.endsWith('/career') && method === 'GET') {
        return jsonResponse(200, {
          profile: 'alice', ai_available: true, has_resume: true, pdf_available: false, photo_url: '',
          resume: RESUME, resume_etag: 'r1', resume_markdown: '# 主简历',
          drafts: [{ id: 'd1', target: '机器人算法', etag: 'e1', jd_text: '负责 VLA', markdown: '# 定制', notes: '', path: '', updated_at: 1 }],
        });
      }
      if (url.includes('/career/import/text')) {
        return jsonResponse(200, { ok: true, method: 'text', filename: '', markdown: '', text: '一段没有结构的文字', error: '', resume: null });
      }
      if (url.includes('/career/preview')) return jsonResponse(200, { html: '<p>预览</p>' });
      return jsonResponse(200, {});
    }),
  );
}

beforeEach(() => {
  jobs.list = [];
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

/**
 * The workspace first renders the wide layout, then useMediaQuery flips it to
 * the tabbed one and remounts the panes; query the live node right before use.
 */
async function enabled(testid: string): Promise<HTMLElement> {
  await screen.findByTestId(testid);
  await new Promise((resolve) => setTimeout(resolve, 0));
  await waitFor(() => expect(screen.getByTestId(testid)).toBeEnabled());
  return screen.getByTestId(testid);
}

describe('TargetWorkspace jobs', () => {
  it('shows the match result and an error message on failure', async () => {
    renderWithProviders(<TargetWorkspace profile="alice" draftId="d1" />);
    fireEvent.click(await enabled('career-match'));
    expect(jobs.list.map((job) => job.kind)).toEqual(['career-match']);
    jobs.list[0].resolve(MATCH);
    expect(await screen.findByText('匹配度中上')).toBeInTheDocument();

    fireEvent.click(await enabled('career-match'));
    jobs.list[1].reject(new Error('模型超时'));
    expect(await screen.findByText('模型超时')).toBeInTheDocument();
  });

  it('match can be retried after a failure and runs independently of tailor', async () => {
    renderWithProviders(<TargetWorkspace profile="alice" draftId="d1" />);
    fireEvent.click(await enabled('career-match'));
    jobs.list[0].reject(new Error('first failed'));
    await screen.findByText('first failed');
    fireEvent.click(await enabled('career-match'));
    // Tailor and match are independent slots: a tailor run must not cancel the match.
    fireEvent.click(await enabled('career-tailor'));
    const [, match, tailor] = jobs.list;
    expect(match.kind).toBe('career-match');
    expect(tailor.kind).toBe('career-tailor');
    expect(match.cancel).not.toHaveBeenCalled();
    match.resolve({ ...MATCH, summary: '第二次的结果' });
    expect(await screen.findByText('第二次的结果')).toBeInTheDocument();
  });

  it('cancels running jobs when the workspace unmounts', async () => {
    const view = renderWithProviders(<TargetWorkspace profile="alice" draftId="d1" />);
    fireEvent.click(await enabled('career-match'));
    fireEvent.click(await enabled('career-tailor'));
    view.unmount();
    expect(jobs.list).toHaveLength(2);
    jobs.list.forEach((job) => expect(job.cancel).toHaveBeenCalled());
  });

  it('opens the tailored candidate for review', async () => {
    renderWithProviders(<TargetWorkspace profile="alice" draftId="d1" />);
    fireEvent.click(await enabled('career-tailor'));
    jobs.list[0].resolve({ markdown: '# AI 定制版' });
    expect(await screen.findByText('AI 定制简历（候选）')).toBeInTheDocument();
  });
});

function ModalHarness({ onApply }: { onApply: (resume: unknown) => void }) {
  const [opened, setOpened] = useState(true);
  return (
    <>
      <button type="button" onClick={() => setOpened(false)}>
        harness-close
      </button>
      <ImportResumeModal profile="alice" opened={opened} aiAvailable hasResume={false} onClose={() => setOpened(false)} onApply={onApply} />
    </>
  );
}

describe('ImportResumeModal AI recognition', () => {
  async function toRecognize(onApply = vi.fn()) {
    renderWithProviders(<ModalHarness onApply={onApply} />);
    fireEvent.click(await screen.findByText('粘贴文本'));
    fireEvent.change(screen.getByTestId('career-import-text'), { target: { value: '一段没有结构的文字' } });
    fireEvent.click(screen.getByTestId('career-import-parse'));
    fireEvent.click(await screen.findByTestId('career-import-ai'));
  }

  it('fills the resume from the AI result', async () => {
    const onApply = vi.fn();
    await toRecognize(onApply);
    expect(jobs.list.map((job) => job.kind)).toEqual(['career-structure']);
    jobs.list[0].resolve({ resume: RESUME });
    fireEvent.click(await screen.findByTestId('career-import-apply'));
    expect(onApply).toHaveBeenCalledWith(RESUME);
  });

  it('shows the AI error', async () => {
    await toRecognize();
    jobs.list[0].reject(new Error('识别失败'));
    expect(await screen.findByText('识别失败')).toBeInTheDocument();
  });

  it('closing the modal cancels recognition and ignores a late result', async () => {
    await toRecognize();
    fireEvent.click(screen.getByText('harness-close'));
    expect(jobs.list[0].cancel).toHaveBeenCalled();
    jobs.list[0].resolve({ resume: RESUME });
    await new Promise((r) => setTimeout(r, 20));
    expect(screen.queryByTestId('career-import-apply')).toBeNull();
  });
});
