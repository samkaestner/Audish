import { useState, useEffect, useRef } from 'react';
import FileUpload from './components/FileUpload';
import CalendarConfig from './components/CalendarConfig';
import ResultsDisplay from './components/ResultsDisplay';
import SettingsDialog from './components/SettingsDialog';
import JuilliardLogo from './components/JuilliardLogo';
import { useSchedulerStore } from './lib/store';
import { Button } from './components/ui/button';
import { Card, CardContent } from './components/ui/card';
import { Progress } from './components/ui/progress';
import { Moon, Sun, Settings } from 'lucide-react';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const { isRunning, results, error } = useSchedulerStore();
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (isRunning && progressRef.current) {
      // Scroll to progress bar when scheduler starts
      setTimeout(() => {
        progressRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    }
  }, [isRunning]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container max-w-5xl mx-auto flex h-16 items-center justify-between py-4">
          <div className="flex items-center gap-4">
            <JuilliardLogo />
            <div className="h-6 w-px bg-border hidden sm:block" />
            <h1 className="text-xl font-semibold tracking-tight hidden sm:block">Audition Scheduler</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowSettings(true)}
              className="h-9 w-9 rounded-full"
              title="Settings"
            >
              <Settings className="h-4 w-4" />
              <span className="sr-only">Open settings</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setDarkMode(!darkMode)}
              className="h-9 w-9 rounded-full"
              title="Toggle theme"
            >
              {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="container max-w-5xl mx-auto py-8 space-y-10">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">New Schedule</h2>
          <p className="text-muted-foreground">
            Upload your data files and configure audition days to generate a new schedule.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1fr_300px] xl:grid-cols-[1fr_350px]">
          <div className="space-y-8">
            <FileUpload />
            <CalendarConfig />
          </div>
          
          <div className="space-y-6">
            {/* Sidebar content could go here if needed, or we can keep it full width */}
          </div>
        </div>
        
        {isRunning && (
          <Card ref={progressRef} className="border-primary/50 bg-primary/5 animate-in slide-in-from-top-5 fade-in-50">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-lg font-semibold">Generating schedule...</p>
                  <span className="text-sm text-muted-foreground">Processing</span>
                </div>
                <Progress value={undefined} className="h-2" />
                <p className="text-sm text-muted-foreground text-center">
                  This may take a moment based on the dataset size.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive dark:border-destructive">
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold">Error</span>
              <p className="text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        {results && (
          <div className="animate-in slide-in-from-bottom-10 fade-in-50 duration-500">
            <ResultsDisplay />
          </div>
        )}
      </main>

      <SettingsDialog open={showSettings} onOpenChange={setShowSettings} />
    </div>
  );
}

export default App;
