import { create } from 'zustand';

interface SchedulerState {
  applicantFile: string | null;
  facultyFile: string | null;
  mappingFile: string;
  rulesFile: string;
  calendarDays: Array<{ date: string; start: string; end: string }>;
  isRunning: boolean;
  isValidating: boolean;
  validationResult: { valid: boolean; message?: string } | null;
  results: {
    scheduled: any[];
    conflicts: any[];
    metrics: string;
    outputFiles: {
      schedule: string;
      conflicts: string;
      metrics: string;
    };
  } | null;
  error: string | null;
  setApplicantFile: (file: string | null) => void;
  setFacultyFile: (file: string | null) => void;
  setMappingFile: (file: string) => void;
  setRulesFile: (file: string) => void;
  setCalendarDays: (days: Array<{ date: string; start: string; end: string }>) => void;
  setIsRunning: (running: boolean) => void;
  setIsValidating: (validating: boolean) => void;
  setValidationResult: (result: { valid: boolean; message?: string } | null) => void;
  clearValidation: () => void;
  setResults: (results: any) => void;
  setError: (error: string | null) => void;
}

export const useSchedulerStore = create<SchedulerState>((set) => ({
  applicantFile: null,
  facultyFile: null,
  mappingFile: 'schools/juilliard/mapping.yaml',
  rulesFile: 'schools/juilliard/rules.yaml',
  calendarDays: [],
  isRunning: false,
  isValidating: false,
  validationResult: null,
  results: null,
  error: null,
  setApplicantFile: (file) => set({ applicantFile: file }),
  setFacultyFile: (file) => set({ facultyFile: file }),
  setMappingFile: (file) => set({ mappingFile: file }),
  setRulesFile: (file) => set({ rulesFile: file }),
  setCalendarDays: (days) => set({ calendarDays: days }),
  setIsRunning: (running) => set({ isRunning: running }),
  setIsValidating: (validating) => set({ isValidating: validating }),
  setValidationResult: (result) => set({ validationResult: result }),
  clearValidation: () => set({ validationResult: null }),
  setResults: (results) => set({ results, error: null }),
  setError: (error) => set({ error, results: null }),
}));

