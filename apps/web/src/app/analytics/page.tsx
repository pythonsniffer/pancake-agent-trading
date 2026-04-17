'use client';

import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { CustomLineChart } from '@/components/charts/line-chart';
import { CustomBarChart } from '@/components/charts/bar-chart';
import { formatCurrency } from '@/lib/utils';
import { BarChart3, TrendingUp, Activity, Target } from 'lucide-react';

export default function AnalyticsPage() {
  const pnlHistory = [
    { date: 'Week 1', value: 150 },
    { date: 'Week 2', value: 320 },
    { date: 'Week 3', value: 280 },
    { date: 'Week 4', value: 510 },
    { date: 'Week 5', value: 690 },
    { date: 'Week 6', value: 850 },
    { date: 'Week 7', value: 1200 },
    { date: 'Week 8', value: 1450 },
  ];

  const strategyPerformance = [
    { name: 'Arbitrage', value: 680 },
    { name: 'Trend', value: 420 },
    { name: 'Mean Rev', value: 210 },
    { name: 'LP Yield', value: 140 },
  ];

  const chainVolume = [
    { name: 'BSC', value: 85 },
    { name: 'ETH', value: 10 },
    { name: 'ARB', value: 5 },
  ];

  const hourlyActivity = Array.from({ length: 24 }, (_, i) => ({
    name: `${i}:00`,
    value: Math.floor(Math.random() * 15) + 2,
  }));

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Analytics</h1>
            <p className="text-muted-foreground">Deep dive into trading performance and system metrics</p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Cumulative P&L', value: '$1,450.20', icon: TrendingUp, color: 'text-crypto-green', bg: 'bg-crypto-green/10' },
              { label: 'Avg Daily Volume', value: '$2,340', icon: BarChart3, color: 'text-crypto-blue', bg: 'bg-crypto-blue/10' },
              { label: 'Best Strategy', value: 'Arbitrage', icon: Target, color: 'text-pancake-400', bg: 'bg-pancake-500/10' },
              { label: 'Uptime', value: '99.2%', icon: Activity, color: 'text-crypto-green', bg: 'bg-crypto-green/10' },
            ].map((card) => (
              <div key={card.label} className="glass-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-2 rounded-lg ${card.bg}`}>
                    <card.icon className={`w-4 h-4 ${card.color}`} />
                  </div>
                  <p className="text-sm text-muted-foreground">{card.label}</p>
                </div>
                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
              </div>
            ))}
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Cumulative P&L</h3>
              <CustomLineChart data={pnlHistory} dataKey="value" xKey="date" color="#22c55e" height={280} />
            </div>
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Strategy Performance ($)</h3>
              <CustomBarChart data={strategyPerformance} dataKey="value" xKey="name" height={280} />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Hourly Trade Activity</h3>
              <CustomBarChart data={hourlyActivity} dataKey="value" xKey="name" colors={['#f59e0b']} height={220} />
            </div>
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Chain Distribution</h3>
              <div className="space-y-4 mt-6">
                {chainVolume.map((item) => (
                  <div key={item.name}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-white">{item.name}</span>
                      <span className="text-sm text-muted-foreground">{item.value}%</span>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-3">
                      <div
                        className="h-3 rounded-full bg-gradient-to-r from-pancake-500 to-pancake-400"
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 bg-white/5 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Primary Chain</p>
                <p className="text-lg font-bold text-white">BNB Smart Chain</p>
                <p className="text-xs text-muted-foreground">85% of all trading volume</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
