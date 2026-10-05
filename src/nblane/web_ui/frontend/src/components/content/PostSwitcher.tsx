import { Badge, Group, Modal, ScrollArea, Text, TextInput, UnstyledButton } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import type { StudioPost } from '../../api/types';
import { STATUS_COLORS, STATUS_LABELS } from './contentDraft';

/**
 * ⌘K quick switcher: fuzzy-filter posts and jump between them without going
 * back to the library. Keyboard-first (arrows + enter).
 */
export function PostSwitcher({
  opened,
  posts,
  currentSlug,
  onClose,
  onPick,
}: {
  opened: boolean;
  posts: StudioPost[];
  currentSlug: string;
  onClose: () => void;
  onPick: (slug: string) => void;
}) {
  const [query, setQuery] = useState('');
  const [index, setIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = posts.filter(
      (post) => !needle || `${post.title} ${post.slug} ${(post.tags ?? []).join(' ')}`.toLowerCase().includes(needle),
    );
    return rows.slice(0, 50);
  }, [posts, query]);

  useEffect(() => {
    if (opened) {
      setQuery('');
      setIndex(0);
    }
  }, [opened]);

  useEffect(() => {
    setIndex((value) => Math.min(value, Math.max(matches.length - 1, 0)));
  }, [matches.length]);

  useEffect(() => {
    listRef.current
      ?.querySelector(`[data-index="${index}"]`)
      ?.scrollIntoView({ block: 'nearest' });
  }, [index]);

  const choose = (slug: string) => {
    onClose();
    if (slug !== currentSlug) onPick(slug);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      size="lg"
      padding={0}
      yOffset="12vh"
    >
      <div data-testid="content-switcher">
      <TextInput
        placeholder="跳转到文章…"
        aria-label="跳转到文章"
        leftSection={<IconSearch size={16} />}
        variant="unstyled"
        size="md"
        px="md"
        data-autofocus
        value={query}
        onChange={(event) => setQuery(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            setIndex((value) => Math.min(value + 1, matches.length - 1));
          } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            setIndex((value) => Math.max(value - 1, 0));
          } else if (event.key === 'Enter') {
            event.preventDefault();
            const picked = matches[index];
            if (picked) choose(picked.slug);
          }
        }}
        styles={{ input: { borderBottom: '1px solid var(--mantine-color-dark-5)', height: 52 } }}
      />
      <ScrollArea.Autosize mah="50vh" ref={listRef}>
        {matches.length ? (
          matches.map((post, i) => (
            <UnstyledButton
              key={post.slug}
              data-index={i}
              data-testid="content-switcher-item"
              onClick={() => choose(post.slug)}
              onMouseEnter={() => setIndex(i)}
              style={{
                display: 'block',
                width: '100%',
                padding: '10px 16px',
                background: i === index ? 'var(--mantine-color-dark-5)' : undefined,
              }}
            >
              <Group justify="space-between" wrap="nowrap">
                <Text size="sm" lineClamp={1} fw={post.slug === currentSlug ? 600 : 400}>
                  {post.title || post.slug}
                </Text>
                <Badge size="xs" variant="light" color={STATUS_COLORS[post.status] ?? 'gray'}>
                  {STATUS_LABELS[post.status] ?? post.status}
                </Badge>
              </Group>
            </UnstyledButton>
          ))
        ) : (
          <Text size="sm" c="dimmed" p="md" ta="center">
            没有匹配的文章。
          </Text>
        )}
      </ScrollArea.Autosize>
      </div>
    </Modal>
  );
}
