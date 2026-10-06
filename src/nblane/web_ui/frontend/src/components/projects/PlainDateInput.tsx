// YYYY-MM-DD date field for the projects page. Native <input type="date">
// renders the browser locale's format (mm/dd/yyyy in en-locale browsers,
// even inside the Chinese UI); Mantine DateInput pins the display to
// valueFormat regardless of browser locale. Same setup as the detail card's
// 排期 row, shared so every date field on the page reads the same.

import { DateInput } from '@mantine/dates';
import type { DateInputProps } from '@mantine/dates';
import 'dayjs/locale/zh-cn';

export function PlainDateInput({
  value,
  onChange,
  ...rest
}: Omit<DateInputProps, 'value' | 'onChange' | 'valueFormat' | 'locale'> & {
  /** 'YYYY-MM-DD' or '' (empty). */
  value: string;
  onChange: (value: string) => void;
  'data-testid'?: string;
}) {
  return (
    <DateInput
      valueFormat="YYYY-MM-DD"
      placeholder="YYYY-MM-DD"
      locale="zh-cn"
      clearable
      {...rest}
      value={value || null}
      onChange={(next) => onChange(next ?? '')}
    />
  );
}
