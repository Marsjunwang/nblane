import { Box, Button, Group, Image, Modal, SegmentedControl, Text, UnstyledButton } from '@mantine/core';
import { useRef, useState } from 'react';

/** Whole-image thumbnails open a shared full-screen, zoomable viewer. */
export function ImagePreview({ src, alt, before, width, height = 180 }: { src: string; alt: string; before?: string; width?: number; height?: number }) {
  const [opened, setOpened] = useState(false);
  const [side, setSide] = useState('after');
  const [zoom, setZoom] = useState(0);
  const viewport = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null);
  const shown = side === 'before' && before ? before : src;
  return <>
    <UnstyledButton onClick={() => setOpened(true)} aria-label={`放大查看${alt}`} style={{ width: width ?? '100%', flexShrink: 0 }}>
      <Image src={src} alt={alt} w={width ?? '100%'} h={height} fit="contain" radius="sm" />
    </UnstyledButton>
    <Modal opened={opened} onClose={() => setOpened(false)} title={alt} fullScreen>
      <Group mb="sm" gap="xs">
        {before && <SegmentedControl aria-label="图片对比" value={side} onChange={setSide} data={[{ value: 'before', label: '原图' }, { value: 'after', label: '修改后' }]} />}
        <Button mih={44} variant="default" onClick={() => setZoom(0)}>适应窗口</Button>
        <Button mih={44} variant="default" onClick={() => setZoom(1)}>100%</Button>
        <Button mih={44} aria-label="缩小图片" variant="default" onClick={() => setZoom((value) => Math.max(0.25, (value || 1) / 1.5))}>−</Button>
        <Button mih={44} aria-label="放大图片" variant="default" onClick={() => setZoom((value) => Math.min(8, (value || 1) * 1.5))}>＋</Button>
        <Text size="xs" c="dimmed">{zoom ? `${Math.round(zoom * 100)}% · 拖动或滚动查看` : '完整显示图片；可放大查看文字'}</Text>
      </Group>
      <Box ref={viewport} style={{ height: 'calc(100dvh - 150px)', overflow: 'auto', cursor: zoom ? 'grab' : 'default', touchAction: 'pan-x pan-y' }}
        onPointerDown={(event) => {
          if (!zoom || event.pointerType !== 'mouse' || !viewport.current) return;
          drag.current = { x: event.clientX, y: event.clientY, left: viewport.current.scrollLeft, top: viewport.current.scrollTop };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!drag.current || !viewport.current) return;
          viewport.current.scrollLeft = drag.current.left - event.clientX + drag.current.x;
          viewport.current.scrollTop = drag.current.top - event.clientY + drag.current.y;
        }} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}>
        <ZoomImage src={shown} alt={alt} zoom={zoom} />
      </Box>
    </Modal>
  </>;
}
function ZoomImage({ src, alt, zoom }: { src: string; alt: string; zoom: number }) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  return <img src={src} alt={alt} draggable={false} onLoad={(event) => setSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })}
    style={zoom ? { width: size.width ? size.width * zoom : undefined, height: size.height ? size.height * zoom : undefined, maxWidth: 'none', display: 'block' }
      : { width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />;
}
