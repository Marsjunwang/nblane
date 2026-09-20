import {
  Alert,
  Badge,
  Card,
  Center,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { useHealthReport } from '../api/hooks';
import type { HealthIssue } from '../api/types';

const SEVERITY_COLORS: Record<string, string> = {
  error: 'red',
  warning: 'yellow',
  info: 'blue',
};

function severityColor(severity: string): string {
  return SEVERITY_COLORS[severity] ?? 'gray';
}

export function HealthPage() {
  const { name = '' } = useParams();
  const report = useHealthReport(name);

  const issuesByCategory = useMemo(() => {
    const grouped = new Map<string, HealthIssue[]>();
    for (const issue of report.data?.issues ?? []) {
      const bucket = grouped.get(issue.category) ?? [];
      bucket.push(issue);
      grouped.set(issue.category, bucket);
    }
    return grouped;
  }, [report.data]);

  if (report.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (report.isError) {
    return (
      <Alert color="red" title="加载失败">
        {report.error.message}
      </Alert>
    );
  }

  const data = report.data;
  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>{data.profile} · 健康检查</Title>
        <Group gap="xs">
          {Object.entries(data.summary_counts ?? {}).map(([severity, count]) => (
            <Badge key={severity} color={severityColor(severity)} variant="light">
              {severity}: {count}
            </Badge>
          ))}
        </Group>
      </Group>
      {!data.can_publish_context && (
        <Alert color="yellow" title="上下文暂不可发布">
          存在需要处理的问题,修复后才能发布上下文。
        </Alert>
      )}
      {(data.issues ?? []).length === 0 ? (
        <Text c="dimmed">没有发现问题,档案状态良好。</Text>
      ) : (
        [...issuesByCategory.entries()].map(([category, issues]) => (
          <Card key={category} withBorder radius="md" padding="lg">
            <Title order={4} mb="sm">
              {category}
            </Title>
            <Stack gap="sm">
              {issues.map((issue, index) => (
                <Group key={`${issue.title}-${index}`} align="flex-start" wrap="nowrap">
                  <Badge color={severityColor(issue.severity)} mt={2}>
                    {issue.severity}
                  </Badge>
                  <div>
                    <Text fw={500}>{issue.title}</Text>
                    {issue.detail && (
                      <Text size="sm" c="dimmed">
                        {issue.detail}
                      </Text>
                    )}
                    {issue.action && <Text size="sm">建议:{issue.action}</Text>}
                  </div>
                </Group>
              ))}
            </Stack>
          </Card>
        ))
      )}
    </Stack>
  );
}
