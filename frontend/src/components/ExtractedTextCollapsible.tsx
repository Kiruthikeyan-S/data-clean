import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Copy, Check } from 'lucide-react';

interface ExtractedTextCollapsibleProps {
  rawText?: string;
}

export const ExtractedTextCollapsible: React.FC<ExtractedTextCollapsibleProps> = ({ rawText }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!rawText) return null;

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <FileText className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-semibold text-slate-900">Extracted Text</span>
          <span className="text-xs text-slate-500 font-normal">
            ({rawText.length} characters)
          </span>
        </div>
        <div className="flex items-center gap-3">
          {isOpen && (
            <button
              type="button"
              onClick={handleCopy}
              className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium bg-slate-100 hover:bg-slate-200 px-2 py-1 rounded transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}
          {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-5 pb-5 pt-2 border-t border-slate-100">
          <pre className="bg-slate-50 text-slate-800 p-4 rounded-lg text-xs font-mono whitespace-pre-wrap break-words max-h-80 overflow-y-auto leading-relaxed border border-slate-200/80">
            {rawText}
          </pre>
        </div>
      )}
    </div>
  );
};
