import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, ArrowRight, X, FileText, Layers } from 'lucide-react';
import { ErrorMessage } from './ErrorMessage';

interface FileUploadProps {
  onProcess: (files: File[]) => void;
  isProcessing?: boolean;
}

const SUPPORTED_EXTENSIONS = [
  'jpg', 'jpeg', 'png', 'webp',
  'pdf', 'txt', 'docx', 'eml',
  'csv', 'xlsx', 'xls', 'json'
];

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB per file

export const FileUpload: React.FC<FileUploadProps> = ({ onProcess, isProcessing }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateSingleFile = (file: File): string | null => {
    if (file.size === 0) {
      return `"${file.name}" is empty (0 bytes).`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `"${file.name}" exceeds 50MB limit.`;
    }
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !SUPPORTED_EXTENSIONS.includes(ext)) {
      return `"${file.name}" has unsupported format (.${ext || 'unknown'}).`;
    }
    return null;
  };

  const addFiles = (newFiles: FileList | File[]) => {
    setError(null);
    const filesArray = Array.from(newFiles);
    if (filesArray.length === 0) return;

    const validNewFiles: File[] = [];
    const errors: string[] = [];

    for (const f of filesArray) {
      // Check duplicate in already selected
      if (selectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
        continue;
      }
      const valErr = validateSingleFile(f);
      if (valErr) {
        errors.push(valErr);
      } else {
        validNewFiles.push(f);
      }
    }

    if (errors.length > 0) {
      setError(errors.join(' '));
    }

    if (validNewFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validNewFiles]);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleProcessClick = () => {
    if (selectedFiles.length === 0) return;
    onProcess(selectedFiles);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    setError(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Title & Description */}
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          Convert & Clean Data into Structured Format
        </h1>
        <p className="text-slate-600 text-sm sm:text-base mt-2 max-w-lg mx-auto leading-relaxed">
          Upload single or multiple files (Store, Item, Customer, Receipts) to clean, standardize, and export.
        </p>
      </div>

      {/* Main Upload Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
        {/* Dropzone Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer transition-all ${
            isDragOver
              ? 'border-blue-500 bg-blue-50/50'
              : 'border-slate-300 hover:border-slate-400 bg-slate-50/50 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleInputChange}
            className="hidden"
            accept=".jpg,.jpeg,.png,.webp,.pdf,.txt,.docx,.eml,.csv,.xlsx,.xls,.json"
          />

          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3 border border-blue-100">
            <UploadCloud className="w-6 h-6" />
          </div>

          <p className="text-base font-semibold text-slate-800">
            {selectedFiles.length > 0 ? 'Add more files or drop here' : 'Drop files here or click to browse'}
          </p>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 font-medium">
            Upload 1 or multiple files simultaneously (e.g. Store, Items, Customer)
          </p>

          {/* Supported Formats Badges */}
          <div className="mt-4 pt-4 border-t border-slate-200/80 flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-500">
            <span className="font-semibold text-slate-600 mr-1">Formats:</span>
            {['CSV', 'XLSX', 'JSON', 'PDF', 'TXT', 'DOCX', 'EML', 'PNG', 'JPG'].map(fmt => (
              <span key={fmt} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[10px]">
                {fmt}
              </span>
            ))}
          </div>
        </div>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-900">
                  Selected Files ({selectedFiles.length})
                </span>
              </div>
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs font-semibold text-rose-600 hover:text-rose-700"
              >
                Clear All
              </button>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {selectedFiles.map((file, idx) => {
                const ext = file.name.split('.').pop()?.toUpperCase() || 'FILE';
                return (
                  <div
                    key={`${file.name}-${idx}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="w-6 h-6 rounded bg-blue-100 text-blue-800 font-mono font-bold text-[10px] flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                      <FileText className="w-4 h-4 text-slate-500 shrink-0" />
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-800 truncate">{file.name}</div>
                        <div className="text-[11px] text-slate-400">
                          {formatFileSize(file.size)} • <span className="font-mono text-slate-600">{ext}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      disabled={isProcessing}
                      className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-white transition-colors"
                      title="Remove file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Error message directly under upload */}
        {error && (
          <div className="mt-4">
            <ErrorMessage message={error} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Process Button */}
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={handleProcessClick}
            disabled={selectedFiles.length === 0 || isProcessing}
            className={`w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
              selectedFiles.length === 0 || isProcessing
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-xs active:scale-[0.99]'
            }`}
          >
            <span>
              {selectedFiles.length > 1
                ? `Process ${selectedFiles.length} Files Simultaneously`
                : selectedFiles.length === 1
                ? 'Process 1 File'
                : 'Process Data'}
            </span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

