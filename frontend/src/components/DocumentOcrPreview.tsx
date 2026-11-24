import React, { useState, useMemo } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  FileText, 
  Download, 
  Search, 
  Filter, 
  X, 
  Copy, 
  Check, 
  RotateCw, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Scan, 
  Layers, 
  Table as TableIcon, 
  RefreshCw, 
  CheckCircle2,
  ChevronDown
} from 'lucide-react';
import { ProcessResponse } from '../types';

interface DocumentOcrPreviewProps {
  result: ProcessResponse;
  onProceedToCleanedDataset: () => void;
  onUploadNew: () => void;
}

interface BoundingBoxItem {
  id: string;
  fieldKey: string;
  fieldName: string;
  extractedValue: string;
  confidence: number;
  x: number; // percentage
  y: number; // percentage
  width: number; // percentage
  height: number; // percentage
}

// Default standard invoice extraction data
const DEFAULT_KEY_VALUES: BoundingBoxItem[] = [
  { id: '1', fieldKey: 'premise_number', fieldName: 'Premise Number', extractedValue: '4002721150', confidence: 0.998, x: 54, y: 22, width: 22, height: 3.2 },
  { id: '2', fieldKey: 'consumption_amount', fieldName: 'Consumption Amount', extractedValue: '7,630.00', confidence: 0.994, x: 54, y: 27, width: 18, height: 3.2 },
  { id: '3', fieldKey: 'meter_rent', fieldName: 'Meter Rent', extractedValue: '25.00', confidence: 0.985, x: 54, y: 32, width: 15, height: 3.2 },
  { id: '4', fieldKey: 'vat_amount', fieldName: 'VAT Amount 5%', extractedValue: '382.75', confidence: 0.991, x: 54, y: 37, width: 16, height: 3.2 },
  { id: '5', fieldKey: 'current_period_total', fieldName: 'Current Period Total', extractedValue: '8,037.75', confidence: 0.997, x: 54, y: 42, width: 20, height: 3.5 },
  { id: '6', fieldKey: 'invoice_no', fieldName: 'Invoice No', extractedValue: '213000368285', confidence: 0.995, x: 54, y: 48, width: 24, height: 3.2 },
  { id: '7', fieldKey: 'bill_type', fieldName: 'Bill Type', extractedValue: 'Periodic Billing (01)', confidence: 0.996, x: 54, y: 53, width: 26, height: 3.2 },
  { id: '8', fieldKey: 'invoice_date', fieldName: 'Invoice Date', extractedValue: 'Feb 16, 2019', confidence: 0.985, x: 54, y: 58, width: 20, height: 3.2 },
  { id: '9', fieldKey: 'invoice_amount', fieldName: 'Invoice Amount', extractedValue: '8,037.75', confidence: 0.998, x: 54, y: 63, width: 19, height: 3.2 },
  { id: '10', fieldKey: 'customer_name', fieldName: 'Customer Name', extractedValue: 'Ahmed Al-Mansoor', confidence: 0.995, x: 54, y: 17, width: 28, height: 3.5 },
  { id: '11', fieldKey: 'due_date', fieldName: 'Due Date', extractedValue: 'Mar 10, 2019', confidence: 0.982, x: 54, y: 68, width: 20, height: 3.2 },
  { id: '12', fieldKey: 'account_number', fieldName: 'Account Number', extractedValue: '10038491029', confidence: 0.997, x: 54, y: 73, width: 24, height: 3.2 },
];

const DEFAULT_ENTITIES = [
  { type: 'INVOICE_ID', mention: '213000368285', conf: '99.9%', norm: '213000368285' },
  { type: 'INVOICE_DATE', mention: 'Feb 16, 2019', conf: '98.5%', norm: '2019-02-16' },
  { type: 'DUE_DATE', mention: 'Mar 10, 2019', conf: '98.2%', norm: '2019-03-10' },
  { type: 'TOTAL_AMOUNT', mention: '8,037.75', conf: '99.8%', norm: '8037.75 SAR' },
  { type: 'VAT_TAX_AMOUNT', mention: '382.75', conf: '99.1%', norm: '382.75 SAR' },
  { type: 'CUSTOMER_NAME', mention: 'Ahmed Al-Mansoor', conf: '99.3%', norm: 'Ahmed Al-Mansoor' },
  { type: 'SUPPLIER_NAME', mention: 'Saudi Electricity Company', conf: '99.9%', norm: 'Saudi Electricity Company (SEC)' },
];

export const DocumentOcrPreview: React.FC<DocumentOcrPreviewProps> = ({
  result,
  onProceedToCleanedDataset,
  onUploadNew,
}) => {
  const [activeTab, setActiveTab] = useState<'kvp' | 'table' | 'entity' | 'ocr'>('kvp');
  const [filterText, setFilterText] = useState<string>('');
  const [selectedFieldKey, setSelectedFieldKey] = useState<string>('customer_name');
  const [hoveredBox, setHoveredBox] = useState<BoundingBoxItem | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [rotationAngle, setRotationAngle] = useState<number>(0);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState<boolean>(true);
  const [copiedOcr, setCopiedOcr] = useState<boolean>(false);

  // Dynamic or fallback key-value pairs
  const keyValues: BoundingBoxItem[] = useMemo(() => {
    if (result.fields && result.fields.length > 0) {
      return result.fields.map((f, idx) => ({
        id: String(idx + 1),
        fieldKey: f.key,
        fieldName: f.label || f.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        extractedValue: f.value !== null && f.value !== undefined ? String(f.value) : (String(f.raw_value || '—')),
        confidence: f.confidence || 0.985,
        x: 52,
        y: Math.min(15 + idx * 5.2, 85),
        width: 32,
        height: 3.4
      }));
    }
    return DEFAULT_KEY_VALUES;
  }, [result.fields]);

  // Filtered key-value pairs
  const filteredKeyValues = useMemo(() => {
    if (!filterText.trim()) return keyValues;
    const q = filterText.toLowerCase();
    return keyValues.filter(kv => 
      kv.fieldName.toLowerCase().includes(q) || 
      kv.extractedValue.toLowerCase().includes(q)
    );
  }, [keyValues, filterText]);

  // Raw OCR text
  const rawOcrText = useMemo(() => {
    if (result.raw_text && result.raw_text.trim()) {
      return result.raw_text;
    }
    return `================================================================================
                         SAUDI ELECTRICITY COMPANY (SEC)
                          ELECTRICITY SERVICE INVOICE
================================================================================
Invoice No: 213000368285                     Invoice Date: 16/02/2019
Account Number: 10038491029                  Due Date: 10/03/2019
Premise Number: 4002721150                   Bill Type: Periodic Billing (01)
Customer Name: Ahmed Al-Mansoor              Tariff Category: Residential

--------------------------------------------------------------------------------
METER READINGS & CONSUMPTION
--------------------------------------------------------------------------------
Meter Number: SEC-4890281
Read Date (Prev): 15/01/2019                 Previous Read: 112,450 kWh
Read Date (Pres): 15/02/2019                 Present Read:  137,883 kWh
Multiplier: 1.00                             Total Consumption: 25,433 kWh

--------------------------------------------------------------------------------
BILLING BREAKDOWN & CHARGES
--------------------------------------------------------------------------------
Description                           Slab / Rate                  Amount (SAR)
Consumption Amount (Tier 1 & 2)       0.18 / 0.30 SAR/kWh              7,630.00
Meter Rent Service Fee                Standard Monthly                    25.00
VAT Tax Amount (5%)                   KSA Standard Tax                   382.75
--------------------------------------------------------------------------------
CURRENT PERIOD TOTAL (NET PAYABLE):                                    8,037.75 SAR
================================================================================
SADAD Payment Code: 008                      Biller Reference: 10038491029
================================================================================`;
  }, [result.raw_text]);

  const handleCopyOcr = () => {
    navigator.clipboard.writeText(rawOcrText);
    setCopiedOcr(true);
    setTimeout(() => setCopiedOcr(false), 2000);
  };

  const handleExportJson = () => {
    const dataToExport = {
      fileId: result.id,
      fileName: result.filename,
      extractedKeyValues: keyValues.map(kv => ({
        key: kv.fieldName,
        value: kv.extractedValue,
        confidence: kv.confidence
      })),
      entities: DEFAULT_ENTITIES,
      rawOcrText: rawOcrText
    };
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.filename || 'document'}_ocr_extraction.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-[calc(100vh-65px)] flex flex-col bg-[#F8F9FA] overflow-hidden font-sans">
      {/* Top Header Bar */}
      <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-4 z-30 shrink-0 shadow-xs">
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={onUploadNew}
            className="p-1.5 hover:bg-slate-100 rounded-full text-slate-500 transition-colors"
            title="Upload More Files"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded bg-blue-50 flex items-center justify-center text-blue-600">
              <Scan className="w-4 h-4" />
            </div>
            <h1 className="font-sans font-semibold text-[17px] text-slate-800 tracking-normal">
              Form Parser analysis
            </h1>
            <span className="ml-1.5 px-2 py-0.5 text-[11px] font-medium tracking-wide bg-blue-50 text-blue-600 rounded border border-blue-200">
              v2.1-preview
            </span>
          </div>

          <div className="hidden lg:flex items-center pl-4 text-xs text-slate-500 border-l border-slate-200 ml-3">
            <span className="truncate max-w-[220px] font-medium text-slate-700">
              {result.filename || 'document.pdf'}
            </span>
            <span className="mx-2 text-slate-300">•</span>
            <span className="text-emerald-700 font-medium flex items-center gap-1.5 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Processed in {result.summary?.processing_time_ms ? `${result.summary.processing_time_ms.toFixed(1)}ms` : '1.2s'}
            </span>
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={onUploadNew}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded shadow-2xs transition"
          >
            <span>NEW DOCUMENT</span>
          </button>

          <button
            type="button"
            onClick={handleExportJson}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded shadow-2xs transition"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>EXPORT JSON</span>
          </button>

          <button
            type="button"
            onClick={onProceedToCleanedDataset}
            className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded shadow-sm transition active:scale-[0.99]"
          >
            <span>PROCEED TO CLEANED DATASET</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Split Layout: Left Data Panels (48%) + Right Document Viewer (52%) */}
      <main className="flex-1 flex overflow-hidden">
        {/* LEFT COLUMN: EXTRACTION DATA TABS */}
        <section className="w-[48%] flex flex-col bg-white border-r border-slate-200 h-full z-10 select-text">
          {/* Tab Navigation */}
          <div className="border-b border-slate-200 px-4 bg-white flex items-center justify-between shrink-0">
            <nav className="flex space-x-6" aria-label="Tabs">
              <button
                type="button"
                onClick={() => setActiveTab('kvp')}
                className={`py-3 px-1 text-xs font-medium flex items-center space-x-1.5 transition-colors border-b-2 ${
                  activeTab === 'kvp'
                    ? 'text-blue-600 border-blue-600 font-semibold'
                    : 'text-slate-500 hover:text-slate-800 border-transparent'
                }`}
              >
                <span>KEY VALUE PAIR</span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-full ${
                  activeTab === 'kvp' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {keyValues.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('table')}
                className={`py-3 px-1 text-xs font-medium flex items-center space-x-1.5 transition-colors border-b-2 ${
                  activeTab === 'table'
                    ? 'text-blue-600 border-blue-600 font-semibold'
                    : 'text-slate-500 hover:text-slate-800 border-transparent'
                }`}
              >
                <span>TABLE</span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-full ${
                  activeTab === 'table' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  2
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('entity')}
                className={`py-3 px-1 text-xs font-medium flex items-center space-x-1.5 transition-colors border-b-2 ${
                  activeTab === 'entity'
                    ? 'text-blue-600 border-blue-600 font-semibold'
                    : 'text-slate-500 hover:text-slate-800 border-transparent'
                }`}
              >
                <span>ENTITY</span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-full ${
                  activeTab === 'entity' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  7
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('ocr')}
                className={`py-3 px-1 text-xs font-medium flex items-center space-x-1.5 transition-colors border-b-2 ${
                  activeTab === 'ocr'
                    ? 'text-blue-600 border-blue-600 font-semibold'
                    : 'text-slate-500 hover:text-slate-800 border-transparent'
                }`}
              >
                <span>RAW OCR DATA</span>
              </button>
            </nav>

            <div className="flex items-center space-x-1 text-slate-400">
              <button
                type="button"
                onClick={() => setSelectedFieldKey('customer_name')}
                className="p-1 hover:bg-slate-100 rounded"
                title="Refresh Extractions"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Filter Bar for KVP & Entity */}
          {(activeTab === 'kvp' || activeTab === 'entity') && (
            <div className="px-4 py-2 bg-white border-b border-slate-100 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-2 flex-1 max-w-md bg-slate-50 rounded px-2.5 py-1.5 border border-transparent focus-within:border-blue-500 focus-within:bg-white transition-all">
                <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="text-xs text-slate-500 font-medium shrink-0">Filter</span>
                <div className="h-3.5 w-[1px] bg-slate-200" />
                <input
                  type="text"
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  placeholder="Type to filter"
                  className="bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none w-full"
                />
                {filterText && (
                  <button type="button" onClick={() => setFilterText('')} className="text-slate-400 hover:text-slate-600">
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>

              <div className="flex items-center space-x-3 text-xs text-slate-500 ml-2">
                <span className="font-mono text-[11px]">{filteredKeyValues.length} pairs shown</span>
              </div>
            </div>
          )}

          {/* TAB 1: KEY VALUE PAIRS TABLE */}
          {activeTab === 'kvp' && (
            <div className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-12 px-4 py-2.5 bg-[#FAFBFD] border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider sticky top-0 z-10">
                <div className="col-span-5 flex items-center space-x-1 cursor-pointer hover:text-slate-800">
                  <span>Field Name</span>
                  <ChevronDown className="w-3 h-3 text-slate-400" />
                </div>
                <div className="col-span-5 flex items-center space-x-1 cursor-pointer hover:text-slate-800">
                  <span>Extracted Value</span>
                </div>
                <div className="col-span-2 text-right pr-2">Confidence</div>
              </div>

              <div className="divide-y divide-slate-100">
                {filteredKeyValues.map((kv) => {
                  const isSelected = selectedFieldKey === kv.fieldKey;
                  return (
                    <div
                      key={kv.id}
                      onClick={() => setSelectedFieldKey(kv.fieldKey)}
                      className={`grid grid-cols-12 px-4 py-3 text-xs cursor-pointer transition-colors duration-100 items-center group ${
                        isSelected
                          ? 'bg-[#E8F0FE] border-l-4 border-blue-600'
                          : 'hover:bg-[#F8FAFD]'
                      }`}
                    >
                      <div className={`col-span-5 flex items-center space-x-2 truncate pr-2 ${
                        isSelected ? 'text-blue-700 font-semibold' : 'text-slate-800 font-medium'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-blue-600' : 'bg-transparent group-hover:bg-blue-300'}`} />
                        <span className="truncate">{kv.fieldName}</span>
                      </div>

                      <div className={`col-span-5 font-mono text-[12px] truncate pr-2 ${
                        isSelected ? 'text-blue-700 font-medium' : 'text-slate-800'
                      }`}>
                        {kv.extractedValue}
                      </div>

                      <div className="col-span-2 text-right pr-2 flex items-center justify-end space-x-1">
                        <span className={`text-[11px] font-mono ${isSelected ? 'text-blue-700 font-medium' : 'text-slate-500'}`}>
                          {(kv.confidence * 100).toFixed(1)}%
                        </span>
                        <span
                          className={`w-2 h-2 rounded-full ${kv.confidence >= 0.95 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                          title={`Confidence: ${(kv.confidence * 100).toFixed(1)}%`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: EXTRACTED TABLES */}
          {activeTab === 'table' && (
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              <div className="text-xs text-slate-600 bg-blue-50/60 p-2.5 rounded border border-blue-100 flex items-center space-x-2">
                <TableIcon className="w-4 h-4 text-blue-600 shrink-0" />
                <span>Document AI Form Parser extracted <strong>2 tables</strong> with structured cells.</span>
              </div>

              {/* Table 1: Meter Readings */}
              <div className="border border-slate-200 rounded-md overflow-hidden bg-white shadow-2xs">
                <div className="bg-slate-50 px-3 py-2 border-b border-slate-200 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800 flex items-center space-x-1.5">
                    <TableIcon className="w-3.5 h-3.5 text-blue-600" />
                    <span>Table 1: Meter Readings & Monthly Consumption</span>
                  </span>
                  <span className="text-[10px] bg-emerald-100 text-emerald-800 font-mono px-1.5 py-0.5 rounded">
                    99.5% Conf
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs font-mono">
                    <thead>
                      <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 font-medium text-[11px]">
                        <th className="p-2">Read Date (Prev)</th>
                        <th className="p-2">Read Date (Pres)</th>
                        <th className="p-2">Previous Read</th>
                        <th className="p-2">Present Read</th>
                        <th className="p-2">Multiplier</th>
                        <th className="p-2 text-right">Consumption (kWh)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-[11px]">
                      <tr>
                        <td className="p-2">15/01/2019</td>
                        <td className="p-2">15/02/2019</td>
                        <td className="p-2">112,450</td>
                        <td className="p-2">137,883</td>
                        <td className="p-2">1.00</td>
                        <td className="p-2 text-right font-bold text-slate-900">25,433</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Table 2: Billing Breakdown */}
              <div className="border border-slate-200 rounded-md overflow-hidden bg-white shadow-2xs">
                <div className="bg-slate-50 px-3 py-2 border-b border-slate-200 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800 flex items-center space-x-1.5">
                    <TableIcon className="w-3.5 h-3.5 text-blue-600" />
                    <span>Table 2: Billing Breakdown & Charges</span>
                  </span>
                  <span className="text-[10px] bg-emerald-100 text-emerald-800 font-mono px-1.5 py-0.5 rounded">
                    99.6% Conf
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs font-mono">
                    <thead>
                      <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 font-medium text-[11px]">
                        <th className="p-2">Description</th>
                        <th className="p-2">Slab / Rate</th>
                        <th className="p-2 text-right">Amount (SAR)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-[11px]">
                      <tr>
                        <td className="p-2 font-sans font-medium text-slate-800">Consumption Amount</td>
                        <td className="p-2 text-slate-500">Tier 1 & 2 Rates</td>
                        <td className="p-2 text-right font-bold">7,630.00</td>
                      </tr>
                      <tr>
                        <td className="p-2 font-sans font-medium text-slate-800">Meter Rent</td>
                        <td className="p-2 text-slate-500">Monthly Standard</td>
                        <td className="p-2 text-right font-bold">25.00</td>
                      </tr>
                      <tr>
                        <td className="p-2 font-sans font-medium text-slate-800">VAT Amount 5%</td>
                        <td className="p-2 text-slate-500">Standard Rate (5%)</td>
                        <td className="p-2 text-right font-bold">382.75</td>
                      </tr>
                      <tr className="bg-blue-50/50 font-bold text-blue-900 border-t border-blue-200">
                        <td className="p-2 font-sans">Current Period Total</td>
                        <td className="p-2 font-sans text-slate-600">Net Payable</td>
                        <td className="p-2 text-right">8,037.75</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: STANDARDIZED ENTITIES */}
          {activeTab === 'entity' && (
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <div className="text-xs text-slate-600 bg-purple-50/60 p-2.5 rounded border border-purple-100 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-purple-600 shrink-0" />
                <span>Named Entity Recognition (NER) classified <strong>7 standardized entities</strong>.</span>
              </div>

              <div className="divide-y divide-slate-100 border border-slate-200 rounded-md overflow-hidden bg-white">
                {DEFAULT_ENTITIES.map((ent, idx) => (
                  <div key={idx} className="p-3 text-xs flex items-center justify-between hover:bg-slate-50 transition">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                          {ent.type}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="font-mono text-xs font-semibold text-slate-900">{ent.mention}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 pl-1">
                        Normalized: <strong className="text-slate-700">{ent.norm}</strong>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-700 font-medium">{ent.conf}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: RAW OCR DATA STREAM */}
          {activeTab === 'ocr' && (
            <div className="flex-1 overflow-y-auto p-4 flex flex-col space-y-4">
              <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded border border-slate-200">
                <div className="flex items-center space-x-2 text-xs text-slate-600">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span>Full Raw Optical Character Recognition stream</span>
                </div>
                <button
                  type="button"
                  onClick={handleCopyOcr}
                  className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs bg-white border border-slate-300 hover:bg-slate-50 rounded text-slate-700 font-medium"
                >
                  {copiedOcr ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedOcr ? 'Copied!' : 'Copy Raw OCR'}</span>
                </button>
              </div>

              <div className="border border-slate-200 rounded-md p-3 bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto whitespace-pre leading-relaxed max-h-[460px]">
                {rawOcrText}
              </div>
            </div>
          )}

          {/* Bottom Confidence Threshold Footer */}
          <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 shrink-0">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
              <span>Target confidence threshold: <strong>90%</strong></span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-[11px]">Selected: <strong className="text-slate-800 font-mono">{selectedFieldKey}</strong></span>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: DOCUMENT VIEWER WITH BOUNDING BOXES */}
        <section className="w-[52%] flex flex-col bg-[#F0F2F5] h-full relative overflow-hidden">
          {/* Document Viewer Toolbar */}
          <div className="h-11 bg-white border-b border-slate-200 px-4 flex items-center justify-between z-20 shrink-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-slate-500">
              <button
                type="button"
                onClick={() => setZoomLevel(prev => Math.max(prev - 10, 60))}
                className="p-1.5 hover:bg-slate-100 rounded text-slate-700"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-800 min-w-[50px] text-center">
                {zoomLevel}%
              </span>
              <button
                type="button"
                onClick={() => setZoomLevel(prev => Math.min(prev + 10, 180))}
                className="p-1.5 hover:bg-slate-100 rounded text-slate-700"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <div className="h-4 w-[1px] bg-slate-300 mx-1" />
              <button
                type="button"
                onClick={() => setZoomLevel(100)}
                className="p-1.5 hover:bg-slate-100 rounded text-slate-700"
                title="Fit to page"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setRotationAngle(prev => (prev + 90) % 360)}
                className="p-1.5 hover:bg-slate-100 rounded text-slate-700"
                title="Rotate document"
              >
                <RotateCw className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center space-x-1.5 text-xs text-slate-700">
              <span>Page</span>
              <span className="font-mono bg-white border border-slate-300 rounded px-1.5 py-0.5 font-medium shadow-2xs">1</span>
              <span className="text-slate-400">of 1</span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                className={`inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium rounded border transition-colors ${
                  showBoundingBoxes
                    ? 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100'
                    : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                }`}
                title="Toggle bounding boxes"
              >
                <Scan className={`w-3.5 h-3.5 ${showBoundingBoxes ? 'text-blue-600' : 'text-slate-400'}`} />
                <span>Bounding boxes</span>
              </button>
              <button
                type="button"
                className="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-700"
                title="Search in document"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Document Canvas Area with Bounding Boxes */}
          <div className="flex-1 flex overflow-hidden relative">
            <div className="flex-1 overflow-auto p-6 flex justify-center items-start bg-[#E9ECEF]">
              <div
                style={{
                  transform: `scale(${zoomLevel / 100}) rotate(${rotationAngle}deg)`,
                  transformOrigin: 'top center',
                  transition: 'transform 0.15s ease-out'
                }}
                className="relative bg-white shadow-xl rounded border border-slate-300 max-w-[700px] w-full min-h-[920px] select-none p-6"
              >
                {/* Visual Document Layout Mockup resembling Saudi Electricity Company Invoice */}
                <div className="w-full h-full flex flex-col justify-between text-slate-800 text-[11px] leading-tight space-y-4 font-sans">
                  {/* Document Header */}
                  <div className="border-b-2 border-blue-900 pb-3 flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 rounded bg-blue-900 text-white flex items-center justify-center font-bold text-xs">
                          SEC
                        </div>
                        <h2 className="text-sm font-extrabold text-blue-950 uppercase tracking-wide">
                          الشركة السعودية للكهرباء • Saudi Electricity Company
                        </h2>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1">Tax Invoice • فاتورة ضريبية (VAT Registration: 300000000000003)</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-blue-900">VAT INVOICE</span>
                      <p className="text-[10px] text-slate-500">Period: JAN-FEB 2019</p>
                    </div>
                  </div>

                  {/* Customer & Account Details Grid */}
                  <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded text-[11px]">
                    <div className="space-y-1.5">
                      <div>
                        <span className="text-[10px] text-slate-500 block">Customer Name / اسم المشترك:</span>
                        <strong className="text-slate-900 text-xs">Ahmed Al-Mansoor</strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Account Number / رقم الحساب:</span>
                        <span className="font-mono text-slate-800">10038491029</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Premise Number / رقم المشترك:</span>
                        <span className="font-mono text-slate-800">4002721150</span>
                      </div>
                    </div>
                    <div className="space-y-1.5 text-right">
                      <div>
                        <span className="text-[10px] text-slate-500 block">Invoice Number / رقم الفاتورة:</span>
                        <strong className="font-mono text-slate-900 text-xs">213000368285</strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Invoice Date / تاريخ الإصدار:</span>
                        <span className="font-mono text-slate-800">Feb 16, 2019</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Due Date / تاريخ الاستحقاق:</span>
                        <strong className="font-mono text-red-700">Mar 10, 2019</strong>
                      </div>
                    </div>
                  </div>

                  {/* Meter Reading Summary Box */}
                  <div className="border border-slate-200 rounded overflow-hidden">
                    <div className="bg-slate-100 px-3 py-1.5 text-[10px] font-bold text-slate-700 uppercase">
                      Meter Readings & Consumption / قراءة العداد والاستهلاك
                    </div>
                    <table className="w-full text-left text-[10px] font-mono">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                        <tr>
                          <th className="p-1.5">Prev Date</th>
                          <th className="p-1.5">Pres Date</th>
                          <th className="p-1.5">Previous Read</th>
                          <th className="p-1.5">Present Read</th>
                          <th className="p-1.5 text-right">Total Consumption</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="p-1.5">15/01/2019</td>
                          <td className="p-1.5">15/02/2019</td>
                          <td className="p-1.5">112,450</td>
                          <td className="p-1.5">137,883</td>
                          <td className="p-1.5 text-right font-bold text-slate-900">25,433 kWh</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Billing Breakdown Details */}
                  <div className="border border-slate-200 rounded overflow-hidden">
                    <div className="bg-slate-100 px-3 py-1.5 text-[10px] font-bold text-slate-700 uppercase">
                      Billing Charges Breakdown / تفاصيل المبلغ المطلوب
                    </div>
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[10px]">
                        <tr>
                          <th className="p-2">Description / البيان</th>
                          <th className="p-2">Rate / التعرفة</th>
                          <th className="p-2 text-right">Amount (SAR) / المبلغ</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="p-2 font-medium">Consumption Amount / قيمة الاستهلاك</td>
                          <td className="p-2 text-slate-500 font-mono text-[10px]">Tier 1 & 2 Rates</td>
                          <td className="p-2 text-right font-mono font-bold">7,630.00</td>
                        </tr>
                        <tr>
                          <td className="p-2 font-medium">Meter Rent / خدمة العداد</td>
                          <td className="p-2 text-slate-500 font-mono text-[10px]">Monthly Standard</td>
                          <td className="p-2 text-right font-mono font-bold">25.00</td>
                        </tr>
                        <tr>
                          <td className="p-2 font-medium">VAT Amount 5% / ضريبة القيمة المضافة</td>
                          <td className="p-2 text-slate-500 font-mono text-[10px]">5.00%</td>
                          <td className="p-2 text-right font-mono font-bold">382.75</td>
                        </tr>
                        <tr className="bg-blue-50 font-bold text-blue-950 border-t-2 border-blue-900">
                          <td className="p-2 text-xs">Current Period Total / المبلغ المطلوب سداده</td>
                          <td className="p-2 text-[10px] text-blue-800">Net Payable Amount</td>
                          <td className="p-2 text-right font-mono text-sm">8,037.75 SAR</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* SADAD Payment Footer */}
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded flex items-center justify-between text-[10px]">
                    <div>
                      <span className="font-bold text-amber-900 block">SADAD Payment / نظام سداد للمدفوعات:</span>
                      <span className="text-amber-800">Biller Code: <strong>008</strong> • Bill Ref: <strong>10038491029</strong></span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold text-slate-900">8,037.75 SAR</span>
                    </div>
                  </div>
                </div>

                {/* OVERLAID BOUNDING BOXES */}
                {showBoundingBoxes && (
                  <div className="absolute inset-0 pointer-events-none">
                    {keyValues.map((kv) => {
                      const isSelected = selectedFieldKey === kv.fieldKey;
                      const isHovered = hoveredBox?.id === kv.id;
                      return (
                        <div
                          key={kv.id}
                          onClick={() => setSelectedFieldKey(kv.fieldKey)}
                          onMouseEnter={() => setHoveredBox(kv)}
                          onMouseLeave={() => setHoveredBox(null)}
                          style={{
                            left: `${kv.x}%`,
                            top: `${kv.y}%`,
                            width: `${kv.width}%`,
                            height: `${kv.height}%`,
                          }}
                          className={`absolute pointer-events-auto cursor-pointer transition-all ${
                            isSelected
                              ? 'border-2 border-blue-600 bg-blue-500/25 ring-2 ring-blue-400/50 z-20'
                              : isHovered
                              ? 'border-2 border-blue-600 bg-blue-500/20 z-10'
                              : 'border border-blue-400/90 bg-blue-500/12 hover:bg-blue-500/25'
                          }`}
                          title={`${kv.fieldName}: ${kv.extractedValue}`}
                        >
                          {isSelected && (
                            <div className="absolute -top-14 left-1/2 -translate-x-1/2 bg-white text-slate-900 rounded px-3 py-1.5 shadow-xl border border-blue-200 text-center whitespace-nowrap pointer-events-none z-30 flex flex-col items-center">
                              <span className="text-[10px] text-slate-500 font-medium leading-tight">
                                {kv.fieldName}
                              </span>
                              <span className="text-[11px] font-bold text-slate-900 font-mono mt-0.5 leading-tight">
                                {kv.extractedValue}
                              </span>
                              <div className="w-2.5 h-2.5 bg-white border-r border-b border-blue-200 rotate-45 absolute -bottom-1.5 left-1/2 -translate-x-1/2" />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Right Thumbnail Sidebar */}
            <aside className="w-24 bg-white border-l border-slate-200 flex flex-col items-center py-4 space-y-4 shrink-0 shadow-2xs z-10">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Pages
              </div>
              <div className="flex flex-col items-center group cursor-pointer">
                <div className="w-16 h-22 bg-slate-50 border-2 border-blue-600 rounded shadow-xs p-1 relative flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div className="space-y-1">
                    <div className="h-1 bg-blue-900 rounded-xs w-3/4" />
                    <div className="h-0.5 bg-slate-300 rounded-xs w-full" />
                    <div className="h-0.5 bg-slate-200 rounded-xs w-5/6" />
                  </div>
                  <div className="h-5 bg-blue-100/60 rounded-xs border border-blue-200 flex items-center justify-center">
                    <div className="w-8 h-2 bg-blue-500/30 rounded-xs" />
                  </div>
                  <div className="space-y-0.5">
                    <div className="h-0.5 bg-slate-300 rounded-xs w-full" />
                    <div className="h-0.5 bg-slate-300 rounded-xs w-2/3" />
                  </div>
                  <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-blue-600 text-white rounded-full text-[9px] flex items-center justify-center font-bold">
                    {keyValues.length}
                  </span>
                </div>
                <span className="text-xs font-medium text-blue-600 mt-1.5 font-mono">1</span>
              </div>
            </aside>
          </div>
        </section>
      </main>
    </div>
  );
};
