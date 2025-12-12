import { useState, useEffect } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from './ui/card';
import { Dialog, DialogHeader, DialogTitle, DialogContent, DialogFooter } from './ui/dialog';
import { Plus, Trash2, Play, Calendar as CalendarIcon, Clock, CheckCircle2, AlertTriangle, Shield } from 'lucide-react';
import * as yaml from 'js-yaml';

function resolveConfigPath(file: string, projectRoot: string, schoolsDir?: string): string {
  // If absolute path (mac/linux) or windows drive path, use as-is
  if (file.startsWith('/') || file.match(/^[A-Z]:/)) return file;
  // If this is one of the bundled school config paths, resolve against bundled schools directory
  if (schoolsDir && (file === 'schools' || file.startsWith('schools/'))) {
    const relativeToSchools = file.replace(/^schools\/?/, '');
    return `${schoolsDir}/${relativeToSchools}`;
  }
  return `${projectRoot}/${file}`;
}

export default function CalendarConfig() {
  const {
    calendarDays,
    setCalendarDays,
    applicantFile,
    facultyFile,
    mappingFile,
    rulesFile,
    setIsRunning,
    setResults,
    setError,
    isValidating,
    validationResult,
    setIsValidating,
    setValidationResult,
    clearValidation,
  } = useSchedulerStore();

  const [showAddDayDialog, setShowAddDayDialog] = useState(false);
  const [newDay, setNewDay] = useState({ date: '', start: '09:00', end: '17:00' });

  // Load calendar days from rules.yaml on mount
  useEffect(() => {
    loadCalendarFromRules();
  }, []);

  const loadCalendarFromRules = async () => {
    if (!window.electronAPI) return;
    
    try {
      const projectRoot = await window.electronAPI.getProjectRoot();
      const schoolsDir = await window.electronAPI.getSchoolsDir?.();
      const rulesPath = resolveConfigPath(rulesFile, projectRoot, schoolsDir);
      
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'pre-fix',
          hypothesisId: 'A',
          location: 'electron/renderer/src/components/CalendarConfig.tsx:loadCalendarFromRules',
          message: 'Resolving rules path for calendar load',
          data: { projectRoot, schoolsDir, rulesFile, rulesPath },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      
      const fileResult = await window.electronAPI.readFile(rulesPath);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'pre-fix',
          hypothesisId: 'A',
          location: 'electron/renderer/src/components/CalendarConfig.tsx:loadCalendarFromRules',
          message: 'Read rules file result',
          data: { rulesPath, success: fileResult?.success, error: fileResult?.error, contentLength: fileResult?.content?.length },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      if (fileResult.success && fileResult.content) {
        // Use custom schema to prevent automatic date parsing
        const schema = yaml.DEFAULT_SCHEMA.extend([]);
        const rules = yaml.load(fileResult.content, { schema }) as any;
        if (rules?.calendar?.days) {
          // Normalize dates to YYYY-MM-DD format
          const normalizedDays = rules.calendar.days.map((day: any) => {
            let dateStr = day.date;
            // If it's a Date object, convert to string
            if (dateStr instanceof Date) {
              dateStr = dateStr.toISOString().split('T')[0];
            } else if (typeof dateStr === 'string') {
              // Ensure it's in YYYY-MM-DD format (already should be from YAML)
              // Just validate it's a valid date string
              if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                // Try to parse and reformat if needed
                const date = new Date(dateStr);
                if (!isNaN(date.getTime())) {
                  dateStr = date.toISOString().split('T')[0];
                }
              }
            }
            return {
              date: dateStr,
              start: day.start || '09:00',
              end: day.end || '17:00',
            };
          });
          setCalendarDays(normalizedDays);
        }
      }
    } catch (error) {
      console.error('Failed to load calendar from rules:', error);
    }
  };

  const openAddDayDialog = () => {
    const today = new Date();
    today.setDate(today.getDate() + calendarDays.length);
    const dateStr = today.toISOString().split('T')[0];
    setNewDay({ date: dateStr, start: '09:00', end: '17:00' });
    setShowAddDayDialog(true);
  };

  const handleAddDay = () => {
    if (!newDay.date) {
      setError('Please select a date');
      return;
    }
    setCalendarDays([
      ...calendarDays,
      { date: newDay.date, start: newDay.start, end: newDay.end },
    ]);
    setShowAddDayDialog(false);
    setNewDay({ date: '', start: '09:00', end: '17:00' });
  };

  const removeDay = (index: number) => {
    setCalendarDays(calendarDays.filter((_, i) => i !== index));
  };

  const updateDay = (index: number, field: 'date' | 'start' | 'end', value: string) => {
    const updated = [...calendarDays];
    updated[index] = { ...updated[index], [field]: value };
    setCalendarDays(updated);
  };


  const validateConfig = async () => {
    if (!applicantFile || !facultyFile) {
      setError('Please select both applicant and faculty files before validating');
      return;
    }

    setIsValidating(true);
    setError(null);
    clearValidation();

    try {
      const projectRoot = await window.electronAPI.getProjectRoot();
      const schoolsDir = await window.electronAPI.getSchoolsDir?.();
      
      const mappingPath = resolveConfigPath(mappingFile, projectRoot, schoolsDir);
      const rulesPath = resolveConfigPath(rulesFile, projectRoot, schoolsDir);
      
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'pre-fix',
          hypothesisId: 'A',
          location: 'electron/renderer/src/components/CalendarConfig.tsx:validateConfig',
          message: 'Resolved mapping/rules paths for validate',
          data: { projectRoot, schoolsDir, mappingFile, rulesFile, mappingPath, rulesPath },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion

      const result = await window.electronAPI.validateConfig({
        applicantFile,
        facultyFile,
        mappingFile: mappingPath,
        rulesFile: rulesPath,
      });

      if (result.success) {
        setValidationResult({
          valid: result.valid,
          message: result.message || (result.valid ? 'All checks passed!' : 'Validation failed'),
        });
      } else {
        setError(result.error || 'Validation failed');
      }
    } catch (error: any) {
      setError(error?.message || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  const runScheduler = async () => {
    if (!applicantFile || !facultyFile) {
      setError('Please select both applicant and faculty files');
      return;
    }

    if (calendarDays.length === 0) {
      setError('Please add at least one audition day');
      return;
    }

    setIsRunning(true);
    setError(null);
    clearValidation();

    try {
      // Create temporary rules file with updated calendar
      const projectRoot = await window.electronAPI.getProjectRoot();
      const schoolsDir = await window.electronAPI.getSchoolsDir?.();
      const originalRulesPath = resolveConfigPath(rulesFile, projectRoot, schoolsDir);
      
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'pre-fix',
          hypothesisId: 'B',
          location: 'electron/renderer/src/components/CalendarConfig.tsx:runScheduler',
          message: 'Resolved paths for scheduler run (incl temp rules/output)',
          data: {
            projectRoot,
            schoolsDir,
            originalRulesPath,
            tempRulesPath: `${projectRoot}/temp_rules.yaml`,
            outputDir: `${projectRoot}/output`,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      
      const fileResult = await window.electronAPI.readFile(originalRulesPath);
      
      if (!fileResult.success) {
        throw new Error('Failed to read rules file');
      }

      // Use custom schema to prevent automatic date parsing
      const schema = yaml.DEFAULT_SCHEMA.extend([]);
      const rules = yaml.load(fileResult.content || '', { schema }) as any;
      rules.calendar = { days: calendarDays };
      
      // Write temporary rules file
      const tempRulesPath = `${projectRoot}/temp_rules.yaml`;
      const writeResult = await window.electronAPI.writeFile(tempRulesPath, yaml.dump(rules));
      if (!writeResult.success) {
        throw new Error('Failed to write temporary rules file');
      }

      // Get output directory (use user's home dir for packaged app, can't write inside .app bundle)
      const outputDir = `${projectRoot}/output`;
      
      // Use resolveConfigPath for mapping file (schoolsDir-aware)
      const mappingPath = resolveConfigPath(mappingFile, projectRoot, schoolsDir);
      
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: 'debug-session',
          runId: 'post-fix',
          hypothesisId: 'C',
          location: 'electron/renderer/src/components/CalendarConfig.tsx:runScheduler',
          message: 'Final resolved paths sent to scheduler',
          data: { mappingPath, tempRulesPath, outputDir },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      
      const result = await window.electronAPI.runScheduler({
        applicantFile,
        facultyFile,
        mappingFile: mappingPath,
        rulesFile: tempRulesPath,
        outputDir,
      });

      if (result.success && result.outputFiles) {
        // Read metrics file for summary
        const metricsResult = await window.electronAPI.readFile(result.outputFiles.metrics);

        // Set results with empty preview data - users can download Excel files to view results
        setResults({
          scheduled: [],
          conflicts: [],
          scheduledTotal: 0,
          conflictsTotal: 0,
          metrics: metricsResult.content || result.stdout || 'Schedule generated successfully. Download Excel files to view results.',
          outputFiles: result.outputFiles,
        });
      } else {
        // Show detailed error message
        const errorMsg = result.error || (result as any).stderr || (result as any).stdout || 'Scheduler failed';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    } catch (error: any) {
      const errorMsg = error?.message || error?.toString() || 'Failed to run scheduler';
      setError(errorMsg);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Calendar Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <CalendarIcon className="h-5 w-5 text-muted-foreground" />
                <span>Audition Calendar</span>
              </CardTitle>
              <CardDescription>Configure the dates and times for auditions.</CardDescription>
            </div>
            <Button onClick={openAddDayDialog} size="sm" className="gap-1">
              <Plus size={16} />
              Add Day
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {calendarDays.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
              <CalendarIcon className="mx-auto h-10 w-10 text-muted-foreground/50" />
              <h3 className="mt-4 text-lg font-semibold">No audition days configured</h3>
              <p className="mb-4 mt-2 text-sm text-muted-foreground">
                Add dates to start building your schedule.
              </p>
              <Button onClick={openAddDayDialog} variant="outline" size="sm">
                Add First Day
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="grid grid-cols-[1fr_1fr_1fr_auto] gap-4 px-4 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                <div>Date</div>
                <div>Start Time</div>
                <div>End Time</div>
                <div className="w-8"></div>
              </div>
              {calendarDays.map((day, index) => (
                <div key={index} className="grid grid-cols-[1fr_1fr_1fr_auto] gap-4 items-center rounded-lg border p-3 bg-card hover:bg-accent/50 transition-colors">
                  <Input
                    type="date"
                    className="h-8"
                    value={typeof day.date === 'string' ? day.date : ''}
                    onChange={(e) => updateDay(index, 'date', e.target.value)}
                  />
                  <div className="relative">
                    <Input
                      type="time"
                      className="h-8 pl-8"
                      value={day.start}
                      onChange={(e) => updateDay(index, 'start', e.target.value)}
                    />
                    <Clock className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="relative">
                    <Input
                      type="time"
                      className="h-8 pl-8"
                      value={day.end}
                      onChange={(e) => updateDay(index, 'end', e.target.value)}
                    />
                    <Clock className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
                  </div>
                  <Button
                    onClick={() => removeDay(index)}
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
        <CardFooter className="bg-muted/20 border-t p-6">
          <div className="w-full space-y-4">
            {/* Validation Result */}
            {validationResult && (
              <div className={`flex items-start gap-3 rounded-lg border p-4 ${
                validationResult.valid 
                  ? 'bg-green-500/10 border-green-500/30 text-green-700 dark:text-green-400' 
                  : 'bg-destructive/10 border-destructive/30 text-destructive'
              }`}>
                {validationResult.valid ? (
                  <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                )}
                <pre className="text-sm whitespace-pre-wrap font-mono overflow-auto max-h-64 flex-1">
                  {validationResult.message}
                </pre>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={validateConfig}
                variant="outline"
                size="lg"
                disabled={!applicantFile || !facultyFile || isValidating}
                className="w-full sm:w-auto"
              >
                <Shield size={18} className="mr-2" />
                {isValidating ? 'Validating...' : 'Validate Configuration'}
              </Button>
              <Button
                onClick={runScheduler}
                size="lg"
                disabled={!applicantFile || !facultyFile || calendarDays.length === 0}
                className="w-full sm:w-auto"
              >
                <Play size={18} className="mr-2" />
                Run Scheduler
              </Button>
            </div>
          </div>
        </CardFooter>
      </Card>

      <Dialog open={showAddDayDialog} onOpenChange={setShowAddDayDialog}>
        <DialogHeader>
          <DialogTitle>Add Audition Day</DialogTitle>
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4 py-2">
            <div className="grid gap-2">
              <label className="text-sm font-medium">Date</label>
              <Input
                type="date"
                value={newDay.date}
                onChange={(e) => setNewDay({ ...newDay, date: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium">Start Time</label>
                <Input
                  type="time"
                  value={newDay.start}
                  onChange={(e) => setNewDay({ ...newDay, start: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">End Time</label>
                <Input
                  type="time"
                  value={newDay.end}
                  onChange={(e) => setNewDay({ ...newDay, end: e.target.value })}
                />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setShowAddDayDialog(false)}
          >
            Cancel
          </Button>
          <Button onClick={handleAddDay} disabled={!newDay.date}>
            Add Day
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}
