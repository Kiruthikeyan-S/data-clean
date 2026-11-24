import React, { useState } from 'react';
import { ShieldCheck, AlertCircle, CheckCircle2, AlertTriangle, HelpCircle, Layers } from 'lucide-react';
import { QualityProfileReport } from '../types';

interface Props {
  profile?: QualityProfileReport;
}

export const DataQualityProfilerDashboard: React.FC<Props> = ({ profile }) => {
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);

  if (!profile) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <ShieldCheck className="w-10 h-10 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-slate-800">Quality Profiler Ready</h3>
        <p className="text-xs text-slate-500 mt-1">Run data processing to view detailed quality audit metrics.</p>
      </div>
    );
  }

  const columnsWithIssues = Object.keys(profile.issues_by_column || {});
  const activeCol = selectedColumn || (columnsWithIssues.length > 0 ? columnsWithIssues[0] : null);
  const activeIssues = activeCol ? profile.issues_by_column[activeCol] || [] : [];

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 70) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-rose-600 bg-rose-50 border-rose-200';
  };

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Quality Score</div>
          <div className={`mt-2 text-2xl font-black ${profile.quality_percentage >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>
            {profile.quality_percentage}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">Overall Accuracy</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Records</div>
          <div className="mt-2 text-2xl font-black text-slate-900">{profile.total_records}</div>
          <div className="mt-1 text-[11px] text-slate-500">Processed rows</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Valid Records</div>
          <div className="mt-2 text-2xl font-black text-emerald-600">{profile.valid_records}</div>
          <div className="mt-1 text-[11px] text-emerald-700">100% compliant</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Missing Values</div>
          <div className="mt-2 text-2xl font-black text-amber-600">{profile.missing_value_count}</div>
          <div className="mt-1 text-[11px] text-slate-500">Empty / null cells</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Duplicates</div>
          <div className="mt-2 text-2xl font-black text-blue-600">{profile.duplicate_count}</div>
          <div className="mt-1 text-[11px] text-slate-500">Collisions found</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Invalid Formats</div>
          <div className="mt-2 text-2xl font-black text-rose-600">{profile.invalid_value_count}</div>
          <div className="mt-1 text-[11px] text-slate-500">Malformed cells</div>
        </div>
      </div>

      {/* Main Grid: Column Diagnostics & Recommended Corrections */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Column Selectors */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-blue-600" />
              Column Quality Breakdown
            </h3>
            <span className="text-[10px] text-slate-500 font-semibold">{columnsWithIssues.length} columns flagged</span>
          </div>

          <div className="space-y-1.5 max-h-[420px] overflow-y-auto pr-1">
            {columnsWithIssues.map((col) => {
              const issues = profile.issues_by_column[col] || [];
              const score = (profile.column_quality_scores[col] !== undefined ? profile.column_quality_scores[col] * 100 : 100);
              const isSelected = col === activeCol;

              return (
                <button
                  key={col}
                  type="button"
                  onClick={() => setSelectedColumn(col)}
                  className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between ${
                    isSelected
                      ? 'bg-blue-50/80 border-blue-300 shadow-2xs'
                      : 'bg-slate-50 hover:bg-slate-100 border-slate-200'
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-bold text-slate-800">{col}</div>
                    <div className="text-[11px] text-slate-500">{issues.length} issue(s) detected</div>
                  </div>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${getScoreColor(score)}`}>
                    {Math.round(score)}%
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Active Column Issues & Recommended Fixes */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Issues for <span className="font-mono text-blue-600 font-extrabold">{activeCol || 'None Selected'}</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Non-destructive diagnostics (original raw values preserved)</p>
            </div>
            {activeIssues.length === 0 && (
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Clean Column
              </span>
            )}
          </div>

          <div className="space-y-3">
            {activeIssues.map((iss, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 flex items-center gap-1.5">
                    {iss.severity === 'high' ? (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    )}
                    {iss.issue_type.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                    iss.severity === 'high' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {iss.count} occurrences
                  </span>
                </div>

                <p className="text-slate-600">{iss.description}</p>

                {iss.sample_invalid_values && iss.sample_invalid_values.length > 0 && (
                  <div className="pt-1 flex items-center gap-1.5 flex-wrap">
                    <span className="text-[11px] font-semibold text-slate-500">Sample values:</span>
                    {iss.sample_invalid_values.slice(0, 4).map((s_val, s_idx) => (
                      <span key={s_idx} className="font-mono text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-700">
                        {String(s_val)}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-2 pt-2 border-t border-slate-200/80 flex items-start gap-1.5 text-blue-900 bg-blue-50/70 p-2 rounded-md">
                  <HelpCircle className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[11px]">Recommended Correction: </span>
                    <span className="text-[11px]">{iss.recommended_correction}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
