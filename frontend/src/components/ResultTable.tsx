import React, { useState, useMemo } from 'react';
import { Search, ChevronLeft, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { ProcessResponse } from '../types';

interface ResultTableProps {
  result: ProcessResponse;
}

const PAGE_SIZE = 10;

export const ResultTable: React.FC<ResultTableProps> = ({ result }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const isStructuredList = result.classification === 'structured' && Array.isArray(result.structured_data);

  // Tabular data for structured files
  const rawRows: Array<Record<string, any>> = useMemo(() => {
    if (isStructuredList) {
      return (result.structured_data as Array<Record<string, any>>) || [];
    }
    return [];
  }, [result, isStructuredList]);

  const columns: string[] = useMemo(() => {
    if (isStructuredList) {
      return result.columns || (rawRows.length > 0 ? Object.keys(rawRows[0]) : []);
    }
    return ['Field', 'Standardized Value', 'Raw Extracted Value'];
  }, [result, isStructuredList, rawRows]);

  // Filter structured rows
  const filteredRows = useMemo(() => {
    if (!isStructuredList) return [];
    if (!searchQuery.trim()) return rawRows;
    const q = searchQuery.toLowerCase();
    return rawRows.filter(row =>
      Object.values(row).some(val => val !== null && String(val).toLowerCase().includes(q))
    );
  }, [rawRows, searchQuery, isStructuredList]);

  // Pagination for structured rows
  const totalPages = Math.ceil(filteredRows.length / PAGE_SIZE) || 1;
  const paginatedRows = useMemo(() => {
    if (!isStructuredList) return [];
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredRows.slice(start, start + PAGE_SIZE);
  }, [filteredRows, currentPage, isStructuredList]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Table Header / Metadata Bar */}
      <div className="p-5 sm:p-6 border-b border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Processed Data</h2>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-xs text-slate-500 font-medium">
            <div>
              <span className="text-slate-400 mr-1">File:</span>
              <span className="text-slate-800 font-semibold">{result.filename}</span>
            </div>
            <div className="border-l border-slate-200 pl-4">
              <span className="text-slate-400 mr-1">Input Type:</span>
              <span className="text-slate-800 capitalize">{result.classification}</span>
            </div>
            <div className="border-l border-slate-200 pl-4">
              <span className="text-slate-400 mr-1">Detected Type:</span>
              <span className="text-slate-800 uppercase">{result.file_type}</span>
            </div>
            {result.cleansing_report?.initial_rows !== undefined && result.classification === 'structured' && (
              <div className="border-l border-slate-200 pl-4">
                <span className="text-slate-400 mr-1">Retained Records:</span>
                <span className="font-semibold text-slate-800 bg-blue-50 text-blue-800 px-2 py-0.5 rounded border border-blue-100 font-mono text-[11px]">
                  {result.cleansing_report.final_rows} / {result.cleansing_report.initial_rows} initial
                </span>
              </div>
            )}
            <div className="border-l border-slate-200 pl-4 flex items-center gap-1.5">
              <span className="text-slate-400 mr-1">Status:</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" />
                Completed
              </span>
            </div>
          </div>
        </div>

        {/* Search Input for Structured Datasets */}
        {isStructuredList && rawRows.length > 0 && (
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search records..."
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-slate-800 placeholder-slate-400"
            />
          </div>
        )}
      </div>

      {/* Structured Multi-Record Table */}
      {isStructuredList ? (
        <div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50/80 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3 w-12 text-center text-slate-400">#</th>
                  {columns.map(col => (
                    <th key={col} className="px-5 py-3 font-semibold whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedRows.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length + 1} className="px-5 py-10 text-center text-slate-400 text-sm">
                      No matching records found.
                    </td>
                  </tr>
                ) : (
                  paginatedRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-5 py-3 text-xs text-center text-slate-400 font-mono">
                        {(currentPage - 1) * PAGE_SIZE + idx + 1}
                      </td>
                      {columns.map(col => {
                        const val = row[col];
                        return (
                          <td key={col} className="px-5 py-3 whitespace-nowrap text-xs text-slate-800">
                            {val === null || val === undefined ? (
                              <span className="text-slate-300 italic text-[11px]">null</span>
                            ) : (
                              String(val)
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer with Row count and Pagination */}
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <span className="font-semibold text-slate-700">{filteredRows.length > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0}</span> to{' '}
              <span className="font-semibold text-slate-700">
                {Math.min(currentPage * PAGE_SIZE, filteredRows.length)}
              </span>{' '}
              of <span className="font-semibold text-slate-700">{filteredRows.length}</span> records
              {searchQuery && ` (filtered from ${rawRows.length} total)`}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                  disabled={currentPage === 1}
                  className="p-1 rounded border border-slate-200 bg-white text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-2 font-medium text-slate-700">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="p-1 rounded border border-slate-200 bg-white text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                  aria-label="Next page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Unstructured Key-Value Entities Table */
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3 w-1/4">Field</th>
                <th className="px-6 py-3 w-2/5">Standardized Value</th>
                <th className="px-6 py-3 w-1/3">Raw Extracted Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {result.fields && result.fields.length > 0 ? (
                result.fields.map(field => {
                  const hasValue = field.value !== null && field.value !== undefined;
                  const hasRaw = field.raw_value !== null && field.raw_value !== undefined;

                  return (
                    <tr key={field.key} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-3.5 text-xs font-semibold text-slate-900 flex items-center gap-2">
                        {field.label}
                        {!field.is_valid && (
                          <span title={field.error_message || 'Format warning'}>
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500 inline" />
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-xs">
                        {hasValue ? (
                          <span className="font-medium text-slate-900 bg-blue-50/60 text-blue-900 px-2 py-0.5 rounded border border-blue-100 font-mono">
                            {String(field.value)}
                          </span>
                        ) : (
                          <span className="text-slate-300 italic text-xs">null</span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-xs text-slate-500">
                        {hasRaw ? (
                          <span className="font-mono text-slate-600">{String(field.raw_value)}</span>
                        ) : (
                          <span className="text-slate-300 italic text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-slate-400 text-xs">
                    No entities identified in document.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
