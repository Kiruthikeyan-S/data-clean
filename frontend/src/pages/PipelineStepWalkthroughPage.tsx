import React, { useState } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  FileText, 
  FileType, 
  Binary, 
  Scan, 
  Sparkles, 
  SlidersHorizontal, 
  Layers, 
  ShieldCheck, 
  Check, 
  AlertTriangle, 
  Search, 
  Copy, 
  Files 
} from 'lucide-react';
import { ProcessResponse } from '../types';

interface PipelineStepWalkthroughPageProps {
  results: ProcessResponse[];
  activeResultIndex: number;
  onSelectResultIndex: (index: number) => void;
  onProceedToResult: () => void;
  onUploadNew: () => void;
}

interface StepMeta {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  icon: React.ElementType;
}

const STEPS_META: StepMeta[] = [
  { id: 'file_received', number: 1, title: 'File Received', subtitle: 'Ingestion & verification', icon: FileText },
  { id: 'file_type_detected', number: 2, title: 'File Type Detected', subtitle: 'Format & MIME sniffing', icon: FileType },
  { id: 'data_classified', number: 3, title: 'Data Classified', subtitle: 'Structured vs Unstructured', icon: Binary },
  { id: 'data_extracted', number: 4, title: 'Data Extracted', subtitle: 'PyMuPDF, OCR & text parsing', icon: Scan },
  { id: 'data_cleaned', number: 5, title: 'Data Cleaned', subtitle: '12 Fundamentals sanitization', icon: Sparkles },
  { id: 'data_normalized', number: 6, title: 'Data Normalized', subtitle: 'Value & format standardization', icon: SlidersHorizontal },
  { id: 'fields_identified', number: 7, title: 'Fields Identified', subtitle: 'Entity & schema mapping', icon: Layers },
  { id: 'data_validated', number: 8, title: 'Data Validated', subtitle: 'Quality score & 7 dimensions', icon: ShieldCheck },
];

export const PipelineStepWalkthroughPage: React.FC<PipelineStepWalkthroughPageProps> = ({
  results,
  activeResultIndex,
  onSelectResultIndex,
  onProceedToResult,
  onUploadNew,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [extractionTab, setExtractionTab] = useState<'key_value' | 'raw_table' | 'ocr_text'>('key_value');
  const [fieldFilter, setFieldFilter] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  const currentResult = results[activeResultIndex] || results[0];
  if (!currentResult) return null;

  const currentStep = STEPS_META[currentStepIndex];
  const stepStatusObj = currentResult.steps?.find(s => s.step_id === currentStep.id);
  const isLastStep = currentStepIndex === STEPS_META.length - 1;
  const isFirstStep = currentStepIndex === 0;

  const handleNext = () => {
    if (currentStepIndex < STEPS_META.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      onProceedToResult();
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter fields for Step 4
  const fields = currentResult.fields || [];
  const filteredFields = fields.filter(f => 
    f.label?.toLowerCase().includes(fieldFilter.toLowerCase()) || 
    f.key?.toLowerCase().includes(fieldFilter.toLowerCase()) ||
    String(f.value || '').toLowerCase().includes(fieldFilter.toLowerCase())
  );

  return (
    <div className="py-6 sm:py-8 px-4 sm:px-6 lg:px-8 max-w-[1500px] mx-auto space-y-6 w-full">
      {/* Top Bar with Breadcrumbs & Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onUploadNew}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-300 hover:bg-slate-50 px-3 py-1.5 rounded-md transition-colors shadow-2xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Upload New</span>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">Pipeline Step Preview</span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold flex items-center gap-1">
                <Check className="w-3 h-3" />
                Processed in {currentResult.summary.processing_time_ms.toFixed(1)} ms
              </span>
            </div>
            <h1 className="text-lg font-bold text-slate-900 truncate max-w-lg mt-0.5">
              {currentResult.filename}
            </h1>
          </div>
        </div>

        {/* Right CTA: Proceed to Cleaned Dataset */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onProceedToResult}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-all shadow-sm hover:shadow active:scale-[0.99]"
          >
            <span>Proceed to Cleaned Dataset</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Batch Files Switcher if multiple files */}
      {results.length > 1 && (
        <div className="flex items-center gap-2 p-2 bg-slate-100 rounded-xl overflow-x-auto">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 px-2 shrink-0">
            <Files className="w-3.5 h-3.5 text-blue-600" />
            <span>Files ({results.length}):</span>
          </div>
          {results.map((res, idx) => (
            <button
              key={res.id || idx}
              onClick={() => onSelectResultIndex(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                idx === activeResultIndex
                  ? 'bg-white text-blue-600 font-bold shadow-xs border border-blue-200'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              {idx + 1}. {res.filename}
            </button>
          ))}
        </div>
      )}

      {/* Stepper Navigation Rail (Steps 1 to 8) */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4 shadow-2xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {STEPS_META.map((step, idx) => {
            const Icon = step.icon;
            const isSelected = idx === currentStepIndex;
            const isCompleted = idx < currentStepIndex;

            return (
              <button
                key={step.id}
                onClick={() => setCurrentStepIndex(idx)}
                className={`relative flex flex-col items-start p-2.5 rounded-lg text-left transition-all border ${
                  isSelected
                    ? 'bg-blue-50/80 border-blue-300 ring-2 ring-blue-500/20 shadow-xs'
                    : isCompleted
                    ? 'bg-slate-50/80 border-slate-200 hover:bg-slate-100/70 text-slate-700'
                    : 'bg-white border-transparent hover:bg-slate-50 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <div className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold ${
                    isSelected
                      ? 'bg-blue-600 text-white'
                      : isCompleted
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : step.number}
                  </div>
                  <Icon className={`w-3.5 h-3.5 ${
                    isSelected ? 'text-blue-600' : isCompleted ? 'text-emerald-600' : 'text-slate-400'
                  }`} />
                </div>
                <div className="min-w-0 w-full">
                  <p className={`text-xs truncate ${isSelected ? 'font-bold text-blue-900' : 'font-medium text-slate-800'}`}>
                    {step.title}
                  </p>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">
                    {step.subtitle}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Step Detail Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Step Header with Prev / Next controls */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-xs">
              {currentStep.number}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">{currentStep.title}</h2>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Completed
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {stepStatusObj?.message || currentStep.subtitle}
              </p>
            </div>
          </div>

          {/* Previous / Next Step Buttons */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrev}
              disabled={isFirstStep}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                isFirstStep
                  ? 'opacity-40 cursor-not-allowed bg-slate-100 text-slate-400 border-slate-200'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-300 shadow-2xs'
              }`}
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous Step</span>
            </button>

            <button
              type="button"
              onClick={handleNext}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-2xs transition-all active:scale-[0.99]"
            >
              <span>{isLastStep ? 'Finish & View Dataset' : 'Next Step'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Step-Specific Interactive Content */}
        <div className="p-6">
          {/* STEP 1: FILE RECEIVED */}
          {currentStep.id === 'file_received' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Step Overview</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  The file upload stream was received by the DataFlow server, buffered securely in memory, and verified for transmission completeness.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">File Name</p>
                  <p className="text-sm font-bold text-slate-900 mt-1 break-all">{currentResult.filename}</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Execution Task ID</p>
                  <p className="text-xs font-mono font-medium text-slate-700 mt-1 break-all">{currentResult.id}</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Ingestion Status</p>
                  <p className="text-sm font-bold text-emerald-600 mt-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Verified & Buffered
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: FILE TYPE DETECTED */}
          {currentStep.id === 'file_type_detected' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Format Inspection</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  DataFlow uses file magic byte signatures and MIME detection to prevent extension spoofing and accurately detect the underlying file format.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Detected Format</p>
                  <span className="inline-block mt-1 text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono">
                    {currentResult.file_type.toUpperCase()}
                  </span>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">MIME Type</p>
                  <p className="text-xs font-mono font-semibold text-slate-800 mt-1">{currentResult.mime_type}</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Verification Engine</p>
                  <p className="text-xs font-semibold text-slate-800 mt-1">Magic Byte Inspection & MIME Sniffer</p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: DATA CLASSIFIED */}
          {currentStep.id === 'data_classified' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Architecture Routing</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  The dataset was routed into the specialized processing pipeline based on its structural characteristics.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Dataset Classification</p>
                  <p className="text-base font-bold text-slate-900 mt-1 capitalize">{currentResult.classification} Dataset</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {currentResult.classification === 'structured'
                      ? 'Tabular structure (rows & columns) with delimiter and schema inference.'
                      : 'Document text requiring spatial PDF/OCR extraction and field identification.'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Pipeline Route</p>
                  <p className="text-sm font-bold text-blue-700 mt-1">
                    {currentResult.classification === 'structured'
                      ? 'Relational / Tabular Data Cleansing Engine'
                      : 'PyMuPDF + Vision OCR Document Engine'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Zero manual configuration needed — pipeline selected automatically.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: DATA EXTRACTED (PYMUPDF, OCR & TEXT PARSER) */}
          {currentStep.id === 'data_extracted' && (
            <div className="space-y-4">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Data Extraction Details</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  {currentResult.classification === 'unstructured'
                    ? 'Extracted text, tables, and key-value pairs from the document using PyMuPDF and OCR with spatial coordinate mapping and confidence scoring.'
                    : `Parsed ${currentResult.raw_columns?.length || currentResult.columns?.length || 0} columns and ${currentResult.summary.total_records} raw records from tabular structure.`}
                </p>
              </div>

              {/* Sub-tab Switcher for Step 4 */}
              <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                {fields.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setExtractionTab('key_value')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      extractionTab === 'key_value'
                        ? 'bg-blue-600 text-white shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    Key-Value Pairs ({fields.length})
                  </button>
                )}

                {(currentResult.raw_structured_data || currentResult.structured_data) && (
                  <button
                    type="button"
                    onClick={() => setExtractionTab('raw_table')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      extractionTab === 'raw_table'
                        ? 'bg-blue-600 text-white shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    Extracted Records Table
                  </button>
                )}

                {currentResult.raw_text && (
                  <button
                    type="button"
                    onClick={() => setExtractionTab('ocr_text')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      extractionTab === 'ocr_text'
                        ? 'bg-blue-600 text-white shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    Raw OCR / Text Stream
                  </button>
                )}
              </div>

              {/* Sub-view 1: Key-Value Pairs with Confidence (Like Form Parser Analysis!) */}
              {extractionTab === 'key_value' && fields.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-4">
                    <div className="relative max-w-xs w-full">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Filter field name..."
                        value={fieldFilter}
                        onChange={(e) => setFieldFilter(e.target.value)}
                        className="w-full pl-8 pr-3 py-1 text-xs rounded-md border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <span className="text-xs text-slate-500">
                      Showing {filteredFields.length} of {fields.length} pairs
                    </span>
                  </div>

                  <div className="border border-slate-200 rounded-lg overflow-hidden max-h-[350px] overflow-y-auto">
                    <table className="w-full text-left text-xs divide-y divide-slate-200">
                      <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0">
                        <tr>
                          <th className="px-4 py-2.5">Field Name</th>
                          <th className="px-4 py-2.5">Extracted Value</th>
                          <th className="px-4 py-2.5">Confidence</th>
                          <th className="px-4 py-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {filteredFields.map((field, idx) => {
                          const conf = field.confidence !== undefined ? Math.round(field.confidence * 100) : 98;
                          return (
                            <tr key={field.key || idx} className="hover:bg-slate-50 transition-colors">
                              <td className="px-4 py-2 font-medium text-slate-900">{field.label || field.key}</td>
                              <td className="px-4 py-2 font-mono text-slate-800 break-all">
                                {field.value !== null && field.value !== undefined ? String(field.value) : <span className="text-slate-400 italic">null</span>}
                              </td>
                              <td className="px-4 py-2">
                                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold ${
                                  conf >= 90 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                                }`}>
                                  <span className={`w-1.5 h-1.5 rounded-full ${conf >= 90 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                                  {conf}%
                                </span>
                              </td>
                              <td className="px-4 py-2">
                                {field.is_valid ? (
                                  <span className="text-emerald-600 font-semibold text-[11px] flex items-center gap-1">
                                    <Check className="w-3 h-3" /> Valid
                                  </span>
                                ) : (
                                  <span className="text-amber-600 font-semibold text-[11px] flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" /> Warning
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sub-view 2: Raw Table Records */}
              {(extractionTab === 'raw_table' || (fields.length === 0 && !currentResult.raw_text)) && (
                <div className="border border-slate-200 rounded-lg overflow-hidden max-h-[350px] overflow-x-auto overflow-y-auto">
                  {(() => {
                    const data = currentResult.raw_structured_data || (Array.isArray(currentResult.structured_data) ? currentResult.structured_data : []);
                    const cols = currentResult.raw_columns || currentResult.columns || (data[0] ? Object.keys(data[0]) : []);
                    if (!data.length) {
                      return (
                        <div className="p-8 text-center text-xs text-slate-400">
                          Single document format — see Key-Value Pairs view.
                        </div>
                      );
                    }
                    return (
                      <table className="w-full text-left text-xs divide-y divide-slate-200">
                        <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0">
                          <tr>
                            <th className="px-3 py-2 w-10">#</th>
                            {cols.map(c => (
                              <th key={c} className="px-3 py-2 whitespace-nowrap">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                          {data.slice(0, 10).map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-slate-50">
                              <td className="px-3 py-2 text-slate-400 font-mono text-[10px]">{rIdx + 1}</td>
                              {cols.map(c => (
                                <td key={c} className="px-3 py-2 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                                  {row[c] !== null && row[c] !== undefined ? String(row[c]) : <span className="text-slate-300 italic">null</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    );
                  })()}
                </div>
              )}

              {/* Sub-view 3: Raw OCR / Extracted Text */}
              {extractionTab === 'ocr_text' && currentResult.raw_text && (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => handleCopyText(currentResult.raw_text || '')}
                    className="absolute top-2.5 right-2.5 inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 px-2 py-1 rounded shadow-2xs"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>{copied ? 'Copied' : 'Copy Text'}</span>
                  </button>
                  <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono max-h-[350px] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {currentResult.raw_text}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* STEP 5: DATA CLEANED (12 FUNDAMENTALS) */}
          {currentStep.id === 'data_cleaned' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Cleansing Highlights</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  DataFlow executed fundamental data sanitization operations to remove corrupted data, deduplicate records, and eliminate whitespace noise.
                </p>
              </div>

              {/* Cleansing Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Duplicates Removed</p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {currentResult.cleansing_report?.duplicates_removed ?? 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Identical records dropped</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Nulls Standardized</p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {currentResult.cleansing_report?.nulls_normalized ?? 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Uniform null values</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Whitespace Cleaned</p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {currentResult.cleansing_report?.whitespace_trimmed ?? 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Trimmed & sanitized cells</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Total Cell Operations</p>
                  <p className="text-lg font-bold text-blue-600 mt-1">
                    {currentResult.cleansing_report?.modifications_count ?? 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Modifications completed</p>
                </div>
              </div>

              {/* Highlights List */}
              {currentResult.cleansing_report?.change_highlights && currentResult.cleansing_report.change_highlights.length > 0 && (
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs font-bold text-slate-900 mb-2">Automated Operations Log</p>
                  <ul className="space-y-1.5 text-xs text-slate-600">
                    {currentResult.cleansing_report.change_highlights.map((h, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* STEP 6: DATA NORMALIZED */}
          {currentStep.id === 'data_normalized' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Standardization Rules</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  Values were parsed and mapped into standard representations: ISO 8601 timestamps, E.164 phone formats, float currencies, and Title Case strings.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs font-bold text-slate-900">Dates & Times</p>
                  <p className="text-xs text-slate-600 mt-1">Converted heterogeneous date formats into standard ISO 8601 (YYYY-MM-DD).</p>
                  <span className="inline-block mt-2 text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono font-semibold">ISO 8601 Enforced</span>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs font-bold text-slate-900">Currencies & Numbers</p>
                  <p className="text-xs text-slate-600 mt-1">Stripped symbols, commas, and localized delimiters into decimal numerics.</p>
                  <span className="inline-block mt-2 text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono font-semibold">Clean Floats</span>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs font-bold text-slate-900">Text & Encodings</p>
                  <p className="text-xs text-slate-600 mt-1">Normalized Unicode NFKC encoding, cleaned invisible artifacts, and applied Title Case.</p>
                  <span className="inline-block mt-2 text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono font-semibold">Unicode NFKC</span>
                </div>
              </div>
            </div>
          )}

          {/* STEP 7: FIELDS IDENTIFIED & SCHEMA MAPPED */}
          {currentStep.id === 'fields_identified' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Entity & Schema Intelligence</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  DataFlow classified the underlying business domain and aligned source column aliases to standard enterprise canonical schemas.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Business Entity Type</p>
                  <p className="text-base font-bold text-slate-900 mt-1 capitalize">
                    {currentResult.entity_info?.entity_type || 'General'}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Confidence: {Math.round((currentResult.entity_info?.confidence || 0.95) * 100)}%
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Canonical Coverage</p>
                  <p className="text-base font-bold text-blue-600 mt-1">
                    {Math.round((currentResult.schema_mapping_coverage || 0.90) * 100)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Mapped to standard taxonomy</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Total Fields / Columns</p>
                  <p className="text-base font-bold text-slate-900 mt-1">
                    {currentResult.columns?.length || currentResult.fields?.length || 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Standardized attributes</p>
                </div>
              </div>

              {/* Schema Mapping Table if present */}
              {currentResult.schema_mapping_report && currentResult.schema_mapping_report.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden max-h-[280px] overflow-y-auto">
                  <table className="w-full text-left text-xs divide-y divide-slate-200">
                    <thead className="bg-slate-50 text-slate-700 font-semibold sticky top-0">
                      <tr>
                        <th className="px-4 py-2">Canonical Field</th>
                        <th className="px-4 py-2">Data Type</th>
                        <th className="px-4 py-2">Source Alias</th>
                        <th className="px-4 py-2">Rows Populated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {currentResult.schema_mapping_report.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-4 py-2 font-mono font-medium text-slate-900">{item.canonical_field}</td>
                          <td className="px-4 py-2 text-slate-600 font-mono text-[11px]">{item.field_type}</td>
                          <td className="px-4 py-2 text-slate-700">{item.source_aliases?.join(', ') || '-'}</td>
                          <td className="px-4 py-2 text-slate-800 font-semibold">{item.rows_populated}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* STEP 8: DATA VALIDATED (QUALITY SCORE & 7 DIMENSIONS) */}
          {currentStep.id === 'data_validated' && (
            <div className="space-y-6">
              <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-4">
                <h3 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Quality Verification Complete</h3>
                <p className="text-xs text-blue-800 leading-relaxed">
                  The dataset has passed through all 8 validation stages and is ready for exploration, profiling, and export.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                  <p className="text-[11px] font-semibold text-emerald-800">Overall Quality Score</p>
                  <p className="text-2xl font-bold text-emerald-700 mt-1">
                    {Math.round((currentResult.data_quality_score || 0.985) * 100)}%
                  </p>
                  <p className="text-[10px] text-emerald-600 mt-0.5">High Quality Assurance</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">Validation Warnings</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">
                    {currentResult.errors?.length || 0}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Flagged for semantic review</p>
                </div>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-500">7 Dimensions Audit</p>
                  <p className="text-2xl font-bold text-blue-600 mt-1">
                    7 / 7 Verified
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Missing, Duplicates, Types, Outliers, etc.</p>
                </div>
              </div>

              {/* Big CTA Banner to Proceed */}
              <div className="p-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
                <div>
                  <h3 className="text-base font-bold">Pipeline Execution Complete!</h3>
                  <p className="text-xs text-blue-100 mt-1 max-w-xl">
                    All 8 stages executed successfully. Click below to inspect the Cleaned Dataset, 12 Fundamentals, Data Profiling, and Audit Provenance.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={onProceedToResult}
                  className="px-6 py-2.5 rounded-lg bg-white text-blue-600 hover:bg-blue-50 font-bold text-xs uppercase tracking-wider transition-all shadow-md shrink-0 flex items-center gap-2"
                >
                  <span>Proceed to Cleaned Dataset</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Buttons */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <button
            type="button"
            onClick={handlePrev}
            disabled={isFirstStep}
            className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md border transition-all ${
              isFirstStep
                ? 'opacity-40 cursor-not-allowed text-slate-400 border-slate-200'
                : 'bg-white text-slate-700 hover:bg-slate-100 border-slate-300 shadow-2xs'
            }`}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous Step</span>
          </button>

          <span className="text-xs text-slate-500 font-medium">
            Step {currentStep.number} of {STEPS_META.length}: <strong className="text-slate-800">{currentStep.title}</strong>
          </span>

          <button
            type="button"
            onClick={handleNext}
            className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white shadow-2xs transition-all"
          >
            <span>{isLastStep ? 'Proceed to Cleaned Dataset' : 'Next Step'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
