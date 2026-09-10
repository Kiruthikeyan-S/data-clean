import React from 'react';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { ProcessResponse } from '../types';
import { ResultTable } from '../components/ResultTable';
import { ExportButtons } from '../components/ExportButtons';
import { DataQualityInspector } from '../components/DataQualityInspector';
import { DataChartsSection } from '../components/DataChartsSection';
import { ExtractedTextCollapsible } from '../components/ExtractedTextCollapsible';
import { ProcessDetailsCollapsible } from '../components/ProcessDetailsCollapsible';

interface ResultPageProps {
  result: ProcessResponse;
  onReset: () => void;
}

export const ResultPage: React.FC<ResultPageProps> = ({ result, onReset }) => {
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
          <span>Process Another File</span>
        </button>

        <ExportButtons taskId={result.id} />
      </div>

      {/* Validation Warnings if any */}
      {result.errors && result.errors.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800">
          <div className="flex items-center gap-2 font-semibold text-amber-900 mb-1">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Validation Warnings ({result.errors.length})</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-amber-700 pl-1">
            {result.errors.map((err, idx) => (
              <li key={idx}>
                <span className="font-medium">{err.field}:</span> {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 6-Dimension Interactive Data Quality Inspector (Missing Values, Duplicates, Wrong Data Types, Invalid Values, Outliers, Format Differences) */}
      {result.cleansing_report?.quality_audit && (
        <DataQualityInspector audit={result.cleansing_report.quality_audit} />
      )}

      {/* Dataset Distribution & Analytics Charts (Pie, Donut, Bar - only when applicable) */}
      {result.visualizations && (
        <DataChartsSection visualizations={result.visualizations} />
      )}

      {/* Structured Result Table with Retained Records count */}
      <ResultTable result={result} />

      {/* Collapsible Extracted Text for unstructured docs */}
      {result.classification === 'unstructured' && result.raw_text && (
        <ExtractedTextCollapsible rawText={result.raw_text} />
      )}

      {/* Collapsible Process Details */}
      <ProcessDetailsCollapsible steps={result.steps} summary={result.summary} />
    </div>
  );
};
