import React, { useState } from 'react';
import { ArrowLeft, AlertTriangle, Files, CheckCircle2, Network, Table, Users, ChevronDown, ChevronRight } from 'lucide-react';
import { ProcessResponse, RelationshipIndexData } from '../types';
import { ResultTable } from '../components/ResultTable';
import { ExportButtons } from '../components/ExportButtons';
import { DataQualityInspector } from '../components/DataQualityInspector';
import { ExtractedTextCollapsible } from '../components/ExtractedTextCollapsible';
import { ProcessDetailsCollapsible } from '../components/ProcessDetailsCollapsible';
import { RelationshipDashboard } from '../components/RelationshipDashboard';
import { EntityMatchesView } from '../components/EntityMatchesView';

interface ResultPageProps {
  results: ProcessResponse[];
  activeIndex: number;
  onSelectIndex: (index: number) => void;
  onReset: () => void;
  batchId?: string;
  relationshipIndex?: RelationshipIndexData;
}

export const ResultPage: React.FC<ResultPageProps> = ({
  results,
  activeIndex,
  onSelectIndex,
  onReset,
  batchId,
  relationshipIndex
}) => {
  const [activeView, setActiveView] = useState<'datasets' | 'relationships' | 'entity_matches'>('datasets');
  const [isValidationExpanded, setIsValidationExpanded] = useState(false);
  const currentResult = results[activeIndex] || results[0];
  
  if (!currentResult) return null;

  const relCount = relationshipIndex?.summary?.relationships_found ?? relationshipIndex?.relationships?.length ?? 0;
  const matchCount = relationshipIndex?.entity_matches?.length ?? 0;
  const isBatch = results.length > 1 || relCount > 0 || matchCount > 0;

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

        {activeView === 'datasets' && (
          <ExportButtons taskId={currentResult.id} currentResult={currentResult} />
        )}
      </div>

      {/* Main 3-Tab View Switcher for Multi-File Batches */}
      {isBatch && (
        <div className="flex items-center gap-2 p-1.5 bg-slate-200/80 rounded-xl w-fit flex-wrap">
          {/* Tab 1: Cleaned Datasets */}
          <button
            onClick={() => setActiveView('datasets')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
              activeView === 'datasets'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Table className="w-4 h-4 text-blue-600" />
            <span>Cleaned Datasets ({results.length})</span>
          </button>

          {/* Tab 2: Cross-Entity Relationships */}
          <button
            onClick={() => setActiveView('relationships')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
              activeView === 'relationships'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-700 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <Network className={`w-4 h-4 ${activeView === 'relationships' ? 'text-white' : 'text-blue-600'}`} />
            <span>Relationships</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
              activeView === 'relationships' ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-800'
            }`}>
              {relCount} Edges
            </span>
          </button>

          {/* Tab 3: Same-Entity Matches */}
          <button
            onClick={() => setActiveView('entity_matches')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
              activeView === 'entity_matches'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-700 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <Users className={`w-4 h-4 ${activeView === 'entity_matches' ? 'text-white' : 'text-indigo-600'}`} />
            <span>Entity Matches</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
              activeView === 'entity_matches' ? 'bg-white/20 text-white' : 'bg-indigo-100 text-indigo-800'
            }`}>
              {matchCount} Matches
            </span>
          </button>
        </div>
      )}

      {/* VIEW 1: Cross-Entity Relationships */}
      {activeView === 'relationships' && (
        <RelationshipDashboard
          batchId={batchId}
          relationshipIndex={relationshipIndex}
        />
      )}

      {/* VIEW 2: Same-Entity Matches (Identity Resolution) */}
      {activeView === 'entity_matches' && (
        <EntityMatchesView
          entityMatches={relationshipIndex?.entity_matches || []}
        />
      )}

      {/* VIEW 3: Cleaned Dataset Views */}
      {activeView === 'datasets' && (
        <>
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
                  
                  const getEntityIcon = (type?: string) => {
                    switch (type?.toLowerCase()) {
                      case 'car': return '🚗';
                      case 'invoice': return '🧾';
                      case 'employee': return '💼';
                      case 'student':
                      case 'academic':
                      case 'syllabus':
                      case 'course': return '🎓';
                      case 'medical': return '🏥';
                      case 'store': return '🏪';
                      case 'item': return '📦';
                      case 'customer': return '👤';
                      case 'transaction': return '💳';
                      case 'mixed': return '🔀';
                      default: return '📁';
                    }
                  };

                  const entityIcon = getEntityIcon(res.entity_info?.entity_type);

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
                      {entityIcon && <span className="text-xs">{entityIcon}</span>}
                      <span className="truncate max-w-[180px]">{res.filename}</span>
                      {res.entity_info && res.entity_info.entity_type !== 'unknown' && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100/70 text-blue-800 font-semibold">
                          {res.entity_info.entity_type === 'mixed' ? 'Multiple Entity' : res.entity_info.entity_type.charAt(0).toUpperCase() + res.entity_info.entity_type.slice(1)}
                        </span>
                      )}
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/80 border border-slate-200 font-mono text-slate-600">
                        {ext}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Validation Warnings Dropdown / Collapsible */}
          {currentResult.errors && currentResult.errors.length > 0 && (
            <div className="bg-amber-50/80 border border-amber-200/90 rounded-xl overflow-hidden shadow-2xs transition-all">
              <button
                type="button"
                onClick={() => setIsValidationExpanded(!isValidationExpanded)}
                className="w-full flex items-center justify-between p-3.5 sm:px-4 text-left hover:bg-amber-100/50 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center border border-amber-300">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-amber-950">
                        Validation Warnings ({currentResult.errors.length})
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-amber-200/70 text-amber-900 border border-amber-300">
                        {isValidationExpanded ? 'Expanded' : 'Click to View'}
                      </span>
                    </div>
                    <p className="text-[11px] text-amber-800/80 mt-0.5">
                      {isValidationExpanded 
                        ? 'Items flagged for semantic review (all records preserved intact)'
                        : `Flagged ${currentResult.errors.length} formatting / value warnings across records`}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs font-semibold text-amber-900 bg-white/80 border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">
                  <span>{isValidationExpanded ? 'Collapse' : 'Show Details'}</span>
                  {isValidationExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-amber-800" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-amber-800" />
                  )}
                </div>
              </button>

              {isValidationExpanded && (
                <div className="px-4 pb-4 pt-2 border-t border-amber-200/70 bg-amber-50/40">
                  <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1 divide-y divide-amber-100">
                    {currentResult.errors.map((err, idx) => (
                      <div key={idx} className="pt-1.5 first:pt-0 flex items-start gap-2 text-xs text-amber-900">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        <div>
                          <span className="font-semibold text-amber-950">{err.field}:</span>{' '}
                          <span className="text-amber-800">{err.message}</span>
                          {err.raw_value !== undefined && err.raw_value !== null && (
                            <span className="ml-1.5 font-mono text-[10px] bg-white text-amber-900 px-1.5 py-0.2 rounded border border-amber-200">
                              raw: {String(err.raw_value)}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 12 Fundamentals & Data Quality Diagnostics Inspector */}
          {currentResult.cleansing_report && (
            <DataQualityInspector 
              audit={currentResult.cleansing_report.quality_audit} 
              cleansingReport={currentResult.cleansing_report}
            />
          )}

          {/* Structured Result Table with Retained Records count */}
          <ResultTable result={currentResult} />

          {/* Collapsible Extracted Text for unstructured docs */}
          {currentResult.classification === 'unstructured' && currentResult.raw_text && (
            <ExtractedTextCollapsible rawText={currentResult.raw_text} />
          )}

          {/* Collapsible Process Details */}
          <ProcessDetailsCollapsible steps={currentResult.steps} summary={currentResult.summary} />
        </>
      )}
    </div>
  );
};
