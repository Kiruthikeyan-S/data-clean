import React from 'react';
import { GitFork, CheckCircle2, Database } from 'lucide-react';
import { RelationshipValidationReport } from '../types';

interface Props {
  report?: RelationshipValidationReport;
}

export const RelationshipValidationDashboard: React.FC<Props> = ({ report }) => {
  if (!report) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <GitFork className="w-10 h-10 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-slate-800">Relationship Validation Ready</h3>
        <p className="text-xs text-slate-500 mt-1">Cross-entity foreign key validation will appear once entities are linked.</p>
      </div>
    );
  }

  const { referential_summary, violations, entity_counts } = report;

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Integrity Score</div>
          <div className={`mt-2 text-2xl font-black ${report.integrity_percentage >= 90 ? 'text-emerald-600' : 'text-amber-600'}`}>
            {report.integrity_percentage}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">Foreign key consistency</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Relationships Checked</div>
          <div className="mt-2 text-2xl font-black text-slate-900">{report.total_relationships_checked}</div>
          <div className="mt-1 text-[11px] text-slate-500">Cross-entity references</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Orphan Records</div>
          <div className="mt-2 text-2xl font-black text-rose-600">{referential_summary?.orphan_foreign_keys ?? 0}</div>
          <div className="mt-1 text-[11px] text-rose-700 font-semibold">Missing parent IDs</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Entity Counts</div>
          <div className="mt-2 text-xs font-bold text-slate-700 space-y-0.5">
            <div>Stores: {entity_counts?.stores ?? 0} • Items: {entity_counts?.items ?? 0}</div>
            <div>Customers: {entity_counts?.customers ?? 0} • Txns: {entity_counts?.transactions ?? 0}</div>
          </div>
        </div>
      </div>

      {/* Foreign Key Constraints Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600" />
              Referential Integrity & Foreign Key Constraint Violations ({violations.length})
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Item.Store_ID → Store, Transaction.Store_ID → Store, Transaction.Customer_ID → Customer, Transaction.Item_ID → Item
            </p>
          </div>
          {violations.length === 0 && (
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> 100% Referential Integrity Intact
            </span>
          )}
        </div>

        {violations.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                  <th className="py-2.5 px-3">Relationship Edge</th>
                  <th className="py-2.5 px-3">Violation Type</th>
                  <th className="py-2.5 px-3">Record ID</th>
                  <th className="py-2.5 px-3">Invalid Value</th>
                  <th className="py-2.5 px-3">Remediation Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {violations.map((v, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60">
                    <td className="py-2.5 px-3 font-semibold text-slate-800 flex items-center gap-1">
                      <span className="text-blue-600">{v.relationship}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        v.violation_type === 'orphan_foreign_key'
                          ? 'bg-rose-100 text-rose-800'
                          : v.violation_type === 'duplicate_primary_key'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {v.violation_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-900">{v.source_record_id}</td>
                    <td className="py-2.5 px-3 font-mono text-rose-700">{String(v.invalid_value)}</td>
                    <td className="py-2.5 px-3 text-slate-600 text-[11px]">{v.remediation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-slate-500">
            All foreign key relationships and primary keys are fully valid and consistent.
          </div>
        )}
      </div>
    </div>
  );
};
