import { useState } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Download, CheckCircle, AlertCircle, BarChart3, FileSpreadsheet } from 'lucide-react';

export default function ResultsDisplay() {
  const { results, error } = useSchedulerStore();
  const [activeTab, setActiveTab] = useState('schedule');

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Results</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload(results.outputFiles.schedule)}
          >
            <Download className="mr-2 h-4 w-4" />
            Schedule
          </Button>
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
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDownload(results.outputFiles.schedule)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Excel
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="py-12">
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <FileSpreadsheet className="h-12 w-12 text-muted-foreground/50" />
                  <div>
                    <p className="text-lg font-medium mb-2">Preview not available</p>
                    <p className="text-sm text-muted-foreground">
                      Please download the Excel file to view the scheduled applicants.
                    </p>
                  </div>
                  <Button
                    onClick={() => handleDownload(results.outputFiles.schedule)}
                    className="mt-4"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Schedule Excel File
                  </Button>
                </div>
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
                      Download the Excel file to view applicants that could not be scheduled
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
              <CardContent className="py-12">
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <AlertCircle className="h-12 w-12 text-muted-foreground/50" />
                  <div>
                    <p className="text-lg font-medium mb-2">Preview not available</p>
                    <p className="text-sm text-muted-foreground">
                      Please download the Excel file to view conflicts.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => handleDownload(results.outputFiles.conflicts)}
                    className="mt-4"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Conflicts Excel File
                  </Button>
                </div>
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
