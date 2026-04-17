'use client';

import { useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { Button } from '@/components/ui/button';
import { Settings as SettingsIcon, Shield, Wallet, Bell, Database, Globe, Save } from 'lucide-react';

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
              <p className="text-muted-foreground">Configure your trading agent parameters</p>
            </div>
            <Button onClick={handleSave} className="gap-2">
              <Save className="w-4 h-4" />
              {saved ? 'Saved!' : 'Save Changes'}
            </Button>
          </div>

          <div className="space-y-6 max-w-3xl">
            {/* Trading Parameters */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-pancake-500/10">
                  <SettingsIcon className="w-5 h-5 text-pancake-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">Trading Parameters</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Min Profit (USD)</label>
                  <input type="number" defaultValue={1.0} step={0.1} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Max Slippage (%)</label>
                  <input type="number" defaultValue={0.5} step={0.1} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Max Gas Price (Gwei)</label>
                  <input type="number" defaultValue={50} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Trade Deadline (min)</label>
                  <input type="number" defaultValue={5} className="input-field w-full text-sm" />
                </div>
              </div>
            </div>

            {/* Risk Management */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-crypto-red/10">
                  <Shield className="w-5 h-5 text-crypto-red" />
                </div>
                <h3 className="text-lg font-semibold text-white">Risk Management</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Max Position Size (USD)</label>
                  <input type="number" defaultValue={500} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Max Daily Loss (USD)</label>
                  <input type="number" defaultValue={100} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Stop Loss (%)</label>
                  <input type="number" defaultValue={5} step={0.5} className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Take Profit (%)</label>
                  <input type="number" defaultValue={10} step={0.5} className="input-field w-full text-sm" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-3">
                <input type="checkbox" defaultChecked id="circuit-breaker" className="w-4 h-4 accent-pancake-500" />
                <label htmlFor="circuit-breaker" className="text-sm text-white">Enable Circuit Breaker (auto-stop on excessive losses)</label>
              </div>
            </div>

            {/* Network */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-crypto-blue/10">
                  <Globe className="w-5 h-5 text-crypto-blue" />
                </div>
                <h3 className="text-lg font-semibold text-white">Network Configuration</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">BSC RPC URL</label>
                  <input type="text" defaultValue="https://bsc-dataseed.binance.org/" className="input-field w-full text-sm" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">BSC Testnet RPC URL</label>
                  <input type="text" defaultValue="https://data-seed-prebsc-1-s1.binance.org:8545/" className="input-field w-full text-sm" />
                </div>
              </div>
              <div className="mt-4 p-3 bg-pancake-500/10 rounded-lg border border-pancake-500/20">
                <p className="text-xs text-pancake-400 font-medium">⚠ Currently running on BSC Testnet. Switch to Mainnet for production trading.</p>
              </div>
            </div>

            {/* Wallet */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-crypto-green/10">
                  <Wallet className="w-5 h-5 text-crypto-green" />
                </div>
                <h3 className="text-lg font-semibold text-white">Wallet</h3>
              </div>
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Wallet Address</label>
                <input type="text" placeholder="0x..." className="input-field w-full text-sm font-mono" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">Private key is stored securely on the server and never exposed to the frontend.</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
