// 「＋ 快速添加」— title, open state and the optional continuous mode live in
// the lane controller, so a folded lane becoming non-empty cannot lose them.

import { Checkbox, Group, Stack, TextInput } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { IconPlus } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { boardPalette } from './palette';

export interface QuickAddController {
  open: boolean;
  title: string;
  continuous: boolean;
  setOpen: (value: boolean) => void;
  setTitle: (value: string) => void;
  setContinuous: (value: boolean) => void;
}

export interface QuickAddCallbacks {
  onSuccess: () => void;
  onError: (message: string) => void;
}

export interface QuickAddOptions {
  pending: boolean;
  controller: QuickAddController;
  onSubmit: (title: string, callbacks: QuickAddCallbacks) => void;
}

export function useQuickAddController(): QuickAddController {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [continuous, setContinuous] = useLocalStorage({
    key: 'nblane.projects.quickAdd.continuous',
    defaultValue: false,
  });
  return { open, title, continuous, setOpen, setTitle, setContinuous };
}

export function QuickAddInput({
  laneId,
  pending,
  controller,
  onSubmit,
}: QuickAddOptions & { laneId: string }) {
  const { open, title, continuous, setOpen, setTitle, setContinuous } = controller;
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  useEffect(() => {
    if (!open || pending) {
      return;
    }
    const active = document.activeElement;
    if (active === document.body || active === inputRef.current) {
      inputRef.current?.focus();
    }
  }, [open, pending]);

  const submit = () => {
    const value = title.trim();
    if (!value || pending) {
      return;
    }
    setError(null);
    onSubmit(value, {
      onSuccess: () => {
        setTitle('');
        setError(null);
        inputRef.current?.focus();
      },
      onError: (message) => {
        setError(message);
        inputRef.current?.focus();
      },
    });
  };

  if (!open) {
    return (
      <button
        type="button"
        data-testid={`quick-add-${laneId}`}
        className="projects-quick-add"
        onClick={() => setOpen(true)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          width: '100%',
          minHeight: 36,
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
    <Stack gap={4} data-quick-add-root={laneId} data-testid={`quick-add-editor-${laneId}`}>
      <Group gap="xs" wrap="nowrap">
        <TextInput
          ref={inputRef}
          size="sm"
          className="projects-form projects-quick-add-input"
          placeholder="任务标题,回车创建"
          value={title}
          disabled={pending}
          error={error ?? undefined}
          data-testid={`quick-add-input-${laneId}`}
          style={{ flex: 1, minWidth: 0 }}
          onChange={(event) => {
            setTitle(event.currentTarget.value);
            setError(null);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              submit();
            } else if (event.key === 'Escape') {
              setTitle('');
              setError(null);
              setOpen(false);
            }
          }}
          onBlur={(event) => {
            const root = event.currentTarget.closest('[data-quick-add-root]');
            const inside = event.relatedTarget instanceof Node && root?.contains(event.relatedTarget);
            if (!title.trim() && !continuous && !inside) {
              setOpen(false);
            }
          }}
        />
        <Checkbox
          size="sm"
          label="连续"
          aria-label="连续添加"
          checked={continuous}
          disabled={pending}
          className="projects-quick-add-continuous"
          data-testid={`quick-add-continuous-${laneId}`}
          onChange={(event) => setContinuous(event.currentTarget.checked)}
          styles={{ root: { minHeight: 36 }, label: { color: boardPalette.dim, fontSize: 13 } }}
        />
      </Group>
    </Stack>
  );
}
