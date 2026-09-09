import React from 'react';
import { FileSpreadsheet, FileCode, FileText } from 'lucide-react';
import { getExportUrl } from '../services/api';

interface ExportButtonsProps {
  taskId: string;
}

export const ExportButtons: React.FC<ExportButtonsProps> = ({ taskId }) => {
  const handleDownload = (format: 'json' | 'csv' | 'excel') => {
    const url = getExportUrl(taskId, format);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <button
        type="button"
        onClick={() => handleDownload('json')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 rounded-md transition-colors shadow-2xs"
      >
        <FileCode className="w-3.5 h-3.5 text-amber-600" />
        <span>Download JSON</span>
      </button>

      <button
        type="button"
        onClick={() => handleDownload('csv')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 rounded-md transition-colors shadow-2xs"
      >
        <FileText className="w-3.5 h-3.5 text-blue-600" />
        <span>Download CSV</span>
      </button>

      <button
        type="button"
        onClick={() => handleDownload('excel')}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 rounded-md transition-colors shadow-2xs"
      >
        <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
        <span>Download Excel</span>
      </button>
    </div>
  );
};
