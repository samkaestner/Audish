import { useState, useEffect } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  BarChart3, 
  FileSpreadsheet,
  ExternalLink,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface Conflict {
  applicantId?: string;
  discipline?: string;
  degree?: string;
  reasonCode?: string;
  details?: string;
}

export default function ResultsDisplay() {
  const { results, error } = useSchedulerStore();
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [totalConflicts, setTotalConflicts] = useState(0);
  const [loadingConflicts, setLoadingConflicts] = useState(false);
  const [showRawMetrics, setShowRawMetrics] = useState(false);

  // Load conflicts preview on mount
  useEffect(() => {
    if (results?.outputFiles?.conflicts) {
      loadConflictsPreview();
    }
  }, [results?.outputFiles?.conflicts]);

  const loadConflictsPreview = async () => {
    if (!window.electronAPI || !results?.outputFiles?.conflicts) return;
    
    setLoadingConflicts(true);
    try {
      const preview = await window.electronAPI.readExcelPreview(results.outputFiles.conflicts, 15);
      if (preview.success && preview.data && preview.headers) {
        // Store actual total count
        setTotalConflicts(preview.total_rows || preview.data.length);
        
        // Map headers by exact column names (case-insensitive)
        const headers = preview.headers.map((h: string) => h.toLowerCase());
        const idIdx = headers.indexOf('applicantid');
        const discIdx = headers.indexOf('discipline');
        const degreeIdx = headers.indexOf('degree');
        const reasonIdx = headers.indexOf('reasoncode');
        const detailsIdx = headers.indexOf('details');
        
        const mappedConflicts: Conflict[] = preview.data.map((row: string[]) => ({
          applicantId: idIdx >= 0 ? row[idIdx] : row[0] || '-',
          discipline: discIdx >= 0 ? row[discIdx] : row[2] || '-',
          degree: degreeIdx >= 0 ? row[degreeIdx] : row[1] || '-',
          reasonCode: reasonIdx >= 0 ? row[reasonIdx] : row[3] || '-',
          details: detailsIdx >= 0 ? row[detailsIdx] : row[4] || '-',
        }));
        
        setConflicts(mappedConflicts);
      }
    } catch (err) {
      console.error('Failed to load conflicts preview:', err);
    } finally {
      setLoadingConflicts(false);
    }
  };

  if (error) return null;
  if (!results) return null;

  const handleDownload = async (filePath: string) => {
    if (!window.electronAPI) return;
    
    try {
      const result = await window.electronAPI.downloadFile(filePath);
      if (!result.success) {
        alert(`Failed to download file: ${result.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      alert(`Error downloading file: ${error.message}`);
    }
  };

  const handleOpenInExcel = async (filePath: string) => {
    if (!window.electronAPI) return;
    
    try {
      const result = await window.electronAPI.openFile(filePath);
      if (!result.success) {
        alert(`Failed to open file: ${result.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      alert(`Error opening file: ${error.message}`);
    }
  };

  const parseMetrics = (metricsText: string) => {
    const lines = metricsText.split('\n');
    const metrics: { key: string; value: string; section: string }[] = [];
    let currentSection = '';

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) return;

      if (!trimmed.startsWith('  ') && !trimmed.includes(':')) {
        currentSection = trimmed;
      } else if (trimmed.includes(':')) {
        const [key, ...valueParts] = trimmed.split(':');
        if (key && valueParts.length > 0) {
          metrics.push({
            key: key.trim(),
            value: valueParts.join(':').trim(),
            section: currentSection
          });
        }
      }
    });

    return metrics;
  };

  const allMetrics = parseMetrics(results.metrics);
  const summaryMetrics = allMetrics.slice(0, 4);
  const hasMoreConflicts = totalConflicts > 10;
  const displayedConflicts = conflicts.slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Success Message with Actions */}
      <Card className="border-green-500/50 bg-green-500/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="h-6 w-6 text-green-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">Schedule Generated Successfully</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Your audition schedule has been created. Open in Excel to review and make any final adjustments.
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => handleOpenInExcel(results.outputFiles.schedule)}
                >
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  Open in Excel
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleDownload(results.outputFiles.schedule)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Summary Cards */}
      {summaryMetrics.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {summaryMetrics.map((metric, i) => {
            const Icon = i === 0 ? BarChart3 : i === 1 ? CheckCircle : i === 2 ? AlertTriangle : BarChart3;
            
            return (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.key}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metric.value}</div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Conflicts Section */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Conflicts
              </CardTitle>
              <CardDescription>
                {totalConflicts === 0 
                  ? 'No conflicts found - all applicants were scheduled!'
                  : `${totalConflicts} applicant${totalConflicts === 1 ? '' : 's'} could not be scheduled`
                }
              </CardDescription>
            </div>
            {conflicts.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload(results.outputFiles.conflicts)}
              >
                <Download className="mr-2 h-4 w-4" />
                Download All
              </Button>
            )}
          </div>
        </CardHeader>
        {conflicts.length > 0 && (
          <CardContent className="pt-0">
            <div className="rounded-md border">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Applicant ID</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Discipline</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Degree</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Reason</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedConflicts.map((conflict, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3 font-medium">{conflict.applicantId}</td>
                        <td className="px-4 py-3 text-muted-foreground">{conflict.discipline}</td>
                        <td className="px-4 py-3 text-muted-foreground">{conflict.degree}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-600 dark:text-amber-400">
                            {conflict.reasonCode}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground max-w-xs truncate" title={conflict.details}>
                          {conflict.details}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            {hasMoreConflicts && (
              <div className="mt-4 text-center">
                <Button
                  variant="ghost"
                  onClick={() => handleDownload(results.outputFiles.conflicts)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  View all {totalConflicts} conflicts
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
        )}
        {totalConflicts === 0 && !loadingConflicts && (
          <CardContent className="pt-0">
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
              All applicants were successfully scheduled
            </div>
          </CardContent>
        )}
      </Card>

      {/* Raw Metrics (Collapsible) */}
      <Card>
        <CardHeader 
          className="cursor-pointer hover:bg-muted/30 transition-colors"
          onClick={() => setShowRawMetrics(!showRawMetrics)}
        >
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Detailed Metrics</CardTitle>
              <CardDescription>Full scheduling report with all statistics</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload(results.outputFiles.metrics);
                }}
              >
                <Download className="h-4 w-4" />
              </Button>
              {showRawMetrics ? (
                <ChevronUp className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </div>
        </CardHeader>
        {showRawMetrics && (
          <CardContent className="pt-0">
            <div className="rounded-md border bg-muted/20 p-4 space-y-4">
              {/* Group metrics by section */}
              {Array.from(new Set(allMetrics.map(m => m.section))).map(section => (
                <div key={section}>
                  {section && (
                    <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                      {section}
                    </h4>
                  )}
                  <div className="grid gap-2">
                    {allMetrics
                      .filter(m => m.section === section)
                      .map((metric, i) => (
                        <div key={i} className="flex justify-between items-center py-1 border-b border-muted last:border-0">
                          <span className="text-sm text-muted-foreground">{metric.key}</span>
                          <span className="text-sm font-medium">{metric.value}</span>
                        </div>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
