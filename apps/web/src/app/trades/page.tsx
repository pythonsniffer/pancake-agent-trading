'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { Button } from '@/components/ui/button';
import { tradesApi } from '@/lib/api';
import { cn, formatCurrency, formatAddress, formatDate, getStatusColor } from '@/lib/utils';
import { ArrowRightLeft, Filter, Download, ExternalLink } from 'lucide-react';

const statusFilters = ['All', 'SUCCESS', 'FAILED', 'PENDING', 'SIMULATED'];
const strategyFilters = ['All', 'ARBITRAGE', 'TREND_FOLLOWING', 'MEAN_REVERSION', 'LP_YIELD'];

export default function TradesPage() {
  const [statusFilter, setStatusFilter] = useState('All');
  const [strategyFilter, setStrategyFilter] = useState('All');

  const { data: trades, isLoading } = useQuery({
    queryKey: ['trades', statusFilter, strategyFilter],
    queryFn: () =>
      tradesApi.getAll({
        status: statusFilter !== 'All' ? statusFilter : undefined,
        strategy: strategyFilter !== 'All' ? strategyFilter : undefined,
        limit: 50,
      }).then((res) => res.data),
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['tradeStats'],
    queryFn: () => tradesApi.getStats().then((res) => res.data),
    refetchInterval: 30000,
  });

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Header />

        <main className="flex-1 p-6 overflow-auto">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Trade History</h1>
              <p className="text-muted-foreground">View and analyze all trading activity</p>
            </div>
            <Button variant="outline" className="gap-2">
              <Download className="w-4 h-4" />
              Export CSV
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Total Trades</p>
              <p className="text-2xl font-bold text-white">{stats?.total_trades || 156}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-crypto-green">{stats?.win_rate?.toFixed(1) || 68.5}%</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Net Profit</p>
              <p className="text-2xl font-bold text-crypto-green">{formatCurrency(stats?.net_profit_usd || 2450.8)}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Gas Costs</p>
              <p className="text-2xl font-bold text-white">{formatCurrency(stats?.total_gas_usd || 234.5)}</p>
            </div>
          </div>

          {/* Filters */}
          <div className="glass-card p-4 mb-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Filters:</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Status:</span>
                <div className="flex gap-1">
                  {statusFilters.map((status) => (
                    <button
                      key={status}
                      onClick={() => setStatusFilter(status)}
                      className={cn(
                        'px-3 py-1.5 text-xs rounded-lg transition-colors',
                        statusFilter === status
                          ? 'bg-pancake-500/20 text-pancake-400'
                          : 'bg-white/5 text-muted-foreground hover:bg-white/10'
                      )}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Strategy:</span>
                <div className="flex gap-1">
                  {strategyFilters.map((strategy) => (
                    <button
                      key={strategy}
                      onClick={() => setStrategyFilter(strategy)}
                      className={cn(
                        'px-3 py-1.5 text-xs rounded-lg transition-colors',
                        strategyFilter === strategy
                          ? 'bg-pancake-500/20 text-pancake-400'
                          : 'bg-white/5 text-muted-foreground hover:bg-white/10'
                      )}
                    >
                      {strategy.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Trades Table */}
          <div className="glass-card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Trade</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Strategy</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Amount</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Profit/Loss</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Gas</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Time</th>
                  <th className="text-center p-4 text-sm font-medium text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                      Loading trades...
                    </td>
                  </tr>
                ) : trades?.trades?.length > 0 ? (
                  trades.trades.map((trade: any) => (
                    <tr key={trade.id} className="border-b border-border/50 hover:bg-white/5">
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="p-2 rounded-lg bg-white/5">
                            <ArrowRightLeft className="w-4 h-4 text-muted-foreground" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">
                              {trade.token_in_symbol || 'Token'} → {trade.token_out_symbol || 'Token'}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatAddress(trade.tx_hash || trade.id)}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-sm text-white">{trade.strategy}</span>
                      </td>
                      <td className="p-4">
                        <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                          'bg-crypto-green/10 text-crypto-green': trade.status === 'SUCCESS',
                          'bg-crypto-red/10 text-crypto-red': trade.status === 'FAILED',
                          'bg-pancake-500/10 text-pancake-400': trade.status === 'PENDING',
                          'bg-crypto-blue/10 text-crypto-blue': trade.status === 'SIMULATED',
                        })} >
                          {trade.status}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="text-sm text-white">
                          {formatCurrency(trade.amount_in_usd || 0)}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <span className={cn('text-sm font-medium', {
                          'text-crypto-green': (trade.profit_usd || 0) >= 0,
                          'text-crypto-red': (trade.profit_usd || 0) < 0,
                        })} >
                          {(trade.profit_usd || 0) >= 0 ? '+' : ''}
                          {formatCurrency(trade.profit_usd || 0)}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="text-sm text-muted-foreground">
                          {formatCurrency(trade.gas_cost_usd || 0)}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="text-sm text-muted-foreground">
                          {formatDate(trade.created_at || trade.timestamp)}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        {trade.tx_hash && (
                          <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                            <ExternalLink className="w-4 h-4 text-muted-foreground" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="p-8 text-center">
                      <p className="text-muted-foreground">No trades found</p>
                      <p className="text-sm text-muted-foreground mt-1">Try adjusting your filters</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
