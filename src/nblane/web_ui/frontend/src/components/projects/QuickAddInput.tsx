// 「＋ 快速添加」— the persistent inline-create row pinned to the top of
// every lane's Queue column (裁决4:创建 ≤1 次点击,零滚动). Click unfolds the
// input; Enter submits; Escape/blur folds back. The full-field form stays in
// the project edit drawer.

import { TextInput } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { boardPalette } from './palette';

export function QuickAddInput({
  laneId,
  pending,
  onSubmit,
}: {
  laneId: string;
  pending: boolean;
  onSubmit: (title: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  const submit = () => {
    const value = title.trim();
    if (!value || pending) {
      return;
    }
    onSubmit(value);
    setTitle('');
    // Keep the input open for rapid consecutive adds.
    inputRef.current?.focus();
  };

  if (!open) {
    return (
      <button
        type="button"
        data-testid={`quick-add-${laneId}`}
        onClick={() => setOpen(true)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          width: '100%',
          padding: '6px 8px',
          background: 'transparent',
          border: `1px dashed ${boardPalette.border}`,
          borderRadius: 6,
          color: boardPalette.dim,
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        <IconPlus size={13} />
        快速添加
      </button>
    );
  }
  return (
    <TextInput
      ref={inputRef}
      size="xs"
      placeholder="任务标题,回车创建"
      value={title}
      disabled={pending}
      data-testid={`quick-add-input-${laneId}`}
      onChange={(event) => setTitle(event.currentTarget.value)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          submit();
        } else if (event.key === 'Escape') {
          setTitle('');
          setOpen(false);
        }
      }}
      onBlur={() => {
        if (!title.trim()) {
          setOpen(false);
        }
      }}
    />
  );
}
