import { useState, useEffect } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogContent, DialogFooter } from './ui/dialog';
import { FileText } from 'lucide-react';
import * as yaml from 'js-yaml';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const {
    mappingFile,
    rulesFile,
    setMappingFile,
    setRulesFile,
    setCalendarDays,
  } = useSchedulerStore();

  const [configFiles, setConfigFiles] = useState({
    mapping: mappingFile,
    rules: rulesFile,
  });

  useEffect(() => {
    setConfigFiles({
      mapping: mappingFile,
      rules: rulesFile,
    });
  }, [mappingFile, rulesFile]);

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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          <span>Advanced Settings</span>
        </DialogTitle>
      </DialogHeader>
      <DialogContent>
        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Configuration files control how the scheduler processes your data. 
              These settings are typically only changed for advanced use cases.
            </p>
          </div>

          <div className="grid gap-4">
            <div className="grid gap-2">
              <label className="text-sm font-medium">Mapping File</label>
              <div className="flex gap-2">
                <Input
                  value={configFiles.mapping}
                  onChange={(e) => setConfigFiles({ ...configFiles, mapping: e.target.value })}
                  className="flex-1 font-mono text-xs"
                  readOnly
                />
                <Button onClick={() => handleSelectConfigFile('mapping')} variant="secondary" size="sm">
                  Browse
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Maps Excel column names to internal fields
              </p>
            </div>

            <div className="grid gap-2">
              <label className="text-sm font-medium">Rules File</label>
              <div className="flex gap-2">
                <Input
                  value={configFiles.rules}
                  onChange={(e) => setConfigFiles({ ...configFiles, rules: e.target.value })}
                  className="flex-1 font-mono text-xs"
                  readOnly
                />
                <Button onClick={() => handleSelectConfigFile('rules')} variant="secondary" size="sm">
                  Browse
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Defines scheduling rules and calendar configuration
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

