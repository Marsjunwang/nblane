import { Alert, Button, Card, Center, Group, Loader, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useMe, useProfiles } from '../api/hooks';
import { ProfileCreateDialog } from '../components/ProfileCreateDialog';

export function ProfilesPage() {
  const profiles = useProfiles();
  const me = useMe();
  const [creating, setCreating] = useState(false);
  const canCreate = me.data?.role === 'admin' && !me.data.agent;

  if (profiles.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (profiles.isError) {
    return (
      <Alert color="red" title="加载失败">
        {profiles.error.message}
      </Alert>
    );
  }

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>档案列表</Title>
        {canCreate && profiles.data.length > 0 && <Button onClick={() => setCreating(true)}>创建档案</Button>}
      </Group>
      {profiles.data.length === 0 ? (
        <Stack align="flex-start" gap="sm">
          <Text>从自己的第一个目标开始。</Text>
          <Text c="dimmed">{canCreate ? '选择领域，写下方向和第一件任务，建立你的成长档案。' : '当前账号还没有可访问的档案，请联系管理员创建或分配。'}</Text>
          {canCreate && <Button onClick={() => setCreating(true)}>创建档案</Button>}
        </Stack>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
          {profiles.data.map((p) => (
            <Card
              key={p.name}
              withBorder
              shadow="sm"
              radius="md"
              padding="lg"
              component={Link}
              to={`/p/${encodeURIComponent(p.name)}/home`}
            >
              <Title order={4}>{p.name}</Title>
              <Text size="sm" c="dimmed" mt="xs">
                {p.skill_schema || '未设置 schema'}
              </Text>
              <Text size="sm" mt="xs">
                技能节点:{p.skill_node_count}
              </Text>
              {p.current_goal_title && (
                <Text size="sm" mt="xs" lineClamp={1}>
                  当前目标:{p.current_goal_title}
                </Text>
              )}
            </Card>
          ))}
        </SimpleGrid>
      )}
      {creating && <ProfileCreateDialog onClose={() => setCreating(false)} />}
    </>
  );
}
