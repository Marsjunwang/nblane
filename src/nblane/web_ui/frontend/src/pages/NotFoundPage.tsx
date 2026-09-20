import { Anchor, Center, Stack, Text, Title } from '@mantine/core';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <Center h="100vh">
      <Stack align="center" gap="xs">
        <Title order={1}>404</Title>
        <Text c="dimmed">页面不存在</Text>
        <Anchor component={Link} to="/">
          返回首页
        </Anchor>
      </Stack>
    </Center>
  );
}
