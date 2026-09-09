import React from 'react';
import {
  Calendar,
  Zap,
  FileText,
  ShieldCheck,
  CheckCircle2,
  Database,
  Sparkles,
  Layers
} from 'lucide-react';
import { ProcessResponse } from '../types';

interface UploadAnalyticsOverviewProps {
  result: ProcessResponse;
}

export const UploadAnalyticsOverview: React.FC<UploadAnalyticsOverviewProps> = ({ result }) => {
  const { summary, cleansing_report } = result;

  // Format File Size
  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Format Timestamp
  const formattedDateTime = result.processed_at
    ? result.processed_at
    : new Date().toISOString().replace('T', ' ').substring(0, 19);

  const qualityScore = summary.quality_score ?? 100.0;
  const totalModifications =
    (cleansing_report?.duplicates_removed || 0) +
    (cleansing_report?.empty_rows_removed || 0) +
    (cleansing_report?.nulls_normalized || 0) +
    (cleansing_report?.whitespace_trimmed || 0);

  const columnsCount = result.columns?.length || result.fields?.length || 0;

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
      {/* Top Banner with File, Date & Time Analysis */}
      <div className="px-5 py-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-blue-400 flex-shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-sm sm:text-base font-bold text-white tracking-tight truncate max-w-md">
                {result.filename}
              </h1>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30">
                {result.file_type.toUpperCase()}
              </span>
              <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-700/80 text-slate-300">
                {formatBytes(result.file_size_bytes)}
              </span>
            </div>
            <p className="text-xs text-slate-300 flex items-center gap-2 mt-0.5">
              <span>{result.classification === 'structured' ? 'Structured Tabular Dataset' : 'Unstructured Document Extraction'}</span>
              <span>•</span>
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 inline" />
                Cleaned & Verified
              </span>
            </p>
          </div>
        </div>

        {/* Date, Time & Execution Speed Pills */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700 text-slate-200">
            <Calendar className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-mono text-[11px] font-medium">{formattedDateTime}</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700 text-slate-200">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-mono text-[11px] font-semibold text-amber-300">{summary.processing_time_ms} ms</span>
          </div>
        </div>
      </div>

      {/* Primary Analytics Executive Grid */}
      <div className="p-5 grid grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50/50 border-b border-slate-100">
        {/* Metric 1: Quality Score */}
        <div className="bg-white p-3.5 rounded-lg border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-medium">Quality Index</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{qualityScore}%</span>
            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
              Optimal
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Audit verification score</span>
        </div>

        {/* Metric 2: Retained Records */}
        <div className="bg-white p-3.5 rounded-lg border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-medium">Retained Records</span>
            <Database className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{summary.total_records}</span>
            <span className="text-[10px] text-slate-500 font-medium">Clean Rows</span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Ready for instant export</span>
        </div>

        {/* Metric 3: Anomalies Handled */}
        <div className="bg-white p-3.5 rounded-lg border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-medium">Cleanse Actions</span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{totalModifications}</span>
            <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
              Fixed
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Duplicates & nulls normalized</span>
        </div>

        {/* Metric 4: Schema Dimensions */}
        <div className="bg-white p-3.5 rounded-lg border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-medium">Dimensions</span>
            <Layers className="w-4 h-4 text-purple-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900">{columnsCount}</span>
            <span className="text-[10px] text-slate-500 font-medium">
              {result.classification === 'structured' ? 'Columns' : 'Entities'}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Schema mapped & validated</span>
        </div>
      </div>
    </div>
  );
};
