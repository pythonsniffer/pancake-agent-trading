'use client';

import { useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { CustomLineChart } from '@/components/charts/line-chart';
import { Button } from '@/components/ui/button';
import { FlaskConical, Play, Calendar, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

export default function BacktestPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [hasResults, setHasResults] = useState(true);

  const backtestResults = [
    { date: 'Day 1', value: 10000 },
    { date: 'Day 5', value: 10120 },
    { date: 'Day 10', value: 10350 },
    { date: 'Day 15', value: 10180 },
    { date: 'Day 20', value: 10580 },
    { date: 'Day 25', value: 10720 },
    { date: 'Day 30', value: 10950 },
  ];

  const strategies = [
    { name: 'Arbitrage', pnl: 520, trades: 89, winRate: 72.5, sharpe: 2.1 },
    { name: 'Trend Following', pnl: 280, trades: 45, winRate: 55.6, sharpe: 1.4 },
    { name: 'Mean Reversion', pnl: 150, trades: 62, winRate: 64.5, sharpe: 1.8 },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Backtesting</h1>
              <p className="text-muted-foreground">Simulate strategies against historical data</p>
            </div>
            <Button
              onClick={() => { setIsRunning(true); setTimeout(() => setIsRunning(false), 2000); }}
              className="gap-2"
              disabled={isRunning}
            >
              {isRunning ? (
                <FlaskConical className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {isRunning ? 'Running...' : 'Run Backtest'}
            </Button>
          </div>

          {/* Config */}
          <div className="glass-card p-5 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Strategy</label>
                <select className="input-field w-full text-sm">
                  <option>All Strategies</option>
                  <option>Arbitrage</option>
                  <option>Trend Following</option>
                  <option>Mean Reversion</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Time Period</label>
                <select className="input-field w-full text-sm">
                  <option>Last 30 Days</option>
                  <option>Last 90 Days</option>
                  <option>Last 6 Months</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Initial Capital</label>
                <input type="number" defaultValue={10000} className="input-field w-full text-sm" />
              </div>
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Max Position ($)</label>
                <input type="number" defaultValue={500} className="input-field w-full text-sm" />
              </div>
            </div>
          </div>

          {hasResults && (
            <>
              {/* Results Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                {[
                  { label: 'Final Value', value: '$10,950', icon: TrendingUp, color: 'text-crypto-green' },
                  { label: 'Total Return', value: '+9.5%', icon: TrendingUp, color: 'text-crypto-green' },
                  { label: 'Max Drawdown', value: '-3.2%', icon: TrendingDown, color: 'text-crypto-red' },
                  { label: 'Total Trades', value: '196', icon: BarChart3, color: 'text-white' },
                ].map((stat) => (
                  <div key={stat.label} className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <stat.icon className={`w-4 h-4 ${stat.color}`} />
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                    </div>
                    <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* Equity Curve */}
              <div className="glass-card p-5 mb-6">
                <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
                <CustomLineChart data={backtestResults} dataKey="value" xKey="date" color="#22c55e" height={300} />
              </div>

              {/* Strategy Breakdown */}
              <div className="glass-card p-5">
                <h3 className="text-lg font-semibold text-white mb-4">Strategy Breakdown</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {strategies.map((s) => (
                    <div key={s.name} className="p-4 bg-white/5 rounded-lg">
                      <h4 className="font-semibold text-white mb-3">{s.name}</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">P&L</span>
                          <span className="text-crypto-green font-medium">+${s.pnl}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Trades</span>
                          <span className="text-white">{s.trades}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Win Rate</span>
                          <span className="text-white">{s.winRate}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Sharpe</span>
                          <span className="text-white">{s.sharpe}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
