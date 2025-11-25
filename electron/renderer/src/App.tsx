import { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import CalendarConfig from './components/CalendarConfig';
import ResultsDisplay from './components/ResultsDisplay';
import JuilliardLogo from './components/JuilliardLogo';
import { useSchedulerStore } from './lib/store';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const { isRunning, results, error } = useSchedulerStore();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b-2 border-black dark:border-white p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <JuilliardLogo />
            <h1 className="text-3xl font-bold">Audition Scheduler</h1>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="neo-button text-sm"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="container mx-auto p-6 space-y-8">
        <FileUpload />
        <CalendarConfig />
        
        {isRunning && (
          <div className="neo-card text-center">
            <p className="text-lg font-bold">Running scheduler...</p>
            <p className="text-sm opacity-70 mt-2">This may take a few moments</p>
          </div>
        )}

        {error && (
          <div className="neo-card border-red-500 bg-red-500/10">
            <p className="text-red-500 font-bold">Error</p>
            <p className="text-sm mt-2 font-mono">{error}</p>
          </div>
        )}

        {results && <ResultsDisplay />}
      </main>
    </div>
  );
}

export default App;

