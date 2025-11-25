import { useState, useEffect } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogHeader, DialogTitle, DialogContent, DialogFooter, DialogClose } from './ui/dialog';
import { Plus, Trash2, Play } from 'lucide-react';
import * as yaml from 'js-yaml';

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
    setMappingFile,
    setRulesFile,
  } = useSchedulerStore();

  const [configFiles, setConfigFiles] = useState({
    mapping: mappingFile,
    rules: rulesFile,
  });
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
      const rulesPath = rulesFile.startsWith('/') || rulesFile.match(/^[A-Z]:/) 
        ? rulesFile 
        : `${projectRoot}/${rulesFile}`;
      
      const fileResult = await window.electronAPI.readFile(rulesPath);
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

  const handleSelectConfigFile = async (type: 'mapping' | 'rules') => {
    if (!window.electronAPI) return;
    
    const file = await window.electronAPI.selectFile({
      filters: [{ name: 'YAML Files', extensions: ['yaml', 'yml'] }],
    });
    
    if (file) {
      if (type === 'mapping') {
        setConfigFiles({ ...configFiles, mapping: file });
        setMappingFile(file);
      } else {
        setConfigFiles({ ...configFiles, rules: file });
        setRulesFile(file);
        // Reload calendar days from new rules file
        const fileResult = await window.electronAPI.readFile(file);
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
      }
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

    try {
      // Create temporary rules file with updated calendar
      const projectRoot = await window.electronAPI.getProjectRoot();
      const originalRulesPath = configFiles.rules.startsWith('/') || configFiles.rules.match(/^[A-Z]:/)
        ? configFiles.rules
        : `${projectRoot}/${configFiles.rules}`;
      
      const fileResult = await window.electronAPI.readFile(originalRulesPath);
      
      if (!fileResult.success) {
        throw new Error('Failed to read rules file');
      }

      const rules = yaml.load(fileResult.content) as any;
      rules.calendar = { days: calendarDays };
      
      // Write temporary rules file
      const tempRulesPath = `${projectRoot}/temp_rules.yaml`;
      const writeResult = await window.electronAPI.writeFile(tempRulesPath, yaml.dump(rules));
      if (!writeResult.success) {
        throw new Error('Failed to write temporary rules file');
      }

      // Get output directory
      const outputDir = `${projectRoot}/output`;
      
      const mappingPath = configFiles.mapping.startsWith('/') || configFiles.mapping.match(/^[A-Z]:/)
        ? configFiles.mapping
        : `${projectRoot}/${configFiles.mapping}`;
      
      const result = await window.electronAPI.runScheduler({
        applicantFile,
        facultyFile,
        mappingFile: mappingPath,
        rulesFile: tempRulesPath,
        outputDir,
      });

      if (result.success) {
        // Read output files
        const scheduleResult = await window.electronAPI.readExcelPreview(result.outputFiles.schedule, 1000);
        const conflictsResult = await window.electronAPI.readExcelPreview(result.outputFiles.conflicts, 1000);
        const metricsResult = await window.electronAPI.readFile(result.outputFiles.metrics);

        // Convert Excel preview data to table format
        const scheduledData = scheduleResult.success && scheduleResult.headers
          ? scheduleResult.data.map((row: string[]) => {
              const obj: Record<string, string> = {};
              scheduleResult.headers.forEach((header: string, idx: number) => {
                obj[header] = row[idx] || '';
              });
              return obj;
            })
          : [];

        const conflictsData = conflictsResult.success && conflictsResult.headers
          ? conflictsResult.data.map((row: string[]) => {
              const obj: Record<string, string> = {};
              conflictsResult.headers.forEach((header: string, idx: number) => {
                obj[header] = row[idx] || '';
              });
              return obj;
            })
          : [];

        setResults({
          scheduled: scheduledData,
          conflicts: conflictsData,
          metrics: metricsResult.content || '',
          outputFiles: result.outputFiles,
        });
      } else {
        setError(result.error || 'Scheduler failed');
      }
    } catch (error: any) {
      setError(error.message || 'Failed to run scheduler');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Configuration</h2>

      <Card>
        <CardHeader>
          <CardTitle>Configuration Files</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block mb-2 font-bold">Mapping File</label>
            <div className="flex gap-2">
              <Input
                value={configFiles.mapping}
                onChange={(e) => setConfigFiles({ ...configFiles, mapping: e.target.value })}
                className="flex-1"
              />
              <Button onClick={() => handleSelectConfigFile('mapping')} variant="outline">
                Browse
              </Button>
            </div>
          </div>

          <div>
            <label className="block mb-2 font-bold">Rules File</label>
            <div className="flex gap-2">
              <Input
                value={configFiles.rules}
                onChange={(e) => setConfigFiles({ ...configFiles, rules: e.target.value })}
                className="flex-1"
              />
              <Button onClick={() => handleSelectConfigFile('rules')} variant="outline">
                Browse
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Audition Days</CardTitle>
            <Button onClick={openAddDayDialog} size="sm">
              <Plus size={16} className="mr-2" />
              Add Day
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {calendarDays.length === 0 ? (
            <p className="text-center py-8 opacity-70">No days configured. Click "Add Day" to get started.</p>
          ) : (
            calendarDays.map((day, index) => (
              <div key={index} className="flex gap-4 items-center border-2 border-black dark:border-white p-4 bg-card">
                <div className="flex-1">
                  <label className="block mb-1 text-sm font-bold">Date</label>
                  <Input
                    type="date"
                    value={typeof day.date === 'string' ? day.date : (day.date instanceof Date ? day.date.toISOString().split('T')[0] : '')}
                    onChange={(e) => updateDay(index, 'date', e.target.value)}
                  />
                </div>
                <div className="flex-1">
                  <label className="block mb-1 text-sm font-bold">Start Time</label>
                  <Input
                    type="time"
                    value={day.start}
                    onChange={(e) => updateDay(index, 'start', e.target.value)}
                  />
                </div>
                <div className="flex-1">
                  <label className="block mb-1 text-sm font-bold">End Time</label>
                  <Input
                    type="time"
                    value={day.end}
                    onChange={(e) => updateDay(index, 'end', e.target.value)}
                  />
                </div>
                <Button
                  onClick={() => removeDay(index)}
                  variant="ghost"
                  size="sm"
                  className="text-red-500"
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          onClick={runScheduler}
          size="lg"
          disabled={!applicantFile || !facultyFile || calendarDays.length === 0}
          className="px-12"
        >
          <Play size={20} className="mr-2" />
          Run Scheduler
        </Button>
      </div>

      <Dialog open={showAddDayDialog} onOpenChange={setShowAddDayDialog}>
        <DialogHeader>
          <DialogTitle>Add Audition Day</DialogTitle>
          <DialogClose />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block mb-2 font-bold">Date</label>
              <Input
                type="date"
                value={newDay.date}
                onChange={(e) => setNewDay({ ...newDay, date: e.target.value })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block mb-2 font-bold">Start Time</label>
              <Input
                type="time"
                value={newDay.start}
                onChange={(e) => setNewDay({ ...newDay, start: e.target.value })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block mb-2 font-bold">End Time</label>
              <Input
                type="time"
                value={newDay.end}
                onChange={(e) => setNewDay({ ...newDay, end: e.target.value })}
                className="w-full"
              />
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
          <Button
            onClick={handleAddDay}
            disabled={!newDay.date}
          >
            Add Day
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

