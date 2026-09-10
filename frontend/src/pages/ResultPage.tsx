import React from 'react';
import { ArrowLeft, AlertTriangle, Files, CheckCircle2 } from 'lucide-react';
import { ProcessResponse } from '../types';
import { ResultTable } from '../components/ResultTable';
import { ExportButtons } from '../components/ExportButtons';
import { DataQualityInspector } from '../components/DataQualityInspector';
import { ExtractedTextCollapsible } from '../components/ExtractedTextCollapsible';
import { ProcessDetailsCollapsible } from '../components/ProcessDetailsCollapsible';

interface ResultPageProps {
  results: ProcessResponse[];
  activeIndex: number;
  onSelectIndex: (index: number) => void;
  onReset: () => void;
}

export const ResultPage: React.FC<ResultPageProps> = ({
  results,
  activeIndex,
  onSelectIndex,
  onReset
}) => {
  const currentResult = results[activeIndex] || results[0];
  if (!currentResult) return null;

  return (
    <div className="py-6 sm:py-8 px-4 sm:px-6 lg:px-8 max-w-[1700px] mx-auto space-y-6 w-full">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-300 hover:bg-slate-50 px-3 py-1.5 rounded-md transition-colors w-fit shadow-2xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Upload More Files</span>
        </button>

        <ExportButtons taskId={currentResult.id} />
      </div>

      {/* Multi-File Batch Dataset Switcher Tabs */}
      {results.length > 1 && (
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <Files className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-slate-900">
                Batch Processed Datasets ({results.length} Files Cleaned)
              </span>
            </div>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              All Files Ready
            </span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1">
            {results.map((res, idx) => {
              const isSelected = idx === activeIndex;
              const ext = res.filename.split('.').pop()?.toUpperCase() || res.file_type.toUpperCase();
              return (
                <button
                  key={res.id || idx}
                  onClick={() => onSelectIndex(idx)}
                  className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg text-xs font-medium border transition-all whitespace-nowrap ${
                    isSelected
                      ? 'bg-blue-50/80 border-blue-300 text-blue-900 shadow-xs font-bold'
                      : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center ${
                    isSelected ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {idx + 1}
                  </span>
                  <span className="truncate max-w-[200px]">{res.filename}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/80 border border-slate-200 font-mono text-slate-600">
                    {ext}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Validation Warnings if any */}
      {currentResult.errors && currentResult.errors.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800">
          <div className="flex items-center gap-2 font-semibold text-amber-900 mb-1">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Validation Warnings ({currentResult.errors.length})</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-amber-700 pl-1">
            {currentResult.errors.map((err, idx) => (
              <li key={idx}>
                <span className="font-medium">{err.field}:</span> {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 6-Dimension Interactive Data Quality Inspector */}
      {currentResult.cleansing_report?.quality_audit && (
        <DataQualityInspector audit={currentResult.cleansing_report.quality_audit} />
      )}

      {/* Structured Result Table with Retained Records count */}
      <ResultTable result={currentResult} />

      {/* Collapsible Extracted Text for unstructured docs */}
      {currentResult.classification === 'unstructured' && currentResult.raw_text && (
        <ExtractedTextCollapsible rawText={currentResult.raw_text} />
      )}

      {/* Collapsible Process Details */}
      <ProcessDetailsCollapsible steps={currentResult.steps} summary={currentResult.summary} />
    </div>
  );
};
