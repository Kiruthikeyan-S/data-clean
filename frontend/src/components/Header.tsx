import React from 'react';
import { Layers, UploadCloud } from 'lucide-react';

interface HeaderProps {
  onNavigateUpload: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNavigateUpload }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <button 
          onClick={onNavigateUpload}
          className="flex items-center gap-2.5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 rounded-md"
        >
          <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold shadow-sm">
            <Layers className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold text-slate-900 leading-none tracking-tight">DataFlow</span>
            <span className="text-xs text-slate-500 font-medium">Data Cleansing & Extraction</span>
          </div>
        </button>

        {/* Navigation - Only Upload */}
        <nav className="flex items-center">
          <button
            onClick={onNavigateUpload}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-semibold rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors border border-blue-100"
          >
            <UploadCloud className="w-4 h-4 text-blue-600" />
            <span>Upload</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
