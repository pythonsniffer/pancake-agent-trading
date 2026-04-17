'use client';

import { useQuery } from '@tanstack/react-query';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { CustomLineChart } from '@/components/charts/line-chart';
import { portfolioApi } from '@/lib/api';
import { formatCurrency, formatPercentage } from '@/lib/utils';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

export default function PortfolioPage() {
  const { data: portfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => portfolioApi.getCurrent().then((res) => res.data),
    refetchInterval: 30000,
  });

  const { data: history } = useQuery({
    queryKey: ['portfolioHistory'],
    queryFn: () => portfolioApi.getHistory(30).then((res) => res.data),
    refetchInterval: 60000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['portfolioMetrics'],
    queryFn: () => portfolioApi.getMetrics().then((res) => res.data),
  });

  const portfolioHistory = history?.history?.map((s: any, i: number) => ({
    date: `Day ${i + 1}`,
    value: s.total_value_usd,
  })) || [
    { date: 'Mon', value: 10200 },
    { date: 'Tue', value: 10450 },
    { date: 'Wed', value: 10300 },
    { date: 'Thu', value: 10800 },
    { date: 'Fri', value: 10650 },
    { date: 'Sat', value: 11000 },
    { date: 'Sun', value: 10900 },
  ];

  const tokens = portfolio?.tokens || [
    { symbol: 'BNB', balance: 4.5, value_usd: 3540 },
    { symbol: 'USDT', balance: 2528, value_usd: 2528 },
    { symbol: 'CAKE', balance: 120, value_usd: 1515 },
    { symbol: 'ETH', balance: 0.8, value_usd: 1515 },
    { symbol: 'BTCB', balance: 0.05, value_usd: 1010 },
  ];

  const totalValue = portfolio?.total_value_usd || 10113;
  const colorMap: Record<string, string> = {
    BNB: 'bg-yellow-500',
    USDT: 'bg-green-500',
    CAKE: 'bg-amber-400',
    ETH: 'bg-blue-500',
    BTCB: 'bg-orange-500',
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Portfolio</h1>
            <p className="text-muted-foreground">Track your portfolio performance and asset allocation</p>
          </div>

          {/* Top Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-1">
                <Wallet className="w-4 h-4 text-pancake-400" />
                <p className="text-sm text-muted-foreground">Total Value</p>
              </div>
              <p className="text-2xl font-bold text-white">{formatCurrency(portfolio?.total_value_usd || 10113)}</p>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-1">
                {(portfolio?.total_pnl_usd || 113) >= 0
                  ? <TrendingUp className="w-4 h-4 text-crypto-green" />
                  : <TrendingDown className="w-4 h-4 text-crypto-red" />}
                <p className="text-sm text-muted-foreground">Total P&L</p>
              </div>
              <p className={`text-2xl font-bold ${(portfolio?.total_pnl_usd || 113) >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                {formatCurrency(portfolio?.total_pnl_usd || 113)}
              </p>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-1">
                <PieChart className="w-4 h-4 text-crypto-blue" />
                <p className="text-sm text-muted-foreground">Win Rate</p>
              </div>
              <p className="text-2xl font-bold text-white">{portfolio?.win_rate?.toFixed(1) || '68.5'}%</p>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-1">
                <BarChart3 className="w-4 h-4 text-crypto-purple" />
                <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
              </div>
              <p className="text-2xl font-bold text-white">{portfolio?.sharpe_ratio?.toFixed(2) || '1.85'}</p>
            </div>
          </div>

          {/* Portfolio Chart & Allocation */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Portfolio Value Over Time</h3>
              <CustomLineChart
                data={portfolioHistory}
                dataKey="value"
                xKey="date"
                color="#f59e0b"
                height={300}
              />
            </div>

            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Asset Allocation</h3>
              <div className="space-y-4">
                {tokens.map((token: any) => {
                  const pct = ((token.value_usd / totalValue) * 100).toFixed(1);
                  return (
                    <div key={token.symbol}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${colorMap[token.symbol] || 'bg-slate-500'}`} />
                          <span className="text-sm text-white font-medium">{token.symbol}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{pct}%</span>
                      </div>
                      <div className="w-full bg-white/5 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${colorMap[token.symbol] || 'bg-slate-500'}`}
                          style={{ width: `${pct}%`, opacity: 0.8 }}
                        />
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-xs text-muted-foreground">{token.balance} {token.symbol}</span>
                        <span className="text-xs text-white">{formatCurrency(token.value_usd)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="glass-card p-5">
            <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[
                { label: 'Max Drawdown', value: `${portfolio?.max_drawdown_percent?.toFixed(1) || '4.2'}%`, color: 'text-crypto-red' },
                { label: 'Profit Factor', value: metrics?.current?.profit_factor?.toFixed(2) || '1.91', color: 'text-crypto-green' },
                { label: 'Avg Win', value: formatCurrency(metrics?.current?.avg_profit_usd || 23.5), color: 'text-crypto-green' },
                { label: 'Avg Loss', value: formatCurrency(metrics?.current?.avg_loss_usd || 12.3), color: 'text-crypto-red' },
                { label: 'Total Trades', value: portfolio?.total_trades?.toString() || '156', color: 'text-white' },
                { label: '24h Change', value: formatPercentage(metrics?.change_24h_percent || 3.2), color: (metrics?.change_24h_percent || 3.2) >= 0 ? 'text-crypto-green' : 'text-crypto-red' },
              ].map((m) => (
                <div key={m.label} className="text-center p-3 bg-white/5 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">{m.label}</p>
                  <p className={`text-lg font-bold ${m.color}`}>{m.value}</p>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
