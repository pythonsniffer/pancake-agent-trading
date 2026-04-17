'use client';

import { Bell, Search, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/utils';

interface HeaderProps {
  portfolioValue?: number;
  dailyChange?: number;
}

export function Header({ portfolioValue = 12450.80, dailyChange = 3.2 }: HeaderProps) {
  const isPositive = dailyChange >= 0;

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search pools, tokens, agents..."
            className="input-field w-80 pl-10 text-sm"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Portfolio Quick View */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Portfolio Value</p>
            <p className="text-lg font-bold text-white">{formatCurrency(portfolioValue)}</p>
          </div>
          <div className={`px-2 py-1 rounded text-xs font-medium ${
            isPositive ? 'bg-crypto-green/10 text-crypto-green' : 'bg-crypto-red/10 text-crypto-red'
          }`}>
            {isPositive ? '+' : ''}{dailyChange}%
          </div>
        </div>

        <div className="h-8 w-px bg-border" />

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-pancake-500" />
        </Button>

        {/* Wallet Connect */}
        <Button variant="outline" className="gap-2">
          <Wallet className="w-4 h-4" />
          Connect Wallet
        </Button>
      </div>
    </header>
  );
}
