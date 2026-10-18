import { test, expect } from '@playwright/test';
test.beforeEach(async ({page}) => {
  await page.route('**/api/v1/profiles/test/content/images/size?*', route => {
    const params = new URL(route.request().url()).searchParams;
    const high = params.get('quality') === 'high';
    const square = params.get('aspect') === '1:1';
    return route.fulfill({json:{width: square ? (high ? 2048 : 1024) : (high ? 2730 : 1365), height: square ? (high ? 2048 : 1024) : (high ? 1536 : 768), supports_4k: !params.get('reference')}});
  });
  await page.route('**/api/v1/profiles/test/content/media-file/**', route => route.fulfill({contentType:'image/svg+xml', body:'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360" fill="gray"/><text x="30" y="80">Reference image</text></svg>'}));
  await page.route('**/api/v1/profiles/test/content/images?*', route => route.fulfill({ json: {runs: []} }));
  await page.goto('/tests/image-editor.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.bn-editor')).toContainText('第一段需要润色');
});
test('mixed selection changes text only, preserves image props and supports one-step undo', async ({page}) => {
  const before = await page.evaluate(() => (window as any).harness.doc());
  await page.evaluate(() => (window as any).harness.select('mixed'));
  await page.locator('.nb-ai-toolbar-button').click();
  await expect(page.getByRole('menuitem', {name:'仅改写文字，保留图片'})).toBeVisible();
  await page.getByRole('menuitem',{name:'润色',exact:true}).click();
  await expect.poll(() => page.evaluate(() => (window as any).harness.request?.parts?.length)).toBe(2);
  expect(await page.evaluate(() => (window as any).harness.request.parts[0])).toContain('**第一段');
  await page.getByRole('button',{name:'接受测试候选'}).click();
  await expect(page.locator('.bn-editor')).toContainText('第1段已经润色');
  await expect(page.locator('.bn-editor')).toContainText('第2段已经润色');
  const after = await page.evaluate(() => (window as any).harness.doc());
  expect(after.content[0].content[1]).toEqual(before.content[0].content[1]);
  await page.locator('.bn-editor').click();
  await page.keyboard.press('Control+z');
  await expect(page.locator('.bn-editor')).toContainText('第一段需要润色');
  await expect(page.locator('.bn-editor')).toContainText('第二段也要润色');
});
test('image-only selection opens image action, never text rewrite', async ({page}) => {
  await page.evaluate(() => (window as any).harness.select('image'));
  await page.locator('.nb-ai-toolbar-button').click();
  await expect(page.getByRole('menuitem',{name:'润色',exact:true})).toHaveCount(0);
  await page.getByRole('menuitem',{name:'修改图片',exact:true}).click();
  await expect(page.getByTestId('image-choice')).toHaveText('1');
});
test('mobile reference preview opens at full size and zooms', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button',{name:'打开图片工作台'}).click();
  await page.getByRole('button',{name:'放大查看参考图'}).click();
  await page.getByRole('button',{name:'100%',exact:true}).click();
  await expect.poll(() => page.locator('[role="dialog"]').last().getByRole('img', {name:'参考图',exact:true}).evaluate((image: HTMLImageElement) => image.naturalWidth)).toBe(640);
  await expect(page.getByText('100% · 拖动或滚动查看')).toBeVisible();
  await page.getByRole('button',{name:'放大图片',exact:true}).click();
  await expect(page.getByText('150% · 拖动或滚动查看')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('text-only candidate replaces the captured passage', async ({page}) => {
  await page.evaluate(() => (window as any).harness.select('text'));
  await page.locator('.nb-ai-toolbar-button').click();
  await page.getByRole('menuitem', {name:'润色',exact:true}).click();
  await page.getByRole('button',{name:'接受测试候选'}).click();
  await expect(page.locator('.bn-editor')).toContainText('润色完成。');
  await expect(page.locator('.bn-editor')).toContainText('第二段也要润色。');
});

test('restores candidates after reload, refuses changed targets, and saves to media', async ({page}) => {
  const candidatePath = 'blog/.candidates/post/run/edited.png';
  const run = {id:'image-test',slug:'post',status:'done',created_at:1,error:'',reference:'media/blog/test/original.png', request:{mode:'edit',instruction:'保留文字调整背景',reference:'media/blog/test/original.png',target:{kind:'block',block_id:'picture',source:'media/blog/test/original.png'}},candidates:[{candidate_path:candidatePath,filename:'edited.png',applied_path:''}]};
  await page.route('**/api/v1/profiles/test/content/images?*', route => route.fulfill({json:{runs:[run]}}));
  let accepts = 0;
  await page.route('**/api/v1/profiles/test/content/images/accept', route => { accepts++; return route.fulfill({json:{path:'media/blog/test/edited.png'}}); });
  await page.reload({waitUntil:'domcontentloaded'});
  await expect(page.locator('.bn-editor')).toBeVisible();
  await page.evaluate(() => (window as any).harness.setConflict(true));
  await page.getByRole('button',{name:'打开图片工作台'}).click();
  await expect(page.getByTestId('image-run')).toContainText('保留文字调整背景');
  expect(accepts).toBe(0);
  await page.getByRole('button',{name:'替换这张图',exact:true}).click();
  await expect(page.getByText('原图已改变、被删除或当前处于 MD 模式。候选已保留，可保存为新媒体后再插入。')).toBeVisible();
  expect(accepts).toBe(0);
  await page.getByRole('button',{name:'保存为新媒体',exact:true}).click();
  await expect(page.getByText('已保存为新媒体图片。')).toBeVisible();
  expect(accepts).toBe(1);
  expect(await page.evaluate(() => (window as any).harness.applied)).toEqual({target:{kind:'media'},path:'media/blog/test/edited.png'});
});

test('text-only selection rewrites text and rejects stale captures', async ({page}) => {
  await page.evaluate(() => (window as any).harness.select('text'));
  await page.locator('.nb-ai-toolbar-button').click();
  await page.getByRole('menuitem', {name:'润色',exact:true}).click();
  await expect.poll(() => page.evaluate(() => (window as any).harness.request?.selection)).toContain('第一段');
  await page.evaluate(() => (window as any).harness.changeCaption());
  expect(await page.evaluate(() => (window as any).harness.ref.current.replaceCapturedSelection('不应覆盖'))).toBe(false);
  await expect(page.locator('.bn-editor')).toContainText('第一段需要润色');
});
test('image replacement preserves metadata, supports iteration and refuses later manual changes', async ({page}) => {
  await page.evaluate(() => (window as any).harness.select('image'));
  await page.locator('.nb-ai-toolbar-button').click();
  await page.getByRole('menuitem',{name:'修改图片',exact:true}).click();
  const result = await page.evaluate(() => {
    const h = (window as any).harness;
    const image = h.image[0];
    const target = {kind:'block', block_id:image.id, source:image.source, fingerprint:image.fingerprint};
    const path = 'media/blog/test/edited.png';
    const applied = h.ref.current.replaceImage(target, path);
    return {applied, target, updated:h.ref.current.retargetImage(target,path)};
  });
  expect(result.applied).toBe(true);
  expect(result.updated.source).toBe('media/blog/test/edited.png');
  expect(JSON.parse(result.updated.fingerprint).caption).toBe('原始图注');
  await page.evaluate(() => (window as any).harness.changeCaption());
  expect(await page.evaluate(target => (window as any).harness.ref.current.replaceImage(target,'media/new.png'), result.updated)).toBe(false);
});

test('resolution and aspect preview match submitted image settings on mobile', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  let submitted: any;
  await page.route('**/api/v1/profiles/test/jobs', async route => {
    submitted = route.request().postDataJSON();
    await route.fulfill({json:{id:'job-image'}});
  });
  await page.getByRole('button',{name:'打开图片工作台'}).click();
  await expect(page.getByText('输出尺寸：1365 × 768 像素', {exact:false})).toBeVisible();
  await page.getByRole('textbox',{name:'清晰度',exact:true}).click();
  await expect(page.getByRole('option',{name:/超清/})).toHaveCount(0);
  await page.getByRole('option',{name:'高清 · 约 400 万像素'}).click();
  await expect(page.getByText('输出尺寸：2730 × 1536 像素', {exact:false})).toBeVisible();
  await page.getByRole('textbox',{name:'输出比例',exact:true}).click();
  await page.getByRole('option',{name:'1:1',exact:true}).click();
  await expect(page.getByText('输出尺寸：2048 × 2048 像素', {exact:false})).toBeVisible();
  await page.getByRole('textbox',{name:'修改要求',exact:true}).fill('保留文字，调整背景');
  await page.getByRole('button',{name:'生成修改图',exact:true}).click();
  await expect.poll(() => submitted?.input?.quality).toBe('high');
  expect(submitted.input.aspect).toBe('1:1');
  expect(submitted.input.reference).toBe('media/blog/test/original.png');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
