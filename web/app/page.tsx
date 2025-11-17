"use client";

import { useState } from "react";
import { Upload, FileCheck, Calendar, Download, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = "http://localhost:8000/api";

interface ValidationResult {
  applicants: {
    total: number;
    preview: any[];
    disciplines: Record<string, number>;
    degrees: Record<string, number>;
  };
  faculty: {
    total: number;
    preview: any[];
  };
  validation: {
    faculty_match_rate: number;
    matched_faculty: number;
    total_faculty: number;
    warnings: string[];
  };
}

interface ScheduleResult {
  metrics: {
    overall: {
      total: number;
      scheduled: number;
      conflicts: number;
      fill_rate: number;
    };
    teacher_preferences: Record<string, number>;
    conflict_reasons: Record<string, number>;
    by_discipline: Record<string, { total: number; scheduled: number; conflicts: number }>;
  };
  scheduled: {
    total: number;
    preview: any[];
    download_url: string;
  };
  conflicts: {
    total: number;
    preview: any[];
    download_url: string;
  };
}

export default function Home() {
  const [applicantsFile, setApplicantsFile] = useState<File | null>(null);
  const [facultyFile, setFacultyFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [scheduleResult, setScheduleResult] = useState<ScheduleResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const { toast } = useToast();

  const handleFileChange = (type: "applicants" | "faculty", file: File | null) => {
    if (type === "applicants") {
      setApplicantsFile(file);
    } else {
      setFacultyFile(file);
    }
    // Reset validation and schedule results when files change
    setValidationResult(null);
    setScheduleResult(null);
  };

  const handleValidate = async () => {
    if (!applicantsFile || !facultyFile) {
      toast({
        title: "Missing files",
        description: "Please upload both applicants and faculty files.",
        variant: "destructive",
      });
      return;
    }

    setIsValidating(true);
    const formData = new FormData();
    formData.append("applicants", applicantsFile);
    formData.append("faculty", facultyFile);

    try {
      const response = await fetch(`${API_BASE_URL}/validate-files`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Validation failed");
      }

      const result = await response.json();
      setValidationResult(result);
      toast({
        title: "Validation successful",
        description: `${result.applicants.total} applicants and ${result.faculty.total} faculty members loaded.`,
      });
    } catch (error: any) {
      toast({
        title: "Validation error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSchedule = async () => {
    if (!applicantsFile || !facultyFile) {
      toast({
        title: "Missing files",
        description: "Please upload both files and validate them first.",
        variant: "destructive",
      });
      return;
    }

    setIsScheduling(true);
    const formData = new FormData();
    formData.append("applicants", applicantsFile);
    formData.append("faculty", facultyFile);

    try {
      const response = await fetch(`${API_BASE_URL}/schedule`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Scheduling failed");
      }

      const result = await response.json();
      setScheduleResult(result);
      toast({
        title: "Scheduling complete",
        description: `${result.scheduled.total} applicants scheduled successfully.`,
      });
    } catch (error: any) {
      toast({
        title: "Scheduling error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const handleDownload = (filename: string) => {
    window.open(`${API_BASE_URL}/download/${filename}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Audish</h1>
          <p className="text-muted-foreground">Schedule music auditions with ease</p>
        </div>

        {/* File Upload Section */}
        <div className="grid md:grid-cols-2 gap-6">
          <FileUploadCard
            title="Applicant Information"
            description="Upload the Excel file containing applicant data"
            file={applicantsFile}
            onFileChange={(file) => handleFileChange("applicants", file)}
            icon={<Upload className="h-5 w-5" />}
          />
          <FileUploadCard
            title="Faculty Availability"
            description="Upload the Excel file containing faculty availability"
            file={facultyFile}
            onFileChange={(file) => handleFileChange("faculty", file)}
            icon={<Calendar className="h-5 w-5" />}
          />
        </div>

        {/* Validate Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleValidate}
            disabled={!applicantsFile || !facultyFile || isValidating}
            size="lg"
            className="w-full md:w-auto"
          >
            <FileCheck className="h-4 w-4 mr-2" />
            {isValidating ? "Validating..." : "Validate Files"}
          </Button>
        </div>

        {/* Validation Results */}
        {validationResult && (
          <Card>
            <CardHeader>
              <CardTitle>Validation Results</CardTitle>
              <CardDescription>Preview of uploaded data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Warnings */}
              {validationResult.validation.warnings.length > 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Warnings</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside">
                      {validationResult.validation.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  label="Total Applicants"
                  value={validationResult.applicants.total}
                />
                <StatCard
                  label="Total Faculty"
                  value={validationResult.faculty.total}
                />
                <StatCard
                  label="Disciplines"
                  value={Object.keys(validationResult.applicants.disciplines).length}
                />
                <StatCard
                  label="Faculty Match Rate"
                  value={`${validationResult.validation.faculty_match_rate}%`}
                />
              </div>

              {/* Discipline Breakdown */}
              <div>
                <h4 className="font-semibold mb-2">Applicants by Discipline</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(validationResult.applicants.disciplines).map(([discipline, count]) => (
                    <Badge key={discipline} variant="secondary">
                      {discipline}: {count}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Schedule Button */}
              <div className="flex justify-center pt-4">
                <Button
                  onClick={handleSchedule}
                  disabled={isScheduling}
                  size="lg"
                  className="w-full md:w-auto"
                >
                  {isScheduling ? "Scheduling..." : "Run Scheduler"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Schedule Results */}
        {scheduleResult && (
          <div className="space-y-6">
            {/* Metrics Dashboard */}
            <Card>
              <CardHeader>
                <CardTitle>Scheduling Results</CardTitle>
                <CardDescription>Overview of scheduling metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Overall Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    label="Total Applicants"
                    value={scheduleResult.metrics.overall.total}
                  />
                  <StatCard
                    label="Scheduled"
                    value={scheduleResult.metrics.overall.scheduled}
                    variant="success"
                  />
                  <StatCard
                    label="Conflicts"
                    value={scheduleResult.metrics.overall.conflicts}
                    variant={scheduleResult.metrics.overall.conflicts > 0 ? "warning" : "default"}
                  />
                  <StatCard
                    label="Fill Rate"
                    value={`${scheduleResult.metrics.overall.fill_rate}%`}
                    variant="success"
                  />
                </div>

                {/* Teacher Preferences */}
                <div>
                  <h4 className="font-semibold mb-2">Teacher Preference Matches</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(scheduleResult.metrics.teacher_preferences).map(([choice, count]) => (
                      <Badge key={choice} variant="outline">
                        {choice} Choice: {count}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Conflict Reasons */}
                {scheduleResult.metrics.overall.conflicts > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Conflict Reasons</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(scheduleResult.metrics.conflict_reasons).map(([reason, count]) => (
                        <Badge key={reason} variant="destructive">
                          {reason}: {count}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Download Buttons */}
                <div className="flex flex-wrap gap-4 pt-4">
                  <Button onClick={() => handleDownload("FinalSchedule.xlsx")}>
                    <Download className="h-4 w-4 mr-2" />
                    Download Schedule
                  </Button>
                  {scheduleResult.conflicts.total > 0 && (
                    <Button
                      variant="outline"
                      onClick={() => handleDownload("Conflicts.xlsx")}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Conflicts
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Results Tables */}
            <Card>
              <CardHeader>
                <CardTitle>Detailed Results</CardTitle>
                <CardDescription>Preview of scheduled applicants and conflicts</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="scheduled">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="scheduled">
                      Scheduled ({scheduleResult.scheduled.total})
                    </TabsTrigger>
                    <TabsTrigger value="conflicts">
                      Conflicts ({scheduleResult.conflicts.total})
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="scheduled">
                    <ScheduledTable data={scheduleResult.scheduled.preview} />
                  </TabsContent>
                  <TabsContent value="conflicts">
                    <ConflictsTable data={scheduleResult.conflicts.preview} />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Per-Discipline Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Per-Discipline Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Discipline</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Scheduled</TableHead>
                      <TableHead className="text-right">Conflicts</TableHead>
                      <TableHead className="text-right">Fill Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(scheduleResult.metrics.by_discipline).map(([discipline, stats]) => (
                      <TableRow key={discipline}>
                        <TableCell className="font-medium">{discipline}</TableCell>
                        <TableCell className="text-right">{stats.total}</TableCell>
                        <TableCell className="text-right">{stats.scheduled}</TableCell>
                        <TableCell className="text-right">{stats.conflicts}</TableCell>
                        <TableCell className="text-right">
                          {((stats.scheduled / stats.total) * 100).toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

// Component: File Upload Card
function FileUploadCard({
  title,
  description,
  file,
  onFileChange,
  icon,
}: {
  title: string;
  description: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  icon: React.ReactNode;
}) {
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith(".xlsx")) {
      onFileChange(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
        >
          {file ? (
            <div className="space-y-2">
              <CheckCircle2 className="h-8 w-8 mx-auto text-green-500" />
              <p className="font-medium">{file.name}</p>
              <p className="text-sm text-muted-foreground">
                {(file.size / 1024).toFixed(2)} KB
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onFileChange(null)}
              >
                Remove
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Drag and drop your Excel file here, or
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => document.getElementById(`file-${title}`)?.click()}
              >
                Browse Files
              </Button>
              <input
                id={`file-${title}`}
                type="file"
                accept=".xlsx"
                className="hidden"
                onChange={(e) => {
                  const selectedFile = e.target.files?.[0];
                  if (selectedFile) {
                    onFileChange(selectedFile);
                  }
                }}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Component: Stat Card
function StatCard({
  label,
  value,
  variant = "default",
}: {
  label: string;
  value: string | number;
  variant?: "default" | "success" | "warning";
}) {
  const variantClasses = {
    default: "bg-gray-50 border-gray-200",
    success: "bg-green-50 border-green-200",
    warning: "bg-yellow-50 border-yellow-200",
  };

  return (
    <div className={`border rounded-lg p-4 ${variantClasses[variant]}`}>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

// Component: Scheduled Table
function ScheduledTable({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return <p className="text-center text-muted-foreground py-8">No data to display</p>;
  }

  const displayKeys = ["id", "first", "last", "degree", "major", "audition_date", "audition_time"];

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {displayKeys.map((key) => (
              <TableHead key={key}>{key.replace(/_/g, " ").toUpperCase()}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.slice(0, 20).map((row, i) => (
            <TableRow key={i}>
              {displayKeys.map((key) => (
                <TableCell key={key}>{row[key] || "-"}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {data.length > 20 && (
        <p className="text-center text-sm text-muted-foreground py-2">
          Showing 20 of {data.length} rows. Download the full file to see all results.
        </p>
      )}
    </div>
  );
}

// Component: Conflicts Table
function ConflictsTable({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertTitle>No Conflicts</AlertTitle>
        <AlertDescription>All applicants were successfully scheduled!</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Degree</TableHead>
            <TableHead>Discipline</TableHead>
            <TableHead>Reason Code</TableHead>
            <TableHead>Details</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.slice(0, 20).map((row, i) => (
            <TableRow key={i}>
              <TableCell>{row.applicant_id || row.id || "-"}</TableCell>
              <TableCell>{row.degree || "-"}</TableCell>
              <TableCell>{row.discipline || "-"}</TableCell>
              <TableCell>
                <Badge variant="destructive">{row.reason_code || "-"}</Badge>
              </TableCell>
              <TableCell className="max-w-xs truncate">{row.details || "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {data.length > 20 && (
        <p className="text-center text-sm text-muted-foreground py-2">
          Showing 20 of {data.length} rows. Download the full file to see all conflicts.
        </p>
      )}
    </div>
  );
}
