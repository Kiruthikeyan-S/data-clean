import React from 'react';
import { FileText, FileSpreadsheet, Image as ImageIcon, Mail, FileCode, X } from 'lucide-react';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
  disabled?: boolean;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove, disabled }) => {
  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    if (['jpg', 'jpeg', 'png', 'webp', 'bmp'].includes(ext)) {
      return <ImageIcon className="w-6 h-6 text-blue-600" />;
    }
    if (['csv', 'xlsx', 'xls'].includes(ext)) {
      return <FileSpreadsheet className="w-6 h-6 text-emerald-600" />;
    }
    if (['json'].includes(ext)) {
      return <FileCode className="w-6 h-6 text-amber-600" />;
    }
    if (['eml', 'msg'].includes(ext)) {
      return <Mail className="w-6 h-6 text-indigo-600" />;
    }
    return <FileText className="w-6 h-6 text-blue-600" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileCategory = (filename: string): string => {
    const ext = filename.split('.').pop()?.toUpperCase() || 'FILE';
    return `${ext} Document`;
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3.5 min-w-0">
        <div className="w-11 h-11 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 shadow-2xs">
          {getFileIcon(file.name)}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate">{file.name}</p>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            {getFileCategory(file.name)} • {formatFileSize(file.size)}
          </p>
        </div>
      </div>
      {!disabled && (
        <button
          type="button"
          onClick={onRemove}
          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-md transition-colors"
          title="Remove file"
          aria-label="Remove file"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
