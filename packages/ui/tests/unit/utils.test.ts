/**
 * @jest-environment jsdom
 */

import { cn, getStatusColor, getStatusBgColor } from '@/lib/utils';

describe('cn utility', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
    expect(cn('foo', true && 'bar', 'baz')).toBe('foo bar baz');
  });

  it('should handle undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
  });

  it('should merge tailwind classes correctly', () => {
    expect(cn('px-4', 'px-2')).toBe('px-2');
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500');
  });

  it('should handle empty strings', () => {
    expect(cn('foo', '', 'bar')).toBe('foo bar');
  });

  it('should handle objects with boolean values', () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz');
  });
});

describe('getStatusColor', () => {
  it('should return green for running status', () => {
    expect(getStatusColor('running')).toContain('green');
  });

  it('should return yellow for starting status', () => {
    expect(getStatusColor('starting')).toContain('yellow');
  });

  it('should return yellow for stopping status', () => {
    expect(getStatusColor('stopping')).toContain('yellow');
  });

  it('should return gray for stopped status', () => {
    expect(getStatusColor('stopped')).toContain('gray');
  });

  it('should return red for error status', () => {
    expect(getStatusColor('error')).toContain('red');
  });

  it('should return default for unknown status', () => {
    const result = getStatusColor('unknown' as any);
    expect(typeof result).toBe('string');
  });
});

describe('getStatusBgColor', () => {
  it('should return green background for running status', () => {
    expect(getStatusBgColor('running')).toContain('green');
  });

  it('should return yellow background for starting status', () => {
    expect(getStatusBgColor('starting')).toContain('yellow');
  });

  it('should return red background for error status', () => {
    expect(getStatusBgColor('error')).toContain('red');
  });

  it('should return gray background for stopped status', () => {
    expect(getStatusBgColor('stopped')).toContain('gray');
  });
});
