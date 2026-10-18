import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MantineProvider, Button, Stack } from '@mantine/core';
import '@mantine/core/styles.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NodeSelection, TextSelection } from '@tiptap/pm/state';
import { BlockNoteBlogEditor, type BlockNoteBlogEditorHandle } from '../src/components/BlockNoteBlogEditor';
import { ImageWorkspace } from '../src/components/content/ImageWorkspace';

function getView() {
 return (document.querySelector('.bn-editor') as any).editor.view;
}
const blocks = [
  { id: 'first', type: 'paragraph', content: [{ type: 'text', text: '第一段需要润色。', styles: { bold: true } }] },
  { id: 'picture', type: 'visual_block', props: { asset_type: 'image', src: 'media/blog/test/original.png', caption: '原始图注', prompt: '保留提示词' } },
  { id: 'last', type: 'paragraph', content: [{ type: 'text', text: '第二段也要润色。', styles: {} }] },
];
const imageRequest = { mode: 'edit', reference: 'media/blog/test/original.png', target: { kind: 'media' } } as const;
function Harness() {
  const ref = useRef<BlockNoteBlogEditorHandle>(null);
  const [request, setRequest] = useState<any>(null);
  const [image, setImage] = useState<any>(null);
  const [opened, setOpened] = useState(false);
  const [changes, setChanges] = useState<any>(null);
  const [conflict, setConflict] = useState(false);
  const [applied, setApplied] = useState<any>(null);
  const state = window as any;
  state.harness = { request, image, changes, ref, applied, setConflict, select: (kind: string) => {
    const view = getView();
    let position = 0;
    let textRange = { from: 3, to: 4 };
    let found = false;
    view.state.doc.descendants((node: any, pos: number) => { if (node.type.name === 'visual_block') position = pos; if (!found && node.type.name === 'paragraph') { textRange = { from: pos + 1, to: pos + node.nodeSize - 1 }; found = true; } });
    const selection = kind === 'image' ? NodeSelection.create(view.state.doc, position) : TextSelection.create(view.state.doc, kind === 'text' ? textRange.from : 3, kind === 'text' ? textRange.to : view.state.doc.content.size - 3);
    view.focus(); view.dispatch(view.state.tr.setSelection(selection));
  }, changeCaption: () => {
    const view = getView();
    const tr = view.state.tr;
    view.state.doc.descendants((node: any, pos: number) => { if (node.type.name === 'visual_block') tr.setNodeMarkup(pos, undefined, { ...node.attrs, caption: '已手动修改图注' }); });
    view.dispatch(tr);
  }, doc: () => getView().state.doc.toJSON() };
  return <Stack p="md">
    <Button onClick={() => ref.current?.replaceCapturedSelection('润色完成。', request?.parts?.map((_: string, i: number) => `第${i + 1}段已经润色。`))}>接受测试候选</Button>
    <Button onClick={() => setOpened(true)}>打开图片工作台</Button>
    <BlockNoteBlogEditor ref={ref} markdown="" blocksJson={blocks} sourceMode={false} resolveMediaUrl={() => 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360" fill="gray"/></svg>'} uploadMedia={async () => ''} onChange={setChanges} onAIRewrite={setRequest} onAIImage={setImage} />
    <output data-testid="image-choice">{image?.length ?? 0}</output>
    <ImageWorkspace profile="test" slug="post" opened={opened} request={imageRequest} enabled media={[]} draft={{title:'测试',summary:'',tags:[],body:''}} onClose={() => setOpened(false)} canApply={(target) => target.kind === 'media' || !conflict} onApply={(target, path) => { setApplied({target, path}); return true; }} />
  </Stack>;
}
createRoot(document.getElementById('root')!).render(<MantineProvider forceColorScheme="dark"><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Harness /></QueryClientProvider></MantineProvider>);
