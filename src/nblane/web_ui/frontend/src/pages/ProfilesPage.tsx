import { Alert, Card, Center, Loader, SimpleGrid, Text, Title } from '@mantine/core';
import { Link } from 'react-router-dom';

import { useProfiles } from '../api/hooks';

export function ProfilesPage() {
  const profiles = useProfiles();

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
      <Title order={2} mb="md">
        档案列表
      </Title>
      {profiles.data.length === 0 ? (
        <Text c="dimmed">还没有档案,先用 `nblane init &lt;name&gt;` 创建一个。</Text>
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
    </>
  );
}
