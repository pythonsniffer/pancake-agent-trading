'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  TrendingUp,
  Activity,
  Users,
  BarChart3,
  Settings,
  ArrowLeftRight,
  FlaskConical,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Agents', href: '/agents', icon: Users },
  { name: 'Trades', href: '/trades', icon: ArrowLeftRight },
  { name: 'Portfolio', href: '/portfolio', icon: TrendingUp },
  { name: 'Pools', href: '/pools', icon: Activity },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Backtest', href: '/backtest', icon: FlaskConical },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 h-screen bg-card border-r border-border">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-pancake-400 to-pancake-600 flex items-center justify-center">
          <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <div>
          <h1 className="font-bold text-white text-sm">PancakeSwap</h1>
          <p className="text-xs text-muted-foreground">AI Trading Agent</p>
        </div>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-pancake-500/10 text-pancake-400'
                  : 'text-muted-foreground hover:text-white hover:bg-white/5'
              )}
            >
              <Icon className={cn('w-5 h-5', isActive && 'text-pancake-400')} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">System Status</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-crypto-green animate-pulse" />
              <span className="text-xs text-crypto-green">Online</span>
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            v1.0.0 • {new Date().toLocaleDateString()}
          </div>
        </div>
      </div>
    </div>
  );
}
