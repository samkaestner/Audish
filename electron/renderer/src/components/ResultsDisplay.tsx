import { useState, useEffect } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Download, CheckCircle, AlertCircle, BarChart3 } from 'lucide-react';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from './ui/table';

export default function ResultsDisplay() {
  const { results, error } = useSchedulerStore();
  const [activeTab, setActiveTab] = useState('conflicts');
  const [conflictPreview, setConflictPreview] = useState<{
    headers: string[];
    rows: string[][];
  } | null>(null);
  const [loadingConflicts, setLoadingConflicts] = useState(false);
  const [conflictsError, setConflictsError] = useState<string | null>(null);

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

  const parseMetrics = (metricsText: string) => {
    const lines = metricsText.split('\n');
    const metrics: Record<string, string> = {};
    let currentSection = '';

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) return;

      if (!trimmed.startsWith('  ')) {
        currentSection = trimmed;
      } else {
        const [key, ...valueParts] = trimmed.split(':');
        if (key && valueParts.length > 0) {
          metrics[`${currentSection} - ${key.trim()}`] = valueParts.join(':').trim();
        }
      }
    });

    return metrics;
  };

  const metrics = parseMetrics(results.metrics);

  useEffect(() => {
    const loadConflictsPreview = async () => {
      if (!window.electronAPI || !results?.outputFiles?.conflicts) return;

      setLoadingConflicts(true);
      setConflictsError(null);

      try {
        const preview = await window.electronAPI.readExcelPreview(
          results.outputFiles.conflicts,
          30
        );

        if (preview && preview.success !== false) {
          const headers: string[] = preview.headers || [];
          const rows: string[][] = preview.data || [];

          setConflictPreview({ headers, rows });
        } else {
          setConflictsError(preview?.error || 'Failed to load conflicts preview');
        }
      } catch (err: any) {
        setConflictsError(err?.message || 'Failed to load conflicts preview');
      } finally {
        setLoadingConflicts(false);
      }
    };

    loadConflictsPreview();
  }, [results?.outputFiles?.conflicts]);

  const getReasonCodeStyle = (reason: string) => {
    const code = reason.toUpperCase();

    if (!code) {
      return 'bg-muted text-muted-foreground';
    }

    if (code.includes('MISSING') || code.includes('INCOMPLETE') || code.includes('INVALID')) {
      return 'bg-amber-500/10 text-amber-500 border border-amber-500/30';
    }

    if (code.includes('UNAVAILABLE') || code.includes('CONFLICT') || code.includes('OVERLAP')) {
      return 'bg-red-500/10 text-red-400 border border-red-500/30';
    }

    if (code.includes('OK') || code.includes('INFO') || code.includes('NOTE')) {
      return 'bg-blue-500/10 text-blue-400 border border-blue-500/30';
    }

    return 'bg-muted text-muted-foreground border border-border/60';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Results</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload(results.outputFiles.conflicts)}
          >
            <Download className="mr-2 h-4 w-4" />
            Conflicts
          </Button>
        </div>
      </div>

      {/* Success Message */}
      <Card className="border-green-500/50 bg-green-500/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="h-6 w-6 text-green-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">Schedule Generated Successfully</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Your schedule has been generated. Download the Excel files below to view the results.
              </p>
              <div className="flex gap-2">
                <Button
                  variant="default"
                  onClick={() => handleDownload(results.outputFiles.schedule)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Schedule
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleDownload(results.outputFiles.conflicts)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Conflicts
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Summary Cards - Only show if we have metrics data */}
      {Object.keys(metrics).length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Object.entries(metrics).slice(0, 4).map(([key, value], i) => {
            // Simple logic to pick an icon based on the card index or content
            const Icon = i === 0 ? BarChart3 : i === 1 ? CheckCircle : i === 2 ? AlertCircle : BarChart3;
            
            return (
              <Card key={key}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {key.split('-').pop()?.trim()}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{value}</div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Tabs for Schedule, Conflicts, Metrics */}
      <Card className="border-0 shadow-none bg-transparent">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList>
              <TabsTrigger value="schedule">Schedule</TabsTrigger>
              <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
              <TabsTrigger value="metrics">Raw Metrics</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="schedule" className="mt-0">
            <Card>
              <CardHeader className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Scheduled Applicants</CardTitle>
                    <CardDescription>
                      Download the Excel file to view scheduled applicants
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="py-6">
                <p className="text-sm text-muted-foreground">
                  The full schedule is available in the Excel file. Download it to view all
                  scheduled applicants and time slots.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="conflicts" className="mt-0">
            <Card>
              <CardHeader className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-destructive">Conflicts</CardTitle>
                    <CardDescription>
                      Preview the first 30 applicants that could not be scheduled, including
                      reason codes and key details.
                    </CardDescription>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(results.outputFiles.conflicts)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Excel
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="py-6">
                {loadingConflicts && (
                  <p className="text-sm text-muted-foreground">Loading conflicts preview...</p>
                )}

                {conflictsError && !loadingConflicts && (
                  <div className="flex items-start gap-2 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4 mt-0.5" />
                    <p>{conflictsError}</p>
                  </div>
                )}

                {!loadingConflicts && !conflictsError && conflictPreview && (
                  <div className="space-y-4">
                    <div className="rounded-md border bg-background overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {conflictPreview.headers.map((header) => {
                              // Prioritize important columns - make them wider
                              const isImportantColumn =
                                header === '_ReasonCode' ||
                                header.toLowerCase().includes('reason') ||
                                header.toLowerCase().includes('conflict') ||
                                header.toLowerCase().includes('school') ||
                                header.toLowerCase().includes('name') ||
                                header.toLowerCase().includes('applicant');
                              
                              const isLongHeader = header.length > 30;
                              const shortHeader = isLongHeader
                                ? header
                                    .replace(/Event - Most Recent Registration /g, '')
                                    .replace(/Event Date\/Time/g, 'Date/Time')
                                    .replace(/Audition Modality Accommodation Approved/g, 'Modality')
                                    .replace(/BM and BCJ Applicant/g, 'BM/BCJ')
                                : header;

                              return (
                                <TableHead
                                  key={header}
                                  className={isImportantColumn ? 'min-w-[150px]' : 'min-w-[100px] max-w-[200px]'}
                                  title={isLongHeader ? header : undefined}
                                >
                                  <div className="truncate" title={header}>
                                    {shortHeader}
                                  </div>
                                </TableHead>
                              );
                            })}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {conflictPreview.rows.slice(0, 30).map((row, index) => (
                            <TableRow key={index}>
                              {conflictPreview.headers.map((header, colIndex) => {
                                const rawValue =
                                  row[colIndex] !== undefined && row[colIndex] !== null
                                    ? String(row[colIndex])
                                    : '';

                                const isReasonCodeColumn =
                                  header === '_ReasonCode' || header.toLowerCase().includes('reason');
                                
                                const isConflictDetailsColumn =
                                  header.toLowerCase().includes('conflict') && header.toLowerCase().includes('detail');
                                
                                const isImportantColumn =
                                  isReasonCodeColumn ||
                                  isConflictDetailsColumn ||
                                  header.toLowerCase().includes('school') ||
                                  header.toLowerCase().includes('name');

                                // Truncate long text (except for reason codes)
                                const maxLength = isImportantColumn ? 80 : 40;
                                const shouldTruncate = rawValue.length > maxLength;
                                const displayValue = shouldTruncate
                                  ? rawValue.substring(0, maxLength) + '...'
                                  : rawValue;

                                if (isReasonCodeColumn && rawValue) {
                                  return (
                                    <TableCell key={`${header}-${colIndex}`} className="whitespace-nowrap">
                                      <span
                                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${getReasonCodeStyle(
                                          rawValue
                                        )}`}
                                      >
                                        {rawValue}
                                      </span>
                                    </TableCell>
                                  );
                                }

                                return (
                                  <TableCell
                                    key={`${header}-${colIndex}`}
                                    className={isImportantColumn ? 'min-w-[150px]' : 'min-w-[100px] max-w-[200px]'}
                                    title={shouldTruncate ? rawValue : undefined}
                                  >
                                    <div className="truncate" title={rawValue}>
                                      {displayValue}
                                    </div>
                                  </TableCell>
                                );
                              })}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>
                        Showing up to 30 conflicts. Use the full Excel export to see all applicants
                        and detailed reason codes.
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="px-0 h-auto text-primary underline hover:no-underline"
                        onClick={() => handleDownload(results.outputFiles.conflicts)}
                      >
                        See all &amp; download Excel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics" className="mt-0">
            <Card>
              <CardHeader className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <CardTitle>Full Metrics Report</CardTitle>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(results.outputFiles.metrics)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Text File
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="bg-muted/30 p-6 space-y-3">
                  {results.metrics.split('\n').map((line, index) => {
                    const trimmed = line.trim();

                    if (!trimmed) {
                      return <div key={index} className="h-2" />;
                    }

                    const isSectionHeader = !line.startsWith('  ');

                    if (isSectionHeader) {
                      return (
                        <div key={index} className="text-sm font-semibold text-foreground">
                          {trimmed}
                        </div>
                      );
                    }

                    return (
                      <div
                        key={index}
                        className="pl-4 text-sm text-muted-foreground flex gap-2"
                      >
                        <span className="text-muted-foreground/70">•</span>
                        <span>{trimmed}</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
