'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn, formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';

interface MetricsCardProps {
  title: string;
  value: number;
  change?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricsCard({
  title,
  value,
  change,
  prefix = '$',
  suffix = '',
  decimals = 2,
  icon,
  className,
}: MetricsCardProps) {
  const isPositive = change ? change >= 0 : true;
  const Icon = isPositive ? TrendingUp : TrendingDown;

  return (
    <div className={cn('glass-card p-5 card-hover', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">
            {prefix}{decimals === 0 ? formatNumber(value, 0) : value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}
          </p>
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-white/5">
            {icon}
          </div>
        )}
      </div>

      {change !== undefined && (
        <div className="flex items-center gap-1 mt-3">
          <div
            className={cn(
              'flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
              isPositive ? 'bg-crypto-green/10 text-crypto-green' : 'bg-crypto-red/10 text-crypto-red'
            )}
          >
            <Icon className="w-3 h-3" />
            {isPositive ? '+' : ''}{change}%
          </div>
          <span className="text-xs text-muted-foreground">vs last 24h</span>
        </div>
      )}
    </div>
  );
}
