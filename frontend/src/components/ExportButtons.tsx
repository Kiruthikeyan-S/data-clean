import React, { useState } from 'react';
import { FileSpreadsheet, FileText, Download, Loader2 } from 'lucide-react';
import { getExportUrl } from '../services/api';
import { ProcessResponse } from '../types';

interface ExportButtonsProps {
  taskId: string;
  currentResult?: ProcessResponse;
}

export const ExportButtons: React.FC<ExportButtonsProps> = ({ taskId, currentResult }) => {
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);

  const triggerClientDownload = (blob: Blob, filename: string) => {
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    }, 200);
  };

  const handleDownload = async (format: 'pdf' | 'csv' | 'excel') => {
    setDownloadingFormat(format);
    const baseName = currentResult?.filename ? currentResult.filename.replace(/\.[^/.]+$/, "") : "dataset";
    const ext = format === 'excel' ? 'xlsx' : format;
    const fallbackFilename = `${baseName}_clean.${ext}`;

    try {
      const url = getExportUrl(taskId, format);
      const res = await fetch(url);
      
      if (res.ok) {
        const blob = await res.blob();
        let downloadName = fallbackFilename;
        const disposition = res.headers.get('Content-Disposition');
        if (disposition && disposition.includes('filename=')) {
          const match = disposition.match(/filename="?([^"]+)"?/);
          if (match && match[1]) {
            downloadName = match[1];
          }
        }
        triggerClientDownload(blob, downloadName);
        setDownloadingFormat(null);
        return;
      }
    } catch (err) {
      console.warn("Server export fetch error, attempting client fallback:", err);
    }

    // Client-side fallback if server endpoint is unreachable or result expired in memory
    try {
      if (currentResult && currentResult.structured_data) {
        const records = Array.isArray(currentResult.structured_data)
          ? currentResult.structured_data
          : [currentResult.structured_data];

        if (format === 'csv') {
          const cols = currentResult.columns || (records.length > 0 ? Object.keys(records[0]) : []);
          const headerLine = cols.join(',');
          const dataLines = records.map(r =>
            cols.map(c => {
              const val = r[c] === null || r[c] === undefined ? '' : String(r[c]);
              return `"${val.replace(/"/g, '""')}"`;
            }).join(',')
          );
          const csvContent = [headerLine, ...dataLines].join('\n');
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
          triggerClientDownload(blob, `${baseName}_clean.csv`);
        } else if (format === 'excel') {
          const cols = currentResult.columns || (records.length > 0 ? Object.keys(records[0]) : []);
          const tsvContent = [
            cols.join('\t'),
            ...records.map(r => cols.map(c => (r[c] === null || r[c] === undefined ? '' : String(r[c]))).join('\t'))
          ].join('\n');
          const blob = new Blob([tsvContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
          triggerClientDownload(blob, `${baseName}_clean.xls`);
        } else if (format === 'pdf') {
          // Trigger browser print window as clean PDF fallback
          window.print();
        }
      }
    } catch (fallbackErr) {
      console.error("Export fallback failed:", fallbackErr);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      {/* 1. PDF Download */}
      <button
        type="button"
        disabled={downloadingFormat !== null}
        onClick={() => handleDownload('pdf')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300 rounded-md transition-colors shadow-2xs disabled:opacity-50"
      >
        {downloadingFormat === 'pdf' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-600" />
        ) : (
          <FileText className="w-3.5 h-3.5 text-rose-600" />
        )}
        <span>Download PDF</span>
      </button>

      {/* 2. CSV Download */}
      <button
        type="button"
        disabled={downloadingFormat !== null}
        onClick={() => handleDownload('csv')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 rounded-md transition-colors shadow-2xs disabled:opacity-50"
      >
        {downloadingFormat === 'csv' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
        ) : (
          <Download className="w-3.5 h-3.5 text-blue-600" />
        )}
        <span>Download CSV</span>
      </button>

      {/* 3. Excel Download */}
      <button
        type="button"
        disabled={downloadingFormat !== null}
        onClick={() => handleDownload('excel')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 rounded-md transition-colors shadow-2xs disabled:opacity-50"
      >
        {downloadingFormat === 'excel' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
        ) : (
          <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
        )}
        <span>Download Excel</span>
      </button>
    </div>
  );
};

