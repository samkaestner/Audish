import { useState } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Download } from 'lucide-react';

export default function ResultsDisplay() {
  const { results, error } = useSchedulerStore();
  const [activeTab, setActiveTab] = useState('schedule');

  if (error) {
    return (
      <Card className="border-red-500">
        <CardHeader>
          <CardTitle className="text-red-500">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="font-mono text-sm">{error}</p>
        </CardContent>
      </Card>
    );
  }

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
      <h2 className="text-2xl font-bold">Results</h2>

      {/* Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(metrics).slice(0, 4).map(([key, value]) => (
          <Card key={key}>
            <CardHeader>
              <CardTitle className="text-sm">{key}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs for Schedule, Conflicts, Metrics */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="schedule">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Scheduled Applicants</CardTitle>
                <Button
                  onClick={() => handleDownload(results.outputFiles.schedule, 'FinalSchedule.xlsx')}
                  size="sm"
                >
                  <Download size={16} className="mr-2" />
                  Download Excel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {results.scheduled.length === 0 ? (
                <p className="text-center py-8 opacity-70">No scheduled applicants to display</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {results.scheduled[0] && Object.keys(results.scheduled[0]).map((key) => (
                          <TableHead key={key}>{key}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.scheduled.slice(0, 100).map((row, idx) => (
                        <TableRow key={idx}>
                          {Object.values(row).map((cell: any, cellIdx) => (
                            <TableCell key={cellIdx}>{String(cell || '')}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {results.scheduled.length > 100 && (
                    <p className="text-center py-4 text-sm opacity-70">
                      Showing first 100 of {results.scheduled.length} rows
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conflicts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Conflicts</CardTitle>
                <Button
                  onClick={() => handleDownload(results.outputFiles.conflicts, 'Conflicts.xlsx')}
                  size="sm"
                >
                  <Download size={16} className="mr-2" />
                  Download Excel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {results.conflicts.length === 0 ? (
                <p className="text-center py-8 opacity-70">No conflicts found</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
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
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="font-mono text-sm whitespace-pre-wrap bg-card p-4 border-2 border-black dark:border-white overflow-x-auto">
                {results.metrics}
              </pre>
              <div className="mt-4">
                <Button
                  onClick={() => handleDownload(results.outputFiles.metrics, 'Metrics.txt')}
                  size="sm"
                >
                  <Download size={16} className="mr-2" />
                  Download Metrics
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

