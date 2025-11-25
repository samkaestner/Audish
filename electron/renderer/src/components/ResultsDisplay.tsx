import { useState } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Download, CheckCircle, AlertCircle, BarChart3 } from 'lucide-react';

export default function ResultsDisplay() {
  const { results, error } = useSchedulerStore();
  const [activeTab, setActiveTab] = useState('schedule');

  if (error) return null;
  if (!results) return null;

  const handleDownload = async (filePath: string, filename: string) => {
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Results</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload(results.outputFiles.schedule, 'FinalSchedule.xlsx')}
          >
            <Download className="mr-2 h-4 w-4" />
            Schedule
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload(results.outputFiles.conflicts, 'Conflicts.xlsx')}
          >
            <Download className="mr-2 h-4 w-4" />
            Conflicts
          </Button>
        </div>
      </div>

      {/* Metrics Summary Cards */}
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
                      {results.scheduledTotal || results.scheduled.length} applicants scheduled successfully
                    </CardDescription>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(results.outputFiles.schedule, 'FinalSchedule.xlsx')}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export Excel
                  </Button>
                </div>
              </CardHeader>
              <div className="relative">
                {results.scheduled.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-muted-foreground">No scheduled applicants to display</p>
                  </div>
                ) : (
                  <div className="rounded-md border-0">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          {results.scheduled[0] && Object.keys(results.scheduled[0]).map((key) => (
                            <TableHead key={key} className="whitespace-nowrap">{key}</TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {results.scheduled.slice(0, 100).map((row, idx) => (
                          <TableRow key={idx}>
                            {Object.values(row).map((cell: any, cellIdx) => (
                              <TableCell key={cellIdx} className="max-w-[200px] truncate" title={String(cell)}>
                                {String(cell || '')}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
              {(results.scheduledTotal || results.scheduled.length) > 100 && (
                <CardFooter className="border-t bg-muted/20 px-6 py-3">
                  <p className="text-xs text-muted-foreground w-full text-center">
                    Showing first 100 rows. Download the Excel file to view all {results.scheduledTotal || results.scheduled.length} records.
                  </p>
                </CardFooter>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="conflicts" className="mt-0">
            <Card>
              <CardHeader className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-destructive">Conflicts</CardTitle>
                    <CardDescription>
                      {results.conflictsTotal || results.conflicts.length} applicants could not be scheduled
                    </CardDescription>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(results.outputFiles.conflicts, 'Conflicts.xlsx')}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export Excel
                  </Button>
                </div>
              </CardHeader>
              <div className="relative">
                {results.conflicts.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <CheckCircle className="h-12 w-12 text-green-500 mb-4 opacity-20" />
                    <p className="text-lg font-medium">No conflicts found</p>
                    <p className="text-sm text-muted-foreground">All applicants were scheduled successfully.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        {results.conflicts[0] && Object.keys(results.conflicts[0]).map((key) => (
                          <TableHead key={key}>{key}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.conflicts.map((row, idx) => (
                        <TableRow key={idx}>
                          {Object.values(row).map((cell: any, cellIdx) => (
                            <TableCell key={cellIdx}>{String(cell || '')}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
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
                    onClick={() => handleDownload(results.outputFiles.metrics, 'Metrics.txt')}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Text File
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="bg-muted/30 p-6 overflow-x-auto">
                  <pre className="font-mono text-sm whitespace-pre-wrap text-foreground/80">
                    {results.metrics}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
