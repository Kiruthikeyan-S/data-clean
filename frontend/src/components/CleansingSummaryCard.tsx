import React, { useState } from 'react';
import { 
  Sparkles, 
  Trash2, 
  CheckCircle2, 
  RefreshCw, 
  ChevronDown, 
  ChevronRight, 
  ShieldCheck, 
  FileX2, 
  Layers
} from 'lucide-react';
import { CleansingReport, CleansingCategory } from '../types';

interface CleansingSummaryCardProps {
  report?: CleansingReport;
  classification: 'structured' | 'unstructured';
}

export const CleansingSummaryCard: React.FC<CleansingSummaryCardProps> = ({ report, classification }) => {
  const [showDuplicatesModal, setShowDuplicatesModal] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!report) return null;

  const hasStructuredMetrics = classification === 'structured' && report.initial_rows !== undefined;

  const getCategoryIcon = (iconType: string) => {
    switch (iconType) {
      case 'dedup':
        return <Trash2 className="w-4 h-4 text-amber-600" />;
      case 'missing':
        return <FileX2 className="w-4 h-4 text-blue-600" />;
      case 'sanitize':
        return <Sparkles className="w-4 h-4 text-indigo-600" />;
      case 'standardize':
        return <RefreshCw className="w-4 h-4 text-emerald-600" />;
      case 'validate':
        return <ShieldCheck className="w-4 h-4 text-sky-600" />;
      default:
        return <Layers className="w-4 h-4 text-slate-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    if (status.includes('Removed') || status.includes('Warnings')) {
      return (
        <span className="px-2 py-0.5 text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 rounded-full">
          {status}
        </span>
      );
    }
    if (status === 'Clean' || status === 'Verified' || status === 'Applied' || status === 'Handled') {
      return (
        <span className="px-2 py-0.5 text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          {status}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
        {status}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
      {/* Header bar */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 border border-blue-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">Data Cleansing & Quality Report</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Handling Missing Data, Deduplication, Whitespace Sanitization & Value Standardization
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50/70 hover:bg-blue-100/70 px-2.5 py-1.5 rounded-md transition-colors w-fit self-start sm:self-auto border border-blue-100"
        >
          <span>{isExpanded ? 'Hide Operations' : 'View Operations Breakdown'}</span>
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Metrics Row */}
      <div className="p-4 sm:p-5 bg-slate-50/50">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* 1. Records Retained */}
          {hasStructuredMetrics ? (
            <div className="p-3 bg-white rounded-lg border border-slate-200/80">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Retained Records</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              </div>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span className="text-lg font-bold text-slate-900">{report.final_rows}</span>
                <span className="text-xs text-slate-400">/ {report.initial_rows} initial</span>
              </div>
            </div>
          ) : (
            <div className="p-3 bg-white rounded-lg border border-slate-200/80">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Dataset Quality</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              </div>
              <div className="mt-1 text-sm font-bold text-emerald-700">
                100% Cleaned
              </div>
            </div>
          )}

          {/* 2. Deduplication */}
          <div className="p-3 bg-white rounded-lg border border-slate-200/80">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Deduplication</span>
              <Trash2 className={`w-3.5 h-3.5 ${report.duplicates_removed > 0 ? 'text-amber-500' : 'text-slate-400'}`} />
            </div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className={`text-lg font-bold ${report.duplicates_removed > 0 ? 'text-amber-700' : 'text-slate-800'}`}>
                {report.duplicates_removed} <span className="text-xs font-normal text-slate-400">removed</span>
              </span>
              {report.removed_samples && report.removed_samples.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowDuplicatesModal(!showDuplicatesModal)}
                  className="text-[11px] font-semibold text-blue-600 hover:underline"
                >
                  {showDuplicatesModal ? 'Hide' : 'Inspect'}
                </button>
              )}
            </div>
          </div>

          {/* 3. Missing Data Handled */}
          <div className="p-3 bg-white rounded-lg border border-slate-200/80">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Missing Data</span>
              <FileX2 className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <div className="mt-1">
              <span className="text-lg font-bold text-slate-800">
                {report.nulls_normalized + report.empty_rows_removed}{' '}
                <span className="text-xs font-normal text-slate-400">handled</span>
              </span>
            </div>
          </div>

          {/* 4. Whitespace & Text Sanitized */}
          <div className="p-3 bg-white rounded-lg border border-slate-200/80">
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Sanitization</span>
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            </div>
            <div className="mt-1">
              <span className="text-lg font-bold text-slate-800">
                {report.whitespace_trimmed}{' '}
                <span className="text-xs font-normal text-slate-400">cells trimmed</span>
              </span>
            </div>
          </div>
        </div>

        {/* Sample Duplicate Records Preview Modal/Drawer */}
        {showDuplicatesModal && report.removed_samples && report.removed_samples.length > 0 && (
          <div className="mt-4 p-4 rounded-lg bg-amber-50/70 border border-amber-200 text-xs">
            <div className="font-semibold text-amber-900 mb-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Trash2 className="w-3.5 h-3.5 text-amber-700" />
                <span>Sample Duplicate Rows Removed by Deduplication:</span>
              </div>
              <span className="text-[11px] text-amber-800 font-normal">Showing first {report.removed_samples.length} items</span>
            </div>
            <div className="overflow-x-auto bg-white rounded border border-amber-200/80">
              <table className="w-full text-left">
                <thead className="bg-amber-100/50 text-[11px] font-semibold text-amber-900 border-b border-amber-200">
                  <tr>
                    {Object.keys(report.removed_samples[0]).map(k => (
                      <th key={k} className="px-3 py-1.5 whitespace-nowrap">{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-amber-100 text-[11px] text-slate-700 font-mono">
                  {report.removed_samples.map((row, idx) => (
                    <tr key={idx} className="hover:bg-amber-50/50">
                      {Object.values(row).map((v, cidx) => (
                        <td key={cidx} className="px-3 py-1.5 whitespace-nowrap">
                          {v === null ? <span className="text-slate-300 italic">null</span> : String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Categorized Cleansing Operations Breakdown */}
      {isExpanded && report.categories && report.categories.length > 0 && (
        <div className="p-4 sm:p-5 border-t border-slate-200 bg-white space-y-3">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Applied Cleansing & Standardization Rules
            </h4>
            <span className="text-[11px] text-slate-400 font-medium">
              {report.categories.length} quality modules active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {report.categories.map((cat: CleansingCategory) => {
              return (
                <div 
                  key={cat.id} 
                  className="rounded-lg border border-slate-200/80 bg-slate-50/40 p-3.5 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-md bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
                        {getCategoryIcon(cat.icon_type)}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                          <span>{cat.title}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                          {cat.description}
                        </p>
                      </div>
                    </div>
                    <div>
                      {getStatusBadge(cat.status)}
                    </div>
                  </div>

                  {cat.details && cat.details.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/60 pl-9">
                      <ul className="space-y-1">
                        {cat.details.map((d, didx) => (
                          <li key={didx} className="text-[11px] text-slate-600 flex items-start gap-1.5">
                            <span className="text-blue-500 font-bold">•</span>
                            <span>{d}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
