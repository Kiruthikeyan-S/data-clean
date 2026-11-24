import React from 'react';
import { DollarSign, ShoppingCart, TrendingUp, AlertOctagon, Package, Users, Store } from 'lucide-react';
import { BusinessAnalyticsReport, DemandPredictionReport } from '../types';

interface Props {
  analytics?: BusinessAnalyticsReport;
  demand?: DemandPredictionReport;
}

export const BusinessAnalyticsDashboard: React.FC<Props> = ({ analytics, demand }) => {
  if (!analytics && !demand) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <TrendingUp className="w-10 h-10 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-slate-800">Business Analytics Ready</h3>
        <p className="text-xs text-slate-500 mt-1">Upload and clean retail transactions to view revenue and demand predictions.</p>
      </div>
    );
  }

  const txn = analytics?.transaction_analytics;
  const store = analytics?.store_analytics;
  const cust = analytics?.customer_analytics;

  return (
    <div className="space-y-6">
      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            ${txn?.total_revenue?.toLocaleString() ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-emerald-600 font-semibold">Validated sales</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Transactions</span>
            <ShoppingCart className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            {txn?.total_transactions?.toLocaleString() ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-slate-500 font-medium">Recorded orders</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Average Value (ATV)</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            ${txn?.average_transaction_value ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-slate-500 font-medium">Per transaction</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Reorder Alerts</span>
            <AlertOctagon className="w-4 h-4 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-rose-600">
            {demand?.stock_shortage_alerts_count ?? 0}
          </div>
          <div className="mt-1 text-[11px] text-rose-700 font-semibold">Potential stockouts</div>
        </div>
      </div>

      {/* Demand Prediction & Inventory Forecast */}
      {demand && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Package className="w-4 h-4 text-blue-600" />
                Inventory Demand Forecasting ({demand.forecast_horizon_days}-Day Horizon)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Statistical velocity predictions with upper & lower confidence bounds
              </p>
            </div>
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase border ${
              demand.data_sufficiency_status === 'sufficient'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {demand.data_sufficiency_status} data
            </span>
          </div>

          {demand.limitations && demand.data_sufficiency_status !== 'sufficient' && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
              <span className="font-bold">Data Limitation: </span>
              {demand.limitations}
            </div>
          )}

          {demand.forecasts && demand.forecasts.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                    <th className="py-2.5 px-3">Item Name</th>
                    <th className="py-2.5 px-3">Current Stock</th>
                    <th className="py-2.5 px-3">Daily Velocity</th>
                    <th className="py-2.5 px-3">Predicted Demand</th>
                    <th className="py-2.5 px-3">Confidence Bounds</th>
                    <th className="py-2.5 px-3">Status / Urgency</th>
                    <th className="py-2.5 px-3">Reorder Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {demand.forecasts.map((fc, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/60">
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{fc.item_name}</td>
                      <td className="py-2.5 px-3 font-mono">{fc.current_stock}</td>
                      <td className="py-2.5 px-3 font-mono">{fc.historical_sales_velocity_daily} / day</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-blue-700">{fc.predicted_demand}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-500 text-[11px]">
                        [{fc.lower_confidence_bound} – {fc.upper_confidence_bound}]
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          fc.reorder_urgency === 'critical'
                            ? 'bg-rose-100 text-rose-800 font-extrabold'
                            : fc.reorder_urgency === 'medium'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {fc.reorder_urgency}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-700">
                        {fc.actionable_recommendation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Grid: Store Analytics & Top Spenders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Store Analytics */}
        {store && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Store className="w-4 h-4 text-blue-600" />
              Store Performance & Stock Holdings ({store.total_stores} Stores)
            </h3>
            <div className="space-y-2">
              {store.store_wise_metrics?.map((st, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-slate-800">{st.store_name}</div>
                    <div className="text-[11px] text-slate-500">ID: {st.store_id} • {st.transactions_count} orders</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-slate-900">${st.total_sales.toLocaleString()}</div>
                    <div className="text-[11px] text-slate-500 font-medium">Stock: {st.total_stock} units</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Customer Spending & Loyalty */}
        {cust && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Users className="w-4 h-4 text-indigo-600" />
              Top Customers & Lifetime Value ({cust.total_customers} Customers)
            </h3>
            <div className="space-y-2">
              {cust.top_customers_by_spend?.map((cu, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-slate-800">{cu.customer_name}</div>
                    <div className="text-[11px] text-slate-500">ID: {cu.customer_id} • {cu.orders_count} purchase(s)</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-emerald-700">${cu.total_spend.toLocaleString()}</div>
                    <div className="text-[10px] text-slate-400">Total Spend</div>
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
