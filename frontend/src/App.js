import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { useDropzone } from 'react-dropzone';
import { Upload, Download, TrendingUp, TrendingDown, Users, Target, Calendar, DollarSign, BarChart3, PieChart, AlertCircle, CheckCircle2, Sheet, CalendarDays, Search } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, ComposedChart, Area, AreaChart } from 'recharts';
import { DateRangePicker } from '@/components/DateRangePicker';
import { GoogleSheetsUpload } from '@/components/GoogleSheetsUpload';
import { format } from 'date-fns';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
const REVENUE_COLORS = {
  target: '#E5E7EB',
  closed: '#10B981', 
  weighted: '#3B82F6'
};

function FileUpload({ onUploadSuccess }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;
      
      setIsUploading(true);
      setUploadStatus(null);
      
      const formData = new FormData();
      formData.append('file', acceptedFiles[0]);
      
      try {
        const response = await axios.get(`${API}/`);
        const uploadResponse = await axios.post(`${API}/upload-data`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        setUploadStatus({ 
          type: 'success', 
          message: uploadResponse.data.message,
          details: `${uploadResponse.data.records_valid} valid records processed out of ${uploadResponse.data.records_processed}` 
        });
        
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } catch (error) {
        setUploadStatus({ 
          type: 'error', 
          message: 'Upload error', 
          details: error.response?.data?.detail || error.message 
        });
      } finally {
        setIsUploading(false);
      }
    }
  });

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Data Import
        </CardTitle>
        <CardDescription>
          Upload your CSV file with sales data to generate analytics.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-medium mb-2">
            {isDragActive
              ? 'Drop the file here...'
              : 'Drag and drop your CSV file here'}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            or click to select a file (.csv, .xls, .xlsx)
          </p>
          <Button variant="outline" disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Select File'}
          </Button>
        </div>
        
        {uploadStatus && (
          <Alert className={`mt-4 ${uploadStatus.type === 'success' ? 'border-green-500' : 'border-red-500'}`}>
            {uploadStatus.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <AlertDescription>
              <div className="font-medium">{uploadStatus.message}</div>
              <div className="text-sm mt-1">{uploadStatus.details}</div>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

function MetricCard({ title, value, target, unit = '', trend, icon: Icon, color = 'blue' }) {
  const percentage = target ? (value / target * 100) : 0;
  const isOnTrack = percentage >= 90;
  
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 text-${color}-500`} />
            <span className="text-sm font-medium text-gray-600">{title}</span>
          </div>
          {trend && (
            <Badge variant={trend > 0 ? 'default' : 'destructive'}>
              {trend > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {Math.abs(trend)}%
            </Badge>
          )}
        </div>
        <div className="space-y-2">
          <div className="text-2xl font-bold">
            {typeof value === 'number' ? value.toLocaleString() : value} {unit}
          </div>
          {target && (
            <>
              <div className="text-sm text-gray-500">
                Target: {target.toLocaleString()} {unit}
              </div>
              <Progress value={percentage} className="h-2" />
              <div className="flex justify-between text-xs">
                <span className={isOnTrack ? 'text-green-600' : 'text-orange-600'}>
                  {percentage.toFixed(1)}% of target
                </span>
                <Badge variant={isOnTrack ? 'default' : 'secondary'}>
                  {isOnTrack ? 'On Track' : 'Needs Attention'}
                </Badge>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function AnalyticsSection({ title, children, conclusion, isOnTrack }) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {title}
          <Badge variant={isOnTrack ? 'default' : 'secondary'}>
            {isOnTrack ? 'On Track' : 'Needs Improvement'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {children}
        {conclusion && (
          <>
            <Separator className="my-4" />
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Conclusion:</strong> {conclusion}
              </AlertDescription>
            </Alert>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function MeetingsTable({ meetings, title }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  
  const filteredMeetings = meetings.filter(meeting => {
    const matchesSearch = meeting.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         meeting.owner?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || meeting.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search by client or owner..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="Show">Attended</option>
            <option value="Scheduled">Scheduled</option>
            <option value="No Show">No Show</option>
          </select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Client</th>
                <th className="text-left p-2">Meeting Date</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">AE Owner</th>
                <th className="text-left p-2">Stage</th>
                <th className="text-left p-2">Closed Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredMeetings.map((meeting, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="p-2 font-medium">{meeting.client}</td>
                  <td className="p-2">
                    {meeting.meeting_date ? new Date(meeting.meeting_date).toLocaleDateString() : '-'}
                  </td>
                  <td className="p-2">
                    <Badge 
                      variant={meeting.status === 'Show' ? 'default' : 
                              meeting.status === 'Scheduled' ? 'secondary' : 'destructive'}
                    >
                      {meeting.status}
                    </Badge>
                  </td>
                  <td className="p-2">{meeting.owner || '-'}</td>
                  <td className="p-2">
                    <Badge variant="outline">{meeting.stage}</Badge>
                  </td>
                  <td className="p-2">
                    <Badge 
                      variant={meeting.closed_status === 'Closed Won' ? 'default' : 
                              meeting.closed_status === 'Closed Lost' ? 'destructive' : 'secondary'}
                    >
                      {meeting.closed_status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredMeetings.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No meetings found matching the current filters.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function DataManagementSection({ onDataUpdated }) {
  const [dataStatus, setDataStatus] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const loadDataStatus = async () => {
    try {
      const response = await axios.get(`${API}/data/status`);
      setDataStatus(response.data);
    } catch (error) {
      console.error('Error loading data status:', error);
    }
  };

  const handleRefreshGoogleSheet = async () => {
    setIsRefreshing(true);
    try {
      await axios.post(`${API}/data/refresh-google-sheet`);
      await loadDataStatus();
      if (onDataUpdated) onDataUpdated();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleUploadSuccess = async () => {
    await loadDataStatus();
    setShowUpload(false);
    if (onDataUpdated) onDataUpdated();
  };

  useEffect(() => {
    loadDataStatus();
  }, []);

  if (!dataStatus) return null;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Sheet className="h-5 w-5" />
            Data Management
          </CardTitle>
          <div className="flex items-center gap-2">
            {dataStatus.source_type === 'google_sheets' && (
              <Button onClick={handleRefreshGoogleSheet} disabled={isRefreshing} size="sm">
                <Download className="h-4 w-4 mr-2" />
                {isRefreshing ? 'Refreshing...' : 'Refresh Sheet'}
              </Button>
            )}
            <Button onClick={() => setShowUpload(!showUpload)} variant="outline" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              {showUpload ? 'Hide Upload' : 'Upload New Data'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <BarChart3 className="h-8 w-8 text-blue-500" />
            <div>
              <div className="text-sm text-gray-600">Total Records</div>
              <div className="text-lg font-bold">{dataStatus.total_records}</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Calendar className="h-8 w-8 text-green-500" />
            <div>
              <div className="text-sm text-gray-600">Last Updated</div>
              <div className="text-sm font-medium">
                {dataStatus.last_update ? new Date(dataStatus.last_update).toLocaleDateString() : 'Never'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Sheet className="h-8 w-8 text-orange-500" />
            <div>
              <div className="text-sm text-gray-600">Source Type</div>
              <div className="text-sm font-medium">
                {dataStatus.source_type || 'Unknown'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className={`h-3 w-3 rounded-full ${dataStatus.has_data ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <div>
              <div className="text-sm text-gray-600">Status</div>
              <div className="text-sm font-medium">
                {dataStatus.has_data ? 'Data Loaded' : 'No Data'}
              </div>
            </div>
          </div>
        </div>

        {showUpload && (
          <div className="border-t pt-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FileUpload onUploadSuccess={handleUploadSuccess} />
              <GoogleSheetsUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MainDashboard({ analytics }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/analytics/dashboard`);
      setDashboardData(response.data);
      setError(null);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error loading dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleDataUpdated = () => {
    // Refresh dashboard when data is updated
    loadDashboard();
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-500">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <div className="font-medium">Error</div>
          <div className="text-sm mt-1">{error}</div>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Data Management Section */}
      <DataManagementSection onDataUpdated={handleDataUpdated} />
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="YTD Revenue 2025"
          value={dashboardData.key_metrics.ytd_revenue}
          target={dashboardData.key_metrics.ytd_target}
          unit="$"
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="YTD Remaining 2025"
          value={dashboardData.key_metrics.ytd_remaining}
          unit="$"
          icon={AlertCircle}
          color="orange"
        />
        <MetricCard
          title="Weighted Pipeline"
          value={dashboardData.key_metrics.weighted_pipeline}
          unit="$"
          icon={TrendingUp}
          color="purple"
        />
        <MetricCard
          title="Active Deals"
          value={dashboardData.key_metrics.deals_count}
          icon={Target}
          color="blue"
        />
      </div>

      {/* Revenue Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Revenue Performance</CardTitle>
          <CardDescription>
            Target vs Closed Revenue with Weighted Pipeline Forecast
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={dashboardData.monthly_revenue_chart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="target_revenue" fill={REVENUE_COLORS.target} name="Target Revenue" />
              <Bar dataKey="closed_revenue" fill={REVENUE_COLORS.closed} name="Closed Revenue" />
              <Line 
                type="monotone" 
                dataKey="weighted_pipe" 
                stroke={REVENUE_COLORS.weighted} 
                strokeWidth={3}
                name="Weighted Pipeline" 
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* July-December 2025 Targets Chart */}
      <Card>
        <CardHeader>
          <CardTitle>July-December 2025 Revenue Targets</CardTitle>
          <CardDescription>
            Monthly and Cumulative Progress vs Targets for H2 2025
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <MetricCard
              title="H2 2025 Target"
              value={dashboardData.key_metrics.annual_target_2025}
              unit="$"
              icon={Target}
              color="blue"
            />
            <MetricCard
              title="Jul-Dec Closed 2025"
              value={dashboardData.key_metrics.ytd_closed_2025}
              target={dashboardData.key_metrics.annual_target_2025}
              unit="$"
              icon={CheckCircle2}
              color="green"
            />
            <MetricCard
              title="Remaining H2 Target"
              value={dashboardData.key_metrics.annual_target_2025 - dashboardData.key_metrics.ytd_closed_2025}
              unit="$"
              icon={AlertCircle}
              color="orange"
            />
          </div>
          
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={dashboardData.annual_targets_2025}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="monthly_target" fill="#E5E7EB" name="Monthly Target" />
              <Bar dataKey="monthly_closed" fill="#10B981" name="Monthly Closed" />
              <Line 
                type="monotone" 
                dataKey="cumulative_target" 
                stroke="#6B7280" 
                strokeWidth={3}
                name="Cumulative Target" 
              />
              <Line 
                type="monotone" 
                dataKey="cumulative_closed" 
                stroke="#059669" 
                strokeWidth={3}
                name="Cumulative Closed" 
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 4 Dashboard Blocks */}
      {analytics?.dashboard_blocks && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Block 1: Meeting Generation */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">Meeting Generation</CardTitle>
              <CardDescription className="text-center font-medium text-blue-600">
                {analytics.dashboard_blocks.block_1_meetings.period}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {analytics.dashboard_blocks.block_1_meetings.total_actual}/{analytics.dashboard_blocks.block_1_meetings.total_target}
                  </div>
                  <div className="text-sm text-gray-600">Total Target</div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Inbound:</span>
                    <span className="font-medium">{analytics.dashboard_blocks.block_1_meetings.inbound_actual}/{analytics.dashboard_blocks.block_1_meetings.inbound_target}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Outbound:</span>
                    <span className="font-medium">{analytics.dashboard_blocks.block_1_meetings.outbound_actual}/{analytics.dashboard_blocks.block_1_meetings.outbound_target}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Referral:</span>
                    <span className="font-medium">{analytics.dashboard_blocks.block_1_meetings.referral_actual}/{analytics.dashboard_blocks.block_1_meetings.referral_target}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 2: Discovery & POA */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">Discovery & POA</CardTitle>
              <CardDescription className="text-center font-medium text-green-600">
                {analytics.dashboard_blocks.block_2_discovery_poa.period}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {analytics.dashboard_blocks.block_2_discovery_poa.discovery_actual}/{analytics.dashboard_blocks.block_2_discovery_poa.discovery_target}
                  </div>
                  <div className="text-sm text-gray-600">Discovery</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {analytics.dashboard_blocks.block_2_discovery_poa.poa_actual}/{analytics.dashboard_blocks.block_2_discovery_poa.poa_target}
                  </div>
                  <div className="text-sm text-gray-600">POA</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 3: New Pipe Created */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">New Pipe Created</CardTitle>
              <CardDescription className="text-center font-medium text-purple-600">
                {analytics.dashboard_blocks.block_3_pipe_creation.period}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-600">
                    ${(analytics.dashboard_blocks.block_3_pipe_creation.new_pipe_created / 1000000).toFixed(1)}M
                  </div>
                  <div className="text-xs text-gray-600">New Pipe This Month</div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-700">
                    Target: $2M/month
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-bold text-blue-600">
                    ${(analytics.dashboard_blocks.block_3_pipe_creation.weighted_pipe_created / 1000).toFixed(0)}K
                  </div>
                  <div className="text-xs text-gray-600">Weighted Pipe</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 4: Revenue Objective */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">Revenue Objective</CardTitle>
              <CardDescription className="text-center font-medium text-gray-600">
                {analytics.dashboard_blocks.block_4_revenue.period}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-600">
                    ${(analytics.dashboard_blocks.block_4_revenue.revenue_target / 1000).toFixed(0)}K
                  </div>
                  <div className="text-xs text-gray-600">Target</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">
                    ${(analytics.dashboard_blocks.block_4_revenue.closed_revenue / 1000).toFixed(0)}K
                  </div>
                  <div className="text-xs text-gray-600">Closed</div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full" 
                    style={{ width: `${Math.min(analytics.dashboard_blocks.block_4_revenue.progress, 100)}%` }}
                  ></div>
                </div>
                <div className="text-center text-xs text-gray-600">
                  {analytics.dashboard_blocks.block_4_revenue.progress.toFixed(1)}% Complete
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [monthOffset, setMonthOffset] = useState(0);
  const [dateRange, setDateRange] = useState(null);
  const [useCustomDate, setUseCustomDate] = useState(false);
  const [importMethod, setImportMethod] = useState('csv'); // 'csv' or 'sheets'
  const [viewMode, setViewMode] = useState('monthly'); // 'monthly' or 'yearly'

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (useCustomDate && dateRange?.from && dateRange?.to) {
        // Use custom date range
        const startDate = format(dateRange.from, 'yyyy-MM-dd');
        const endDate = format(dateRange.to, 'yyyy-MM-dd');
        response = await axios.get(`${API}/analytics/custom?start_date=${startDate}&end_date=${endDate}`);
      } else if (viewMode === 'yearly') {
        // Use yearly view
        response = await axios.get(`${API}/analytics/yearly?year=2025`);
      } else {
        // Use monthly offset
        response = await axios.get(`${API}/analytics/monthly?month_offset=${monthOffset}`);
      }
      
      setAnalytics(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [monthOffset, dateRange, useCustomDate, viewMode]);

  const handleUploadSuccess = () => {
    loadAnalytics();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg font-medium">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Sales Analytics Dashboard</h1>
          <p className="text-gray-600">Analyze your sales performance with detailed reports</p>
        </div>
        
        {/* Import Method Selector */}
        <div className="mb-6">
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant={importMethod === 'csv' ? 'default' : 'outline'}
              onClick={() => setImportMethod('csv')}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload CSV/Excel
            </Button>
            <Button
              variant={importMethod === 'sheets' ? 'default' : 'outline'}
              onClick={() => setImportMethod('sheets')}
              className="flex items-center gap-2"
            >
              <Sheet className="h-4 w-4" />
              Google Sheets
            </Button>
          </div>
          
          {importMethod === 'csv' ? (
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          ) : (
            <GoogleSheetsUpload onUploadSuccess={handleUploadSuccess} />
          )}
        </div>
        
        <Alert className="border-red-500">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-medium">Error</div>
            <div className="text-sm mt-1">{error}</div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Sales Analytics Dashboard</h1>
          <p className="text-gray-600">Analyze your sales performance with detailed reports</p>
        </div>
        
        {/* Import Method Selector */}
        <div className="mb-6">
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant={importMethod === 'csv' ? 'default' : 'outline'}
              onClick={() => setImportMethod('csv')}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload CSV/Excel
            </Button>
            <Button
              variant={importMethod === 'sheets' ? 'default' : 'outline'}
              onClick={() => setImportMethod('sheets')}
              className="flex items-center gap-2"
            >
              <Sheet className="h-4 w-4" />
              Google Sheets
            </Button>
          </div>
          
          {importMethod === 'csv' ? (
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          ) : (
            <GoogleSheetsUpload onUploadSuccess={handleUploadSuccess} />
          )}
        </div>
      </div>
    );
  }

  const periodStart = new Date(analytics.week_start);
  const periodEnd = new Date(analytics.week_end);
  
  // Prepare chart data
  const sourceData = [
    { name: 'Inbound', value: analytics.meeting_generation.inbound },
    { name: 'Outbound', value: analytics.meeting_generation.outbound },
    { name: 'Referrals', value: analytics.meeting_generation.referrals }
  ];

  const relevanceData = [
    { name: 'Relevant', value: analytics.meeting_generation.relevance_analysis.relevant, color: '#00C49F' },
    { name: 'Questionable', value: analytics.meeting_generation.relevance_analysis.question_mark, color: '#FFBB28' },
    { name: 'Not Relevant', value: analytics.meeting_generation.relevance_analysis.not_relevant, color: '#FF8042' }
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">
            {useCustomDate ? 'Custom Report' : 
             viewMode === 'yearly' ? 'Yearly Report 2025' : 'Monthly Report'}
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Button
                variant={!useCustomDate && viewMode === 'monthly' ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setUseCustomDate(false);
                  setViewMode('monthly');
                }}
                className="flex items-center gap-1"
              >
                <Calendar className="h-4 w-4" />
                Monthly
              </Button>
              <Button
                variant={!useCustomDate && viewMode === 'yearly' ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setUseCustomDate(false);
                  setViewMode('yearly');
                }}
                className="flex items-center gap-1"
              >
                <CalendarDays className="h-4 w-4" />
                Yearly
              </Button>
              <Button
                variant={useCustomDate ? 'default' : 'outline'}
                size="sm"
                onClick={() => setUseCustomDate(true)}
                className="flex items-center gap-1"
              >
                <CalendarDays className="h-4 w-4" />
                Custom Period
              </Button>
            </div>
            {!useCustomDate && viewMode === 'monthly' && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setMonthOffset(monthOffset + 1)}
                >
                  ← Previous Month
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setMonthOffset(monthOffset - 1)}
                  disabled={monthOffset <= 0}
                >
                  Next Month →
                </Button>
              </div>
            )}
            {useCustomDate && (
              <DateRangePicker 
                dateRange={dateRange}
                onDateChange={(range) => setDateRange(range)}
                className="w-auto"
              />
            )}
            <Button onClick={loadAnalytics} size="sm">
              Refresh
            </Button>
          </div>
        </div>
        <p className="text-gray-600">
          Period: {periodStart.toLocaleDateString('en-US')} - {periodEnd.toLocaleDateString('en-US')}
        </p>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="meetings">Meeting Generation</TabsTrigger>
          <TabsTrigger value="attended">Meetings Attended</TabsTrigger>
          <TabsTrigger value="deals">Deals & Pipeline</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
        </TabsList>

        {/* Main Dashboard */}
        <TabsContent value="dashboard">
          <MainDashboard analytics={analytics} />
        </TabsContent>

        {/* Meeting Generation */}
        <TabsContent value="meetings">
          <AnalyticsSection 
            title="Meeting Generation (Current Period)"
            isOnTrack={analytics.meeting_generation.on_track}
            conclusion={analytics.meeting_generation.on_track 
              ? "You are on track to meet your meeting generation targets." 
              : "Need to increase prospecting efforts to reach targets."}
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <MetricCard
                title="Total New Intros"
                value={analytics.meeting_generation.total_new_intros}
                target={analytics.meeting_generation.target}
                icon={Users}
                color="blue"
              />
              <MetricCard
                title="Inbound"
                value={analytics.meeting_generation.inbound}
                icon={TrendingUp}
                color="green"
              />
              <MetricCard
                title="Outbound"
                value={analytics.meeting_generation.outbound}
                icon={Target}
                color="orange"
              />
              <MetricCard
                title="Referrals"
                value={analytics.meeting_generation.referrals}
                icon={Users}
                color="purple"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Card>
                <CardHeader>
                  <CardTitle>Source Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={sourceData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {sourceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Relevance Analysis</CardTitle>
                  <CardDescription>
                    Relevance Rate: {analytics.meeting_generation.relevance_analysis.relevance_rate.toFixed(1)}%
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {relevanceData.map((item, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-4 h-4 rounded" 
                            style={{ backgroundColor: item.color }}
                          ></div>
                          <span className="font-medium">{item.name}</span>
                        </div>
                        <span className="font-bold">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Meetings Details Table */}
            {analytics.meeting_generation.meetings_details && analytics.meeting_generation.meetings_details.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Meeting Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-semibold">Date</th>
                          <th className="text-left p-2 font-semibold">Client / Prospect</th>
                          <th className="text-left p-2 font-semibold">Owner (BDR)</th>
                          <th className="text-left p-2 font-semibold">Source</th>
                          <th className="text-center p-2 font-semibold">Relevance</th>
                          <th className="text-left p-2 font-semibold">Owner</th>
                          <th className="text-left p-2 font-semibold">Stage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.meeting_generation.meetings_details.map((meeting, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-2">{meeting.date}</td>
                            <td className="p-2 font-medium">{meeting.client}</td>
                            <td className="p-2">{meeting.bdr}</td>
                            <td className="p-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                meeting.source === 'Inbound' ? 'bg-blue-100 text-blue-800' :
                                meeting.source === 'Outbound' ? 'bg-green-100 text-green-800' :
                                meeting.source.includes('referral') ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {meeting.source}
                              </span>
                            </td>
                            <td className="p-2 text-center">
                              <span className={`inline-flex items-center w-3 h-3 rounded-full ${
                                meeting.relevance === 'Relevant' ? 'bg-green-500' :
                                meeting.relevance === 'Question mark' || meeting.relevance === 'Maybe' ? 'bg-yellow-500' :
                                meeting.relevance === 'Not relevant' ? 'bg-red-500' :
                                'bg-gray-500'
                              }`}></span>
                            </td>
                            <td className="p-2">{meeting.owner}</td>
                            <td className="p-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                meeting.stage?.includes('Won') || meeting.stage?.includes('Closed Won') ? 'bg-green-100 text-green-800' :
                                meeting.stage?.includes('Lost') ? 'bg-red-100 text-red-800' :
                                meeting.stage?.includes('POA') || meeting.stage?.includes('Legal') ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {meeting.stage}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* BDR Performance */}
            {Object.keys(analytics.meeting_generation.bdr_performance).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>BDR Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">BDR</th>
                          <th className="text-right p-2">Total Meetings</th>
                          <th className="text-right p-2">Relevant Meetings</th>
                          <th className="text-right p-2">Relevance Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(analytics.meeting_generation.bdr_performance).map(([bdr, stats]) => (
                          <tr key={bdr} className="border-b">
                            <td className="p-2 font-medium">{bdr}</td>
                            <td className="text-right p-2">{stats.total_meetings}</td>
                            <td className="text-right p-2">{stats.relevant_meetings}</td>
                            <td className="text-right p-2">
                              {((stats.relevant_meetings / stats.total_meetings) * 100).toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </AnalyticsSection>
        </TabsContent>

        {/* Meetings Attended */}
        <TabsContent value="attended">
          <AnalyticsSection 
            title="Meetings Attended (Current Period)"
            isOnTrack={analytics.meetings_attended.on_track}
            conclusion={analytics.meetings_attended.on_track 
              ? "Good performance on meeting attendance and conversions." 
              : "Need to improve attendance rates and conversions."}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <MetricCard
                title="Meetings Scheduled"
                value={analytics.meetings_attended.intro_metrics.scheduled}
                target={analytics.meetings_attended.intro_metrics.target}
                icon={Calendar}
                color="blue"
              />
              <MetricCard
                title="Meetings Attended"
                value={analytics.meetings_attended.intro_metrics.attended}
                icon={CheckCircle2}
                color="green"
              />
              <MetricCard
                title="Attendance Rate"
                value={analytics.meetings_attended.intro_metrics.attendance_rate.toFixed(1)}
                unit="%"
                icon={BarChart3}
                color="orange"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <MetricCard
                title="Discoveries Completed"
                value={analytics.meetings_attended.discovery_metrics.completed}
                target={analytics.meetings_attended.discovery_metrics.target}
                icon={Target}
                color="purple"
              />
              <MetricCard
                title="POAs Generated"
                value={analytics.meetings_attended.poa_metrics.generated}
                target={analytics.meetings_attended.poa_metrics.target}
                icon={DollarSign}
                color="green"
              />
            </div>

            {/* Meetings Detail Table */}
            {analytics.meetings_attended.meetings_detail && analytics.meetings_attended.meetings_detail.length > 0 && (
              <MeetingsTable 
                meetings={analytics.meetings_attended.meetings_detail}
                title="All Meetings Detail"
              />
            )}

            {/* AE Performance */}
            {Object.keys(analytics.meetings_attended.ae_performance).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>AE Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">AE</th>
                          <th className="text-right p-2">Scheduled</th>
                          <th className="text-right p-2">Attended</th>
                          <th className="text-right p-2">POAs Generated</th>
                          <th className="text-right p-2">Conversion Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(analytics.meetings_attended.ae_performance).map(([ae, stats]) => (
                          <tr key={ae} className="border-b">
                            <td className="p-2 font-medium">{ae}</td>
                            <td className="text-right p-2">{stats.total_scheduled}</td>
                            <td className="text-right p-2">{stats.attended}</td>
                            <td className="text-right p-2">{stats.poa_generated}</td>
                            <td className="text-right p-2">
                              {stats.attended > 0 ? ((stats.poa_generated / stats.attended) * 100).toFixed(1) : 0}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </AnalyticsSection>
        </TabsContent>

        {/* Deals & Pipeline */}
        <TabsContent value="deals">
          <div className="space-y-6">
            {/* Deals Closed */}
            <AnalyticsSection 
              title="Deals Closed (Current Period)"
              isOnTrack={analytics.deals_closed.on_track}
              conclusion={analytics.deals_closed.on_track 
                ? "Excellent performance on deal closing this period." 
                : "Need to accelerate deal closing efforts."}
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <MetricCard
                  title="Deals Closed"
                  value={analytics.deals_closed.deals_closed}
                  target={analytics.deals_closed.target_deals}
                  icon={CheckCircle2}
                  color="green"
                />
                <MetricCard
                  title="ARR Closed"
                  value={analytics.deals_closed.arr_closed}
                  target={analytics.deals_closed.target_arr}
                  unit="$"
                  icon={DollarSign}
                  color="green"
                />
                <MetricCard
                  title="MRR Closed"
                  value={analytics.deals_closed.mrr_closed}
                  unit="$"
                  icon={TrendingUp}
                  color="blue"
                />
                <MetricCard
                  title="Average Deal Size"
                  value={analytics.deals_closed.avg_deal_size}
                  unit="$"
                  icon={BarChart3}
                  color="purple"
                />
              </div>

              {/* Monthly Closed Chart */}
              {analytics.deals_closed.monthly_closed && analytics.deals_closed.monthly_closed.length > 0 && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>Monthly Deals Closed Trend</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={analytics.deals_closed.monthly_closed}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => typeof value === 'number' && value > 1000 ? `$${value.toLocaleString()}` : value} />
                        <Legend />
                        <Bar dataKey="deals_count" fill="#8884d8" name="Deals Count" />
                        <Line type="monotone" dataKey="arr_closed" stroke="#82ca9d" strokeWidth={3} name="ARR Closed" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}

              {analytics.deals_closed.deals_detail.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Closed Deals Detail</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Client</th>
                            <th className="text-right p-2">ARR</th>
                            <th className="text-left p-2">Owner</th>
                            <th className="text-left p-2">Deal Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.deals_closed.deals_detail.map((deal, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2 font-medium">{deal.client}</td>
                              <td className="text-right p-2">${deal.expected_arr?.toLocaleString()}</td>
                              <td className="p-2">{deal.owner}</td>
                              <td className="p-2">
                                <Badge variant="outline">{deal.type_of_deal}</Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </AnalyticsSection>

            {/* Pipeline Metrics */}
            <AnalyticsSection 
              title="Pipeline Metrics"
              isOnTrack={analytics.pipe_metrics.total_aggregate_pipe.on_track}
              conclusion={analytics.pipe_metrics.total_aggregate_pipe.on_track 
                ? "Total pipeline is healthy and meeting targets." 
                : "Need to strengthen pipeline generation to meet targets."}
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <MetricCard
                  title="New Pipeline Created"
                  value={analytics.pipe_metrics.new_pipe_created.value}
                  target={analytics.pipe_metrics.new_pipe_created.target}
                  unit="$"
                  icon={TrendingUp}
                  color="green"
                />
                <MetricCard
                  title="Hot Pipeline"
                  value={analytics.pipe_metrics.hot_pipe.value}
                  target={analytics.pipe_metrics.hot_pipe.target}
                  unit="$"
                  icon={DollarSign}
                  color="orange"
                />
                <MetricCard
                  title="Total Pipeline"
                  value={analytics.pipe_metrics.total_aggregate_pipe.value}
                  target={analytics.pipe_metrics.total_aggregate_pipe.target}
                  unit="$"
                  icon={BarChart3}
                  color="blue"
                />
              </div>

              {analytics.pipe_metrics.hot_pipe.deals.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Hot Pipeline Deals</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Client</th>
                            <th className="text-right p-2">Value</th>
                            <th className="text-left p-2">Stage</th>
                            <th className="text-left p-2">Owner</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.pipe_metrics.hot_pipe.deals.map((deal, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2 font-medium">{deal.client}</td>
                              <td className="text-right p-2">${deal.pipeline?.toLocaleString()}</td>
                              <td className="p-2">
                                <Badge variant="outline">{deal.stage}</Badge>
                              </td>
                              <td className="p-2">{deal.owner}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </AnalyticsSection>

            {/* Old Pipeline */}
            <Card>
              <CardHeader>
                <CardTitle>Old Pipeline (Reactivation Opportunities)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <MetricCard
                    title="Stalled Deals"
                    value={analytics.old_pipe.total_stalled_deals}
                    icon={AlertCircle}
                    color="orange"
                  />
                  <MetricCard
                    title="Total Value"
                    value={analytics.old_pipe.total_stalled_value}
                    unit="$"
                    icon={DollarSign}
                    color="red"
                  />
                  <MetricCard
                    title="Companies to Recontact"
                    value={analytics.old_pipe.companies_to_recontact}
                    icon={Users}
                    color="blue"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Projections */}
        <TabsContent value="projections">
          <div className="space-y-6">
            {/* Closing Projections */}
            <Card>
              <CardHeader>
                <CardTitle>Closing Projections</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Next 7 Days</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        ${analytics.closing_projections.next_7_days.total_value.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Weighted Value: ${analytics.closing_projections.next_7_days.weighted_value.toLocaleString()}
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.next_7_days.deals.length} potential deals
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">This Month</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        ${analytics.closing_projections.current_month.total_value.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Weighted Value: ${analytics.closing_projections.current_month.weighted_value.toLocaleString()}
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.current_month.deals.length} potential deals
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">This Quarter</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        ${analytics.closing_projections.next_quarter.total_value.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Weighted Value: ${analytics.closing_projections.next_quarter.weighted_value.toLocaleString()}
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.next_quarter.deals.length} potential deals
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Projection par AE */}
                {Object.keys(analytics.closing_projections.ae_projections).length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Projections by AE</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">AE</th>
                              <th className="text-right p-2">Total Pipeline</th>
                              <th className="text-right p-2">Weighted Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(analytics.closing_projections.ae_projections).map(([ae, stats]) => (
                              <tr key={ae} className="border-b">
                                <td className="p-2 font-medium">{ae}</td>
                                <td className="text-right p-2">${stats.pipeline?.toLocaleString()}</td>
                                <td className="text-right p-2">${stats.weighted_value?.toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>

            {/* Big Numbers Recap */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <MetricCard
                    title="YTD Revenue"
                    value={analytics.big_numbers_recap.ytd_revenue}
                    target={analytics.big_numbers_recap.ytd_target}
                    unit="$"
                    icon={DollarSign}
                    color="green"
                  />
                  <MetricCard
                    title="Remaining Target"
                    value={analytics.big_numbers_recap.remaining_target}
                    unit="$"
                    icon={Target}
                    color="orange"
                  />
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="h-5 w-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-600">Target Status</span>
                      </div>
                      <Badge 
                        variant={analytics.big_numbers_recap.forecast_gap ? 'destructive' : 'default'}
                        className="text-sm"
                      >
                        {analytics.big_numbers_recap.forecast_gap 
                          ? 'Forecast Gap Detected' 
                          : 'On Track'}
                      </Badge>
                    </CardContent>
                  </Card>
                </div>

                {analytics.big_numbers_recap.forecast_gap && (
                  <Alert className="border-orange-500">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Action Required:</strong> Need to intensify efforts to close the gap of 
                      ${analytics.big_numbers_recap.remaining_target.toLocaleString()} and achieve annual targets.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

      </Tabs>
      </Tabs>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;