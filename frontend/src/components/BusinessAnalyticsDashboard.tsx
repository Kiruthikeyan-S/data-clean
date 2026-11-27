import React, { useState, useMemo } from 'react';
import {
  DollarSign,
  ShoppingCart,
  TrendingUp,
  AlertOctagon,
  Package,
  Users,
  Store,
  ChevronLeft,
  ChevronRight,
  Calculator,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { BusinessAnalyticsReport, DemandPredictionReport } from '../types';

interface Props {
  analytics?: BusinessAnalyticsReport;
  demand?: DemandPredictionReport;
}

const PAGE_SIZE = 15;

export const BusinessAnalyticsDashboard: React.FC<Props> = ({ analytics, demand }) => {
  const [statusFilter, setStatusFilter] = useState<'all' | 'alerts' | 'healthy'>('all');
  const [page, setPage] = useState(1);
  const [showFormulas, setShowFormulas] = useState(true);

  const forecasts = demand?.forecasts || [];
  const filteredForecasts = useMemo(() => {
    if (statusFilter === 'alerts') {
      return forecasts.filter(f => f.reorder_urgency !== 'healthy');
    }
    if (statusFilter === 'healthy') {
      return forecasts.filter(f => f.reorder_urgency === 'healthy');
    }
    return forecasts;
  }, [forecasts, statusFilter]);

  if (!analytics && !demand) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <TrendingUp className="w-10 h-10 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-slate-800">Business Analytics Ready</h3>
        <p className="text-xs text-slate-500 mt-1">
          Upload retail or inventory data to view revenue and demand forecasts.
        </p>
      </div>
    );
  }

  const txn = analytics?.transaction_analytics;
  const store = analytics?.store_analytics;
  const cust = analytics?.customer_analytics;

  const formatCurrency = (val?: number) => {
    const num = val ?? 0;
    if (num >= 100) {
      return `$${Math.round(num).toLocaleString()}`;
    }
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatVelocity = (vel: number) => {
    if (vel >= 1) {
      return `${Math.round(vel).toLocaleString()} / day`;
    }
    const weekly = Math.max(1, Math.round(vel * 7));
    return `${weekly.toLocaleString()} / week`;
  };

  const formatAction = (urgency: 'critical' | 'medium' | 'healthy', reorderQty: number) => {
    const qty = Math.max(1, Math.round(reorderQty || 0));
    const unitLabel = qty === 1 ? 'unit' : 'units';
    if (urgency === 'critical') return `Reorder ${qty.toLocaleString()} ${unitLabel} now`;
    if (urgency === 'medium') return `Reorder ${qty.toLocaleString()} ${unitLabel}`;
    return 'No reorder needed';
  };

  const totalPages = Math.max(1, Math.ceil(filteredForecasts.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedForecasts = filteredForecasts.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const alertCount = demand?.stock_shortage_alerts_count ?? 0;

  return (
    <div className="space-y-6">
      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">{formatCurrency(txn?.total_revenue)}</div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-emerald-600 font-semibold">Validated sales</span>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200" title="Total Revenue = Σ (Quantity × Unit Price)">
              Σ(Qty × Price)
            </span>
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Transactions</span>
            <ShoppingCart className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            {(txn?.total_transactions ?? 0).toLocaleString()}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium">Recorded orders</span>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200" title="Count of total orders">
              Count(Orders)
            </span>
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Average Value</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            {formatCurrency(txn?.average_transaction_value)}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium">Per transaction</span>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200" title="Average Value = Total Revenue ÷ Total Transactions">
              Revenue ÷ Orders
            </span>
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Reorder Alerts</span>
            <AlertOctagon className={`w-4 h-4 ${alertCount > 0 ? 'text-rose-600' : 'text-emerald-600'}`} />
          </div>
          <div className={`mt-2 text-2xl font-black ${alertCount > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
            {alertCount.toLocaleString()}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className={`font-semibold ${alertCount > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
              {alertCount > 0 ? 'Low-stock items' : 'Healthy stock'}
            </span>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200" title="Low stock trigger when Current Stock ÷ Daily Velocity <= 7 days">
              Stock ÷ V ≤ 7d
            </span>
          </div>
        </div>
      </div>

      {/* Applied Financial & Demand Formulas Section */}
      <div className="bg-white rounded-xl border border-indigo-200 shadow-xs overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-gradient-to-r from-indigo-50/90 via-blue-50/70 to-slate-50 border-b border-indigo-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-600 text-white rounded-lg shadow-2xs">
              <Calculator className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Applied Calculation Formulas & Logic Guide</h4>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800">
                  Business Math
                </span>
              </div>
              <p className="text-[11px] text-slate-600 mt-0.5">
                Exact mathematical formulas used in this dashboard for revenue, daily velocity, 30-day demand, and restocking alerts.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowFormulas(prev => !prev)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white hover:bg-slate-50 text-indigo-700 border border-indigo-200 transition-colors shadow-2xs w-fit"
          >
            <Info className="w-3.5 h-3.5 text-indigo-600" />
            <span>{showFormulas ? 'Hide Formulas' : 'Show All Formulas'}</span>
            {showFormulas ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showFormulas && (
          <div className="p-4 sm:p-5 bg-slate-50/50 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {/* Card 1: Total Revenue */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                    1. Total Revenue (Total Value)
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">Revenue</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  Total Value = Σ (Quantity Sold × Unit Price)
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Sums the product of quantity sold and unit price across all validated transactions to calculate overall monetary revenue.
                </p>
              </div>

              {/* Card 2: Average Value */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                    2. Average Transaction Value (ATV / Mean)
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-bold border border-blue-200">Mean</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  ATV = Total Revenue ÷ Total Transactions
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  The arithmetic mean revenue generated per customer order, indicating typical purchasing ticket size.
                </p>
              </div>

              {/* Card 3: Daily Velocity */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Package className="w-3.5 h-3.5 text-blue-600" />
                    3. Daily Sales Velocity (V)
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">Velocity</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  Velocity (V) = Σ Units Sold ÷ Observed Days
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Average item sales speed per day (min 7-day span). If V &lt; 1.0, displayed as <code>V × 7</code> units per week.
                </p>
              </div>

              {/* Card 4: Predicted Demand */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Calculator className="w-3.5 h-3.5 text-purple-600" />
                    4. 30-Day Demand Forecast (D)
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-bold border border-purple-200">Forecast</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  Demand (D) = ⌈ Velocity (V) × 30 Days ⌉
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Projects unit demand over 30 days, ceiling-rounded to whole physical units so no fractional products are predicted.
                </p>
              </div>

              {/* Card 5: Confidence Range */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-amber-600" />
                    5. Confidence Range (Min – Max)
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 font-bold border border-amber-200">90% Range</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  Range = [ D - 1.645×SE , D + 1.645×SE ]
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  90% statistical uncertainty interval from slow to peak month based on order size standard error SE = (s / √n) × √30.
                </p>
              </div>

              {/* Card 6: Reorder Action */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
                    6. Reorder Action & Restock Qty
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 font-bold border border-rose-200">Restock</span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-200 font-mono text-xs font-bold text-slate-900">
                  Q = ⌈ Upper Bound - Stock + (V × 7) ⌉
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Alerts if Days of Stock (Stock ÷ V) ≤ 7 days. Reorders enough units to reach peak demand plus a 7-day supplier buffer.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Inventory Demand Forecasting Table */}
      {demand && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-600" />
              Inventory Demand Forecasting ({demand.forecast_horizon_days}-Day)
            </h3>

            <div className="flex flex-wrap items-center gap-2">
              {forecasts.length > 0 && (
                <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-[11px] font-semibold">
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('all');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    All ({forecasts.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('alerts');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'alerts' ? 'bg-white text-rose-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Needs Reorder ({forecasts.filter(f => f.reorder_urgency !== 'healthy').length})
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('healthy');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'healthy' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Healthy ({forecasts.filter(f => f.reorder_urgency === 'healthy').length})
                  </button>
                </div>
              )}

              <span
                className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase border ${
                  demand.data_sufficiency_status === 'sufficient'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}
              >
                {demand.data_sufficiency_status} data
              </span>
            </div>
          </div>

          {demand.limitations && demand.data_sufficiency_status !== 'sufficient' && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
              <span className="font-bold">Data Limitation: </span>
              {demand.limitations}
            </div>
          )}

          {paginatedForecasts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                    <th className="py-2.5 px-3">Item Name</th>
                    <th className="py-2.5 px-3" title="Physical units currently in warehouse inventory">
                      Current Stock
                    </th>
                    <th className="py-2.5 px-3" title="Formula: Total Sold ÷ Observed Days (minimum 7-day span)">
                      <div className="flex items-center gap-1 cursor-help">
                        <span>Daily Velocity</span>
                        <Info className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-2.5 px-3" title="Formula: ⌈ Daily Velocity × 30 Days ⌉ (rounded up to whole integer)">
                      <div className="flex items-center gap-1 cursor-help">
                        <span>Predicted Demand</span>
                        <Info className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-2.5 px-3" title="Formula: 90% Confidence Interval: Demand ± 1.645 × Standard Error">
                      <div className="flex items-center gap-1 cursor-help">
                        <span>Confidence Range</span>
                        <Info className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-2.5 px-3" title="Formula: Days of Stock = Current Stock ÷ Daily Velocity">
                      <div className="flex items-center gap-1 cursor-help">
                        <span>Status</span>
                        <Info className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                    <th className="py-2.5 px-3" title="Formula: ⌈ Upper Bound - Current Stock + (Velocity × 7-Day Safety Buffer) ⌉">
                      <div className="flex items-center gap-1 cursor-help">
                        <span>Reorder Action</span>
                        <Info className="w-3 h-3 text-slate-400" />
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedForecasts.map((fc, idx) => {
                    const stockUnits = Math.round(fc.current_stock);
                    const predUnits = Math.round(fc.predicted_demand);
                    const minUnits = Math.round(fc.lower_confidence_bound);
                    const maxUnits = Math.round(fc.upper_confidence_bound);

                    const statusBadge =
                      fc.reorder_urgency === 'critical'
                        ? { label: 'Critical', cls: 'bg-rose-100 text-rose-800' }
                        : fc.reorder_urgency === 'medium'
                        ? { label: 'Low Stock', cls: 'bg-amber-100 text-amber-800' }
                        : { label: 'Healthy', cls: 'bg-emerald-100 text-emerald-800' };

                    return (
                      <tr key={idx} className="hover:bg-slate-50/70">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">{fc.item_name}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-800">{stockUnits.toLocaleString()}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700">
                          {formatVelocity(fc.historical_sales_velocity_daily)}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-blue-700">
                          {predUnits.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-600">
                          {minUnits.toLocaleString()} – {maxUnits.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${statusBadge.cls}`}>
                            {statusBadge.label}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-xs text-slate-700">
                          {formatAction(fc.reorder_urgency, fc.recommended_reorder_quantity)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {filteredForecasts.length > PAGE_SIZE && (
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100 text-xs text-slate-600">
                  <span>
                    {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filteredForecasts.length)} of{' '}
                    {filteredForecasts.length}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-2 font-semibold text-slate-800">
                      {safePage} / {totalPages}
                    </span>
                    <button
                      type="button"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-slate-100">
              No items match the selected filter.
            </div>
          )}
        </div>
      )}

      {/* Grid: Store Analytics & Top Spenders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {store && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Store className="w-4 h-4 text-blue-600" />
              Store Performance ({store.total_stores})
            </h3>
            <div className="space-y-2">
              {store.store_wise_metrics?.map((st, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-800">{st.store_name}</div>
                    <div className="text-[11px] text-slate-500">
                      {st.store_id} • {st.transactions_count.toLocaleString()} orders
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-slate-900">{formatCurrency(st.total_sales)}</div>
                    <div className="text-[11px] text-slate-500 font-medium">
                      Stock: {Math.round(st.total_stock).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {cust && cust.total_customers > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Users className="w-4 h-4 text-indigo-600" />
              Top Customers ({cust.total_customers.toLocaleString()})
            </h3>
            <div className="space-y-2">
              {cust.top_customers_by_spend?.map((cu, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-800">{cu.customer_name}</div>
                    <div className="text-[11px] text-slate-500">
                      {cu.customer_id} • {cu.orders_count.toLocaleString()} orders
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-emerald-700">{formatCurrency(cu.total_spend)}</div>
                    <div className="text-[10px] text-slate-400">Total spend</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
