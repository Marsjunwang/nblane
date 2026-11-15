import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const staticRoot = path.resolve(fileURLToPath(new URL('../../src/nblane/web_ui/static/', import.meta.url)));
const contentTypes = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript',
  '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
  '.json': 'application/json', '.webmanifest': 'application/manifest+json',
};

// These credentials belong only to this in-memory loopback fixture.
export const fixtureCredentials = Object.freeze({ username: 'fixture', password: 'sticker-smoke-only' });
const currentUser = {
  id: 'fixture', display_name: '演示账号', role: 'member', auth_enabled: true,
  profiles: ['demo'], teams: [], must_change_password: false,
};
const today = new Date().toISOString().slice(0, 10);

async function readJson(request) {
  let body = '';
  for await (const chunk of request) {
    body += chunk;
    if (body.length > 16_384) throw new Error('Fixture request too large');
  }
  return JSON.parse(body || '{}');
}

/** Serve the committed SPA against disposable API state, never a real profile. */
export async function startMiniFixture(port = 0) {
  const state = {
    signedIn: false, loginCount: 0, taskCount: 1, exceptionCount: 0, longTitle: false,
    checkins: [], todos: [{ text: '整理工作流程', done: true }, { text: '记录下一步尝试', done: false }],
  };
  const server = createServer(async (request, response) => {
    const json = (data, status = 200) => {
      response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ETag: '"fixture-v1"' });
      response.end(JSON.stringify(data));
    };
    try {
      const url = new URL(request.url, 'http://127.0.0.1');
      if (url.pathname === '/api/v1/auth/login' && request.method === 'POST') {
        const credentials = await readJson(request);
        if (credentials.username !== fixtureCredentials.username || credentials.password !== fixtureCredentials.password) {
          return json({ code: 'invalid_credentials', message: 'Fixture credentials required' }, 401);
        }
        state.signedIn = true;
        state.loginCount += 1;
        return json(currentUser);
      }
      if (url.pathname.startsWith('/api/') && !state.signedIn) {
        return json({ code: 'not_authenticated', message: 'Please log in' }, 401);
      }
      if (url.pathname === '/api/v1/auth/me') return json(currentUser);
      if (url.pathname === '/api/v1/profiles') return json([{ name: 'demo' }]);
      if (url.pathname.endsWith('/kanban') && request.method === 'GET') {
        return json({ profile: 'demo', total: state.taskCount, sections: [
          { name: 'Doing', tasks: Array.from({ length: state.taskCount }, (_, index) => ({
            id: `kb_${index + 1}`, done: false, todos: index ? [] : state.todos,
            title: index ? `记录下一项任务 ${index + 1}` : state.longTitle
              ? '探索一种新的 AI native 工作方式，并将跨项目经验整理成可复用的方法'
              : '探索 ai native 的工作方式',
          })) }, { name: 'Queue', tasks: [] },
        ] });
      }
      if (url.pathname.includes('/projects-board') && request.method === 'GET') {
        return json({ profile: 'demo', today, north_star: '', habits: [
          { id: 'reading', title: '阅读', kind: 'reading', streak: 3,
            week: [{ date: today, done: state.checkins.some((item) => item.habit === 'reading') }] },
          { id: 'exercise', title: '日课', kind: 'exercise', streak: 1,
            week: [{ date: today, done: state.checkins.some((item) => item.habit === 'exercise') }] },
        ] });
      }
      if (url.pathname.includes('/habit-plans') && request.method === 'GET') {
        return json({ plans: ['一', '二'].map((suffix, index) => ({
          id: `p${index + 1}`, title: `日课计划${suffix}`, habit_id: 'exercise', status: 'active',
          start_date: today, end_date: today,
        })) });
      }
      if (url.pathname.includes('/ai-exceptions') && request.method === 'GET') {
        return json({ profile: 'demo', total: state.exceptionCount, items: state.exceptionCount ? [{
          id: 'run:fixture', source: 'AI 调用', title: '演示异常', message: '这是隔离测试的异常提示。',
          action: 'demo', created: '2026-11-15T08:00:00Z', source_ref: 'fixture', retryable: false,
          href: '/p/demo/projects', severity: 'error',
        }] : [] });
      }
      if (url.pathname.endsWith('/checkins') && request.method === 'POST') {
        state.checkins.push(await readJson(request));
        return json({ ok: true }, 201);
      }
      if (url.pathname.endsWith('/done') && request.method === 'POST') {
        state.taskCount = Math.max(0, state.taskCount - 1);
        return json({ ok: true });
      }
      if (url.pathname.endsWith('/kanban/cards/kb_1') && request.method === 'PATCH') {
        state.todos = (await readJson(request)).todos;
        return json({ ok: true });
      }
      if (url.pathname.startsWith('/api/')) {
        return json({ code: 'not_found', message: 'Fixture endpoint not implemented' }, 404);
      }

      let file = path.resolve(staticRoot, `.${decodeURIComponent(url.pathname)}`);
      if (!file.startsWith(`${staticRoot}${path.sep}`)) file = path.join(staticRoot, 'index.html');
      try {
        if (!(await stat(file)).isFile()) file = path.join(staticRoot, 'index.html');
      } catch {
        file = path.join(staticRoot, 'index.html');
      }
      const body = await readFile(file);
      response.writeHead(200, {
        'Content-Type': contentTypes[path.extname(file)] ?? 'application/octet-stream',
        'Cache-Control': 'no-store',
      });
      response.end(body);
    } catch {
      if (!response.headersSent) response.writeHead(500);
      response.end('Disposable SPA fixture unavailable');
    }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });
  return {
    server, state, origin: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve) => {
      server.close(resolve);
      server.closeAllConnections();
    }),
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const fixture = await startMiniFixture(Number(process.argv[2] ?? 0));
  console.log(fixture.origin);
  for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => void fixture.close());
}
