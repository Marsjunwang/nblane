import { fireEvent, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ProfileCreateDialog } from './ProfileCreateDialog';

const schemas = [{ name: 'engineering', domain: '工程实践', description: '通过项目积累技能。' }];

afterEach(() => vi.unstubAllGlobals());

function renderDialog(onClose = vi.fn()) {
  renderWithProviders(
    <Routes>
      <Route path="/" element={<ProfileCreateDialog onClose={onClose} />} />
      <Route path="/p/:name/projects" element={<div>新档案项目页</div>} />
      <Route path="/p/:name/home" element={<div>新档案首页</div>} />
    </Routes>,
  );
  return onClose;
}

async function chooseProfile() {
  fireEvent.change(screen.getByRole('textbox', { name: '档案名' }), { target: { value: '小林' } });
  await waitFor(() => expect(screen.getByRole('button', { name: '下一步' })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: '下一步' }));
  await screen.findByRole('textbox', { name: '北极星' });
}

describe('ProfileCreateDialog', () => {
  it('retains the profile name when schema loading fails and retries without closing', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(503, { message: '领域服务暂时不可用' }))
      .mockResolvedValue(jsonResponse(200, schemas));
    vi.stubGlobal('fetch', fetchMock);
    const onClose = renderDialog();
    fireEvent.change(screen.getByRole('textbox', { name: '档案名' }), { target: { value: '小林' } });
    await screen.findByText('领域加载失败');
    expect(screen.getByRole('button', { name: '下一步' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));
    await waitFor(() => expect(screen.getByRole('button', { name: '下一步' })).toBeEnabled());
    expect(screen.getByRole('textbox', { name: '档案名' })).toHaveValue('小林');
    expect(onClose).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('keeps all fields after a failed creation, then retries and opens the first project', async () => {
    const writes: RequestInit[] = [];
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        writes.push(init);
        return writes.length === 1
          ? jsonResponse(503, { message: '保存暂时失败，请重试' })
          : jsonResponse(200, { name: '小林', has_first_plan: true });
      }
      return jsonResponse(200, schemas);
    }));
    const onClose = renderDialog();
    await chooseProfile();
    for (const [name, value] of [['北极星', '独立完成产品'], ['阶段目标', '交付原型'], ['首个项目', '机器人原型'], ['第一件任务', '整理验收标准']]) {
      fireEvent.change(screen.getByRole('textbox', { name }), { target: { value } });
    }
    fireEvent.click(screen.getByRole('button', { name: '创建档案' }));
    await screen.findByText('保存暂时失败，请重试');
    expect(screen.getByRole('textbox', { name: '第一件任务' })).toHaveValue('整理验收标准');
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '上一步' }));
    expect(screen.getByRole('textbox', { name: '档案名' })).toHaveValue('小林');
    fireEvent.click(screen.getByRole('button', { name: '下一步' }));
    fireEvent.click(screen.getByRole('button', { name: '创建档案' }));
    await screen.findByText('新档案项目页');
    expect(onClose).toHaveBeenCalledOnce();
    expect(writes).toHaveLength(2);
    expect(writes[1].body).toBe(writes[0].body);
    expect(JSON.parse(String(writes[1].body))).toEqual({
      name: '小林', schema: 'engineering', north_star: '独立完成产品', goal_title: '交付原型',
      project_title: '机器人原型', task_title: '整理验收标准',
    });
  });

  it('opens the home page when the optional first plan is left empty', async () => {
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) =>
      init?.method === 'POST'
        ? jsonResponse(200, { name: '小林', has_first_plan: false })
        : jsonResponse(200, schemas),
    ));
    renderDialog();
    await chooseProfile();
    fireEvent.click(screen.getByRole('button', { name: '创建档案' }));
    await screen.findByText('新档案首页');
  });

  it('keeps a task draft and asks for a goal before submitting it', async () => {
    const fetchMock = vi.fn().mockImplementation(async () => jsonResponse(200, schemas));
    vi.stubGlobal('fetch', fetchMock);
    renderDialog();
    await chooseProfile();
    fireEvent.change(screen.getByRole('textbox', { name: '第一件任务' }), { target: { value: '整理资料' } });
    fireEvent.click(screen.getByRole('button', { name: '创建档案' }));
    await screen.findByText('请先写下阶段目标，再添加项目和任务。');
    expect(screen.getByRole('textbox', { name: '第一件任务' })).toHaveValue('整理资料');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
