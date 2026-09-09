import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, ArrowRight } from 'lucide-react';
import { FilePreview } from './FilePreview';
import { ErrorMessage } from './ErrorMessage';

interface FileUploadProps {
  onProcess: (file: File) => void;
  isProcessing?: boolean;
}

const SUPPORTED_EXTENSIONS = [
  'jpg', 'jpeg', 'png', 'webp',
  'pdf', 'txt', 'docx', 'eml',
  'csv', 'xlsx', 'xls', 'json'
];

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB

export const FileUpload: React.FC<FileUploadProps> = ({ onProcess, isProcessing }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (!file) {
      return 'No file selected.';
    }

    if (file.size === 0) {
      return 'The selected file is empty (0 bytes). Please choose a valid file.';
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return 'File size exceeds maximum allowed limit (50 MB).';
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !SUPPORTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format (.${ext || 'unknown'}). Supported formats include PDF, Images, DOCX, TXT, EML, CSV, Excel, and JSON.`;
    }

    return null;
  };

  const handleFile = (file: File) => {
    setError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
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
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleProcessClick = () => {
    if (!selectedFile) return;
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }
    onProcess(selectedFile);
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Title & Description */}
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          Convert Data into Clean Structured Format
        </h1>
        <p className="text-slate-600 text-sm sm:text-base mt-2 max-w-lg mx-auto leading-relaxed">
          Upload a file to extract, clean, standardize, validate, and export your data.
        </p>
      </div>

      {/* Main Upload Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
        {/* Dropzone Area */}
        {!selectedFile ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 sm:p-10 text-center cursor-pointer transition-all ${
              isDragOver
                ? 'border-blue-500 bg-blue-50/50'
                : 'border-slate-300 hover:border-slate-400 bg-slate-50/50 hover:bg-slate-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleInputChange}
              className="hidden"
              accept=".jpg,.jpeg,.png,.webp,.pdf,.txt,.docx,.eml,.csv,.xlsx,.xls,.json"
            />

            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 border border-blue-100">
              <UploadCloud className="w-6 h-6" />
            </div>

            <p className="text-base font-semibold text-slate-800">
              Drop your file here
            </p>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 font-medium">
              or click to browse
            </p>

            {/* Supported Formats Badges */}
            <div className="mt-6 pt-6 border-t border-slate-200/80 flex flex-col gap-2.5 items-center">
              <div className="flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-500">
                <span className="font-semibold text-slate-600 mr-1">Images:</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">JPG</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">PNG</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">WEBP</span>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-500">
                <span className="font-semibold text-slate-600 mr-1">Documents:</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">PDF</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">TXT</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">DOCX</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">EML</span>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-500">
                <span className="font-semibold text-slate-600 mr-1">Structured:</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">CSV</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">XLSX</span>
                <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">JSON</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <FilePreview file={selectedFile} onRemove={handleRemove} disabled={isProcessing} />
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
            disabled={!selectedFile || isProcessing}
            className={`w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
              !selectedFile || isProcessing
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-xs active:scale-[0.99]'
            }`}
          >
            <span>Process Data</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
