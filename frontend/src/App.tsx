import React, { useState } from 'react';
import { Header } from './components/Header';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultPage } from './pages/ResultPage';
import { ErrorMessage } from './components/ErrorMessage';
import { ProcessResponse, StepStatus } from './types';
import { processFile } from './services/api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'upload' | 'processing' | 'result'>('upload');
  
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [steps, setSteps] = useState<StepStatus[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleStartProcess = async (file: File) => {
    setCurrentFile(file);
    setErrorMessage(null);
    setCurrentPage('processing');
    setSteps([]);
    setCurrentStepIndex(0);
    setProgressPercent(0);
    setElapsedSeconds(0);

    const TOTAL_DURATION_MS = 10000; // 10 seconds comprehensive analysis
    const TOTAL_STAGES = 9;
    const INTERVAL_MS = 100;
    let elapsedMs = 0;

    // Start API request in parallel
    const apiPromise = processFile(file);

    // Run smooth 10-second inspection progress animation
    const progressTimer = setInterval(() => {
      elapsedMs += INTERVAL_MS;
      const currentElapsed = Math.min(elapsedMs, TOTAL_DURATION_MS);
      const pct = (currentElapsed / TOTAL_DURATION_MS) * 100;
      const stepIdx = Math.min(TOTAL_STAGES - 1, Math.floor((currentElapsed / TOTAL_DURATION_MS) * TOTAL_STAGES));

      setProgressPercent(pct);
      setElapsedSeconds(currentElapsed / 1000);
      setCurrentStepIndex(stepIdx);
    }, INTERVAL_MS);

    try {
      // Await both the backend processing and the 10-second inspection duration
      const [response] = await Promise.all([
        apiPromise,
        new Promise((resolve) => setTimeout(resolve, TOTAL_DURATION_MS))
      ]);

      clearInterval(progressTimer);
      setProgressPercent(100);
      setElapsedSeconds(10.0);
      setCurrentStepIndex(TOTAL_STAGES);
      setSteps(response.steps);
      setResult(response);

      // Brief transition delay so user sees final completed verification
      setTimeout(() => {
        setCurrentPage('result');
      }, 500);

    } catch (err: any) {
      clearInterval(progressTimer);
      setErrorMessage(err.message || 'An unexpected error occurred during processing.');
      setCurrentPage('upload');
    }
  };

  const handleReset = () => {
    setCurrentFile(null);
    setResult(null);
    setErrorMessage(null);
    setProgressPercent(0);
    setElapsedSeconds(0);
    setCurrentPage('upload');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc]">
      {/* Header Navigation */}
      <Header onNavigateUpload={handleReset} />

      {/* Global Error Banner if on upload page */}
      {errorMessage && currentPage === 'upload' && (
        <div className="max-w-2xl mx-auto px-4 mt-6 w-full">
          <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1">
        {currentPage === 'upload' && (
          <UploadPage onProcess={handleStartProcess} />
        )}

        {currentPage === 'processing' && (
          <ProcessingPage
            filename={currentFile?.name || 'File'}
            steps={steps}
            currentStepIndex={currentStepIndex}
            progressPercent={progressPercent}
            elapsedSeconds={elapsedSeconds}
          />
        )}

        {currentPage === 'result' && result && (
          <ResultPage result={result} onReset={handleReset} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        <div className="max-w-6xl mx-auto px-4">
          DataFlow Enterprise Data Processing Pipeline • Standardized Data Normalization & Validation
        </div>
      </footer>
    </div>
  );
};

export default App;
