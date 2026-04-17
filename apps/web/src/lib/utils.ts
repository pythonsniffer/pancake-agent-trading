import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercentage(value: number, decimals = 2): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatNumber(value: number, decimals = 0): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(decimals)}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(decimals)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(decimals)}K`;
  }
  return value.toFixed(decimals);
}

export function formatAddress(address: string, start = 6, end = 4): string {
  if (!address) return '';
  return `${address.slice(0, start)}...${address.slice(-end)}`;
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'running':
    case 'success':
    case 'active':
      return 'text-crypto-green';
    case 'paused':
    case 'pending':
      return 'text-pancake-400';
    case 'error':
    case 'failed':
    case 'stopped':
      return 'text-crypto-red';
    default:
      return 'text-muted-foreground';
  }
}

export function getStatusBg(status: string): string {
  switch (status.toLowerCase()) {
    case 'running':
    case 'success':
    case 'active':
      return 'bg-crypto-green/10';
    case 'paused':
    case 'pending':
      return 'bg-pancake-400/10';
    case 'error':
    case 'failed':
    case 'stopped':
      return 'bg-crypto-red/10';
    default:
      return 'bg-muted/50';
  }
}
