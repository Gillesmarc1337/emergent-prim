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
import { Upload, Download, TrendingUp, TrendingDown, Users, Target, Calendar, DollarSign, BarChart3, PieChart, AlertCircle, CheckCircle2, Sheet, CalendarDays, Search, X, RotateCcw, ChevronUp, ChevronDown, FileText, CheckCircle } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, ComposedChart, Area, AreaChart } from 'recharts';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { DateRangePicker } from '@/components/DateRangePicker';
import { GoogleSheetsUpload } from '@/components/GoogleSheetsUpload';
import { format } from 'date-fns';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import Header from './components/Header';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
const REVENUE_COLORS = {
  target: '#F59E0B',
  closed: '#10B981', 
  weighted: '#3B82F6',
  new_weighted: '#D97706',
  aggregate_weighted: '#4ECDC4'
};

// Custom hook for table sorting
function useSortableData(items, config = null) {
  const [sortConfig, setSortConfig] = useState(config);

  const sortedItems = React.useMemo(() => {
    let sortableItems = [...items];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        // Handle different data types
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        
        // Numeric comparison
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          if (aValue < bValue) {
            return sortConfig.direction === 'ascending' ? -1 : 1;
          }
          if (aValue > bValue) {
            return sortConfig.direction === 'ascending' ? 1 : -1;
          }
          return 0;
        }
        
        // String comparison (case insensitive)
        const aString = String(aValue).toLowerCase();
        const bString = String(bValue).toLowerCase();
        if (aString < bString) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aString > bString) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [items, sortConfig]);

  const requestSort = (key) => {
    let direction = 'ascending';
    if (
      sortConfig &&
      sortConfig.key === key &&
      sortConfig.direction === 'ascending'
    ) {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  return { items: sortedItems, requestSort, sortConfig };
}

// Sortable Table Header Component
function SortableTableHeader({ children, sortKey, requestSort, sortConfig, className = "" }) {
  const getSortIcon = () => {
    if (!sortConfig || sortConfig.key !== sortKey) {
      return <ChevronUp className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100" />;
    }
    return sortConfig.direction === 'ascending' 
      ? <ChevronUp className="h-3 w-3 text-blue-600" /> 
      : <ChevronDown className="h-3 w-3 text-blue-600" />;
  };

  return (
    <th 
      className={`cursor-pointer hover:bg-gray-100 transition-colors group ${className}`}
      onClick={() => requestSort(sortKey)}
    >
      <div className="flex items-center justify-between">
        <span>{children}</span>
        {getSortIcon()}
      </div>
    </th>
  );
}

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

function MetricCard({ title, value, target, unit = '', trend, icon: Icon, color = 'blue', statusBadge }) {
  const percentage = target ? (value / target * 100) : 0;
  const isOnTrack = percentage >= 90;
  
  // Use custom statusBadge if provided, otherwise default logic
  const displayBadge = statusBadge || (isOnTrack ? 'On Track' : 'Needs Attention');
  const badgeVariant = displayBadge === 'On Track' ? 'default' : 'secondary';
  
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
                <span className={percentage >= 80 ? 'text-green-600' : percentage >= 60 ? 'text-orange-600' : 'text-red-600'}>
                  {percentage.toFixed(1)}% of target
                </span>
                <Badge variant={badgeVariant} className={
                  displayBadge === 'On Track' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                }>
                  {displayBadge}
                </Badge>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function DraggableDealItem({ deal, index, onHide, showActions = false }) {
  const [isVisible, setIsVisible] = useState(true);
  const [status, setStatus] = useState(deal.status || 'active');
  const [label, setLabel] = useState(deal.label || '');

  if (!isVisible || status === 'won' || status === 'lost') return null;

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    // Visual only - no backend update
  };

  const handleDelete = () => {
    setIsVisible(false);
    if (onHide) onHide();
  };

  return (
    <Draggable draggableId={deal.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`bg-white border-l-4 border-l-green-500 p-4 mb-2 rounded shadow-sm hover:shadow-md transition-shadow ${
            snapshot.isDragging ? 'rotate-2 scale-105' : ''
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="font-medium">{deal.client}</div>
              <div className="text-sm text-gray-600">
                AE: {deal.owner} | Pipeline: ${deal.pipeline?.toLocaleString()}
              </div>
              {deal.poa_date && (
                <div className="text-xs text-blue-600">
                  POA: {new Date(deal.poa_date).toLocaleDateString()}
                </div>
              )}
              {label && (
                <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded mt-1 inline-block">
                  {label}
                </div>
              )}
            </div>
            
            {showActions && (
              <div className="flex gap-1 ml-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleStatusChange('won')}
                  className="text-green-600 hover:text-green-700"
                  title="Mark as Won"
                >
                  ✓
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleStatusChange('lost')}
                  className="text-red-600 hover:text-red-700"
                  title="Mark as Lost"
                >
                  ✗
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDelete}
                  className="text-gray-600 hover:text-gray-700"
                  title="Remove from board"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </Draggable>
  );
}

function DealItemContent({ deal }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <div className="font-medium">{deal.client}</div>
        <div className="text-sm text-gray-600">
          AE: {deal.owner} | Pipeline: ${deal.pipeline?.toLocaleString()}
        </div>
      </div>
    </div>
  );
}

function DraggableLeadItem({ lead, index, onHide }) {
  return (
    <Draggable draggableId={lead.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`p-3 bg-white border rounded-lg shadow-sm mb-2 ${
            snapshot.isDragging ? 'shadow-lg' : 'hover:shadow-md'
          } transition-shadow`}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1 grid grid-cols-4 gap-2">
              <div className="font-medium">{lead.client}</div>
              <div className="text-sm text-gray-600">AE: {lead.owner}</div>
              <div className="text-sm text-green-600">MRR: ${lead.expected_mrr?.toLocaleString()}</div>
              <div className="text-sm text-blue-600">ARR: ${lead.expected_arr?.toLocaleString()}</div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onHide(lead.id);
              }}
              className="text-red-500 hover:text-red-700"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </Draggable>
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

  const { items: sortedMeetings, requestSort, sortConfig } = useSortableData(filteredMeetings);

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
                <SortableTableHeader sortKey="client" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  Client
                </SortableTableHeader>
                <SortableTableHeader sortKey="meeting_date" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  Meeting Date
                </SortableTableHeader>
                <SortableTableHeader sortKey="status" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  Status
                </SortableTableHeader>
                <SortableTableHeader sortKey="owner" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  AE Owner
                </SortableTableHeader>
                <SortableTableHeader sortKey="stage" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  Stage
                </SortableTableHeader>
                <SortableTableHeader sortKey="closed_status" requestSort={requestSort} sortConfig={sortConfig} className="text-left p-2">
                  Closed Status
                </SortableTableHeader>
              </tr>
            </thead>
            <tbody>
              {sortedMeetings.map((meeting, index) => (
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
          {sortedMeetings.length === 0 && (
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
  
  // State for chart series visibility
  const [visibleSeries, setVisibleSeries] = useState({
    'Closed Revenue': true,
    'Target Revenue': false,  // Hidden by default
    'New Weighted Pipe': false,  // Hidden by default  
    'Aggregate Weighted Pipe': true
  });

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

  // Handle legend click to toggle series visibility
  const handleLegendClick = (dataKey) => {
    setVisibleSeries(prev => ({
      ...prev,
      [dataKey]: !prev[dataKey]
    }));
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
        {(() => {
          // Calculate period duration for dynamic targets
          const monthlyData = dashboardData.monthly_revenue_chart || [];
          const periodMonths = Math.max(1, monthlyData.length); // Number of months in period
          
          // Base monthly targets
          const baseNewPipeTarget = 2000000; // $2M per month
          const baseAggregateWeightedTarget = 800000; // $800K per month
          
          // Dynamic targets
          const newPipeTarget = baseNewPipeTarget * periodMonths;
          const aggregateWeightedTarget = baseAggregateWeightedTarget * periodMonths;
          
          // Period description
          const periodDescription = periodMonths === 6 ? "Jul–Dec 2025 (6 months)" : 
                                  periodMonths === 1 ? "Current Month (1 month)" :
                                  `Selected Period (${periodMonths} months)`;
          
          return (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-purple-500" />
                    <span className="text-sm font-medium text-gray-600">New Pipe Created (Selected Period)</span>
                  </div>
                </div>
                
                <div className="text-xs text-gray-500 mb-3">{periodDescription}</div>
                
                <div className="space-y-4">
                  {/* 1. Total New Pipe Generated */}
                  <div>
                    <div className="text-lg font-bold">
                      ${(dashboardData.key_metrics.pipe_created / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-500">Total New Pipe Generated</div>
                    <div className="text-xs text-gray-400">Target: ${(newPipeTarget / 1000000).toFixed(1)}M</div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                      <div 
                        className="bg-purple-500 h-1 rounded-full" 
                        style={{ width: `${Math.min((dashboardData.key_metrics.pipe_created / newPipeTarget) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  {/* 2. New Weighted Pipe */}
                  <div>
                    <div className="text-sm font-bold text-blue-600">
                      ${(dashboardData.dashboard_blocks?.block_3_pipe_creation?.weighted_pipe_created / 1000000 || 0).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-500">New Weighted Pipe</div>
                  </div>
                  
                  {/* 3. Aggregate Weighted Pipe */}
                  <div>
                    <div className="text-sm font-bold text-green-600">
                      ${(dashboardData.key_metrics.weighted_pipeline / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-500">Aggregate Weighted Pipe</div>
                    <div className="text-xs text-gray-400">Target: ${(aggregateWeightedTarget / 1000000).toFixed(1)}M</div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                      <div 
                        className="bg-green-500 h-1 rounded-full" 
                        style={{ width: `${Math.min((dashboardData.key_metrics.weighted_pipeline / aggregateWeightedTarget) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                {/* Tooltip info */}
                <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                  <div className="font-medium mb-1">📊 Includes all deals created in period</div>
                  <div>• Weighted: Excel logic (Stage × Source × Recency)</div>
                  <div>• Targets: 2M New Pipe + 800K Aggregate per month</div>
                </div>
              </CardContent>
            </Card>
          );
        })()}
        <MetricCard
          title="Active Deals"
          value={dashboardData.key_metrics.deals_count}
          icon={Users}
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
            <BarChart data={dashboardData.monthly_revenue_chart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              {visibleSeries['Closed Revenue'] && (
                <Bar dataKey="closed_revenue" fill={REVENUE_COLORS.closed} name="Closed Revenue" />
              )}
              {visibleSeries['Target Revenue'] && (
                <Bar dataKey="target_revenue" fill={REVENUE_COLORS.target} name="Target Revenue" />
              )}
              {visibleSeries['New Weighted Pipe'] && (
                <Bar dataKey="new_weighted_pipe" fill="#D97706" name="New Weighted Pipe" />
              )}
              {visibleSeries['Aggregate Weighted Pipe'] && (
                <Bar 
                  dataKey="aggregate_weighted_pipe" 
                  fill="#4ECDC4" 
                  name="Aggregate Weighted Pipe"
                />
              )}
            </BarChart>
          </ResponsiveContainer>
          
          {/* Custom Legend */}
          <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
            {Object.entries(visibleSeries).map(([seriesName, isVisible]) => {
              const colors = {
                'Closed Revenue': REVENUE_COLORS.closed,
                'Target Revenue': REVENUE_COLORS.target,
                'New Weighted Pipe': '#D97706',
                'Aggregate Weighted Pipe': '#4ECDC4'
              };
              
              return (
                <button
                  key={seriesName}
                  onClick={() => handleLegendClick(seriesName)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                    isVisible 
                      ? 'bg-white shadow-sm border border-gray-200' 
                      : 'bg-gray-100 opacity-60 hover:opacity-80'
                  }`}
                >
                  <div 
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: colors[seriesName] }}
                  />
                  <span className={`text-sm ${isVisible ? 'text-gray-700 font-medium' : 'text-gray-500'}`}>
                    {seriesName}
                  </span>
                </button>
              );
            })}
          </div>
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
              <CardTitle className="text-lg text-center">Meetings Generation</CardTitle>
              <CardDescription className="text-center font-medium text-blue-600">
                {analytics.dashboard_blocks?.block_1_meetings?.period || 'Current Period'}
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
                  <div className="flex justify-between">
                    <span>Upsells / Cross-sell:</span>
                    <span className="font-medium text-purple-600">{analytics.dashboard_blocks.block_1_meetings.upsells_actual}/{analytics.dashboard_blocks.block_1_meetings.upsells_target}</span>
                  </div>
                  {analytics.dashboard_blocks.block_1_meetings.unassigned_actual > 0 && (
                    <div className="flex justify-between">
                      <span>Unassigned:</span>
                      <span className="font-medium text-orange-600">{analytics.dashboard_blocks.block_1_meetings.unassigned_actual}</span>
                    </div>
                  )}
                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between">
                      <span>Show:</span>
                      <span className="font-medium text-green-600">{analytics.dashboard_blocks.block_1_meetings.show_actual}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>No Show:</span>
                      <span className="font-medium text-red-600">{analytics.dashboard_blocks.block_1_meetings.no_show_actual}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 2: Intro & POA */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">Intro & POA</CardTitle>
              <CardDescription className="text-center font-medium text-green-600">
                {analytics.dashboard_blocks?.block_2_intro_poa?.period || 'Current Period'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {analytics.dashboard_blocks.block_2_intro_poa.intro_actual}/{analytics.dashboard_blocks.block_2_intro_poa.intro_target}
                  </div>
                  <div className="text-sm text-gray-600">Intro</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {analytics.dashboard_blocks.block_2_intro_poa.poa_actual}/{analytics.dashboard_blocks.block_2_intro_poa.poa_target}
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
                {analytics.dashboard_blocks?.block_3_pipe_creation?.period || 'Current Period'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-600">
                    ${(analytics.dashboard_blocks.block_3_pipe_creation.new_pipe_created / 1000000).toFixed(1)}M
                  </div>
                  <div className="text-xs text-gray-600">Total New Pipe Generated</div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-700">
                    {analytics.dashboard_blocks?.block_3_pipe_creation?.target_pipe_created 
                      ? `Target: $${(analytics.dashboard_blocks.block_3_pipe_creation.target_pipe_created / 1000000).toFixed(1)}M` 
                      : 'Target: $2M'}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center">
                    <div className="text-sm font-bold text-blue-600">
                      ${(analytics.dashboard_blocks.block_3_pipe_creation.weighted_pipe_created / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-600">New Weighted Pipe</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-bold text-teal-600">
                      ${(analytics.dashboard_blocks.block_3_pipe_creation.aggregate_weighted_pipe / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-600">Aggregate Weighted Pipe</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 4: Deals Closed (Current Period) */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center">Deals Closed (Current Period)</CardTitle>
              <CardDescription className="text-center font-medium text-gray-600">
                {analytics.dashboard_blocks?.block_4_revenue?.period || 'Current Period'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center">
                  <div className="text-sm font-bold text-gray-700">
                    {analytics.deals_closed?.deals_closed || 0}
                  </div>
                  <div className="text-xs text-gray-500">Deals Closed</div>
                  <div className="text-xs text-gray-400">
                    Target: {analytics.deals_closed?.target_deals || 0}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-bold text-green-600">
                    ${analytics.deals_closed?.arr_closed ? (analytics.deals_closed.arr_closed / 1000).toFixed(0) + 'K' : '0'}
                  </div>
                  <div className="text-xs text-gray-500">ARR Closed</div>
                  <div className="text-xs text-gray-400">
                    Target: ${analytics.deals_closed?.target_arr ? (analytics.deals_closed.target_arr / 1000).toFixed(0) + 'K' : '0'}
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${analytics.deals_closed?.on_track ? 'bg-green-500' : 'bg-orange-500'}`}
                    style={{ width: `${Math.min(analytics.deals_closed?.target_deals ? (analytics.deals_closed.deals_closed / analytics.deals_closed.target_deals * 100) : 0, 100)}%` }}
                  ></div>
                </div>
                <div className="text-center text-xs text-gray-600 mt-1">
                  {analytics.deals_closed?.target_deals ? ((analytics.deals_closed.deals_closed / analytics.deals_closed.target_deals * 100).toFixed(1)) : 0}% of target
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
  const [yearlyData, setYearlyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [monthOffset, setMonthOffset] = useState(0);
  const [dateRange, setDateRange] = useState(null);
  const [useCustomDate, setUseCustomDate] = useState(false);
  const [importMethod, setImportMethod] = useState('csv'); // 'csv' or 'sheets'
  const [viewMode, setViewMode] = useState('monthly'); // 'monthly' or 'yearly'
  
  // New states for projections
  const [hotDeals, setHotDeals] = useState([]);
  const [hotLeads, setHotLeads] = useState([]);
  const [performanceSummary, setPerformanceSummary] = useState(null);
  const [hiddenDeals, setHiddenDeals] = useState(new Set());
  const [hiddenLeads, setHiddenLeads] = useState(new Set());
  const [loadingProjections, setLoadingProjections] = useState(false);
  
  // State for Upsell & Renew tab
  const [upsellRenewData, setUpsellRenewData] = useState(null);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      let yearlyResponse;
      
      if (useCustomDate && dateRange?.from && dateRange?.to) {
        // Use custom date range
        const startDate = format(dateRange.from, 'yyyy-MM-dd');
        const endDate = format(dateRange.to, 'yyyy-MM-dd');
        response = await axios.get(`${API}/analytics/custom?start_date=${startDate}&end_date=${endDate}`);
        // Also load yearly data for comparison
        yearlyResponse = await axios.get(`${API}/analytics/yearly?year=2025`);
      } else if (viewMode === 'yearly') {
        // Use yearly view
        response = await axios.get(`${API}/analytics/yearly?year=2025`);
        yearlyResponse = response; // Same data
      } else {
        // Use monthly offset
        response = await axios.get(`${API}/analytics/monthly?month_offset=${monthOffset}`);
        // Also load yearly data for Deals & Pipeline comparison
        yearlyResponse = await axios.get(`${API}/analytics/yearly?year=2025`);
      }
      
      setAnalytics(response.data);
      setYearlyData(yearlyResponse.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
    loadProjectionsData();
    loadUpsellRenewData();
  }, [monthOffset, dateRange, useCustomDate, viewMode]);

  const handleUploadSuccess = () => {
    loadAnalytics();
    loadProjectionsData();
    loadUpsellRenewData();
  };

  // Load Upsell & Renew data
  const loadUpsellRenewData = async () => {
    try {
      let startDate, endDate;
      
      if (useCustomDate && dateRange?.from && dateRange?.to) {
        startDate = format(dateRange.from, 'yyyy-MM-dd');
        endDate = format(dateRange.to, 'yyyy-MM-dd');
      } else {
        // Calculate current month based on offset
        const now = new Date();
        const targetDate = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1);
        startDate = format(new Date(targetDate.getFullYear(), targetDate.getMonth(), 1), 'yyyy-MM-dd');
        endDate = format(new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0), 'yyyy-MM-dd');
      }
      
      const response = await axios.get(`${API}/analytics/upsell-renewals?start_date=${startDate}&end_date=${endDate}`);
      setUpsellRenewData(response.data);
    } catch (error) {
      console.error('Error loading upsell/renew data:', error);
    }
  };

  // New functions for projections data
  const loadProjectionsData = async () => {
    setLoadingProjections(true);
    try {
      const [hotDealsResponse, hotLeadsResponse, performanceResponse] = await Promise.all([
        axios.get(`${API}/projections/hot-deals`),
        axios.get(`${API}/projections/hot-leads`),
        axios.get(`${API}/projections/performance-summary`)
      ]);
      
      // Combine hot deals (B Legals) and hot leads (POA Booked + Proposal sent) for the interactive board
      const combinedDeals = [
        ...hotDealsResponse.data.map(deal => ({...deal, source: 'hot-deals'})),
        ...hotLeadsResponse.data.map(lead => ({...lead, source: 'hot-leads'}))
      ];

      // Assign columns based on deal stage for logical grouping
      const dealsWithColumns = combinedDeals.map((deal, index) => ({
        ...deal,
        // Ensure required fields have defaults
        client: deal.client || deal.company || deal.lead_name || `Deal ${index + 1}`,
        pipeline: deal.pipeline || deal.expected_arr || deal.value || 0,
        owner: deal.owner || deal.ae || 'TBD',
        column: deal.column || (() => {
          // Assign columns based on deal stage
          if (deal.stage === 'B Legals') return 'next14';  // Closest to closing
          if (deal.stage === 'C Proposal sent') return 'next30';  // Medium term
          if (deal.stage === 'D POA Booked') return 'next60';  // Longer term
          // Default assignment for other stages
          return index % 3 === 0 ? 'next14' : index % 3 === 1 ? 'next30' : 'next60';
        })()
      }));
      
      console.log(`DEBUG: Loaded ${dealsWithColumns.length} deals for interactive board`);
      console.log('Deals by column:', {
        next14: dealsWithColumns.filter(d => d.column === 'next14').length,
        next30: dealsWithColumns.filter(d => d.column === 'next30').length,
        next60: dealsWithColumns.filter(d => d.column === 'next60').length
      });
      
      setHotDeals(dealsWithColumns);
      setHotLeads(hotLeadsResponse.data);
      setPerformanceSummary(performanceResponse.data);
    } catch (error) {
      console.error('Error loading projections data:', error);
    } finally {
      setLoadingProjections(false);
    }
  };

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const { source, destination } = result;
    
    // Handle column-based drag and drop for the new interactive board
    if (['next14', 'next30', 'next60'].includes(source.droppableId) || 
        ['next14', 'next30', 'next60'].includes(destination.droppableId)) {
      
      const newDeals = Array.from(hotDeals);
      const draggedDeal = newDeals.find(deal => deal.id === result.draggableId);
      
      if (draggedDeal) {
        // Update the deal's column assignment
        draggedDeal.column = destination.droppableId;
        setHotDeals(newDeals);
      }
    } else if (source.droppableId === 'hot-deals') {
      const newDeals = Array.from(hotDeals);
      const [reorderedItem] = newDeals.splice(source.index, 1);
      newDeals.splice(destination.index, 0, reorderedItem);
      setHotDeals(newDeals);
    } else if (source.droppableId === 'hot-leads') {
      const newLeads = Array.from(hotLeads);
      const [reorderedItem] = newLeads.splice(source.index, 1);
      newLeads.splice(destination.index, 0, reorderedItem);
      setHotLeads(newLeads);
    }
  };

  // Alias for backward compatibility
  const handleOnDragEnd = onDragEnd;

  const hideItem = (type, id) => {
    if (type === 'deals') {
      setHiddenDeals(prev => new Set([...prev, id]));
    } else if (type === 'leads') {
      setHiddenLeads(prev => new Set([...prev, id]));
    }
  };

  const resetView = (type) => {
    if (type === 'deals') {
      setHiddenDeals(new Set());
      loadProjectionsData(); // Reload original data
    } else if (type === 'leads') {
      setHiddenLeads(new Set());
      loadProjectionsData(); // Reload original data
    }
  };

  const filteredHotDeals = hotDeals.filter(deal => !hiddenDeals.has(deal.id));
  const filteredHotLeads = hotLeads.filter(lead => !hiddenLeads.has(lead.id));

  // Sortable data hooks for AE Performance tables
  const { items: sortedAeIntros, requestSort: requestAeIntrosSort, sortConfig: aeIntrosSortConfig } = 
    useSortableData(analytics?.ae_performance?.ae_performance || []);
  const { items: sortedIntrosDetails, requestSort: requestIntrosDetailsSort, sortConfig: introsDetailsSortConfig } = 
    useSortableData(analytics?.ae_performance?.intros_details || []);
  const { items: sortedAePoa, requestSort: requestAePoaSort, sortConfig: aePoaSortConfig } = 
    useSortableData(analytics?.ae_performance?.ae_poa_performance || []);
  const { items: sortedPoaDetails, requestSort: requestPoaDetailsSort, sortConfig: poaDetailsSortConfig } = 
    useSortableData(analytics?.ae_performance?.poa_attended_details || []);

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
             viewMode === 'yearly' ? 'July To Dec 2025 Report' : 'Monthly Report'}
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
                July To Dec
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
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="meetings">Meetings Generation</TabsTrigger>
          <TabsTrigger value="attended">Meetings Attended</TabsTrigger>
          <TabsTrigger value="upsell">Upsell & Renew</TabsTrigger>
          <TabsTrigger value="deals">Deals & Pipeline</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
        </TabsList>

        {/* Main Dashboard */}
        <TabsContent value="dashboard">
          <MainDashboard analytics={analytics} />
        </TabsContent>

        {/* Meetings Generation */}
        <TabsContent value="meetings">
          <AnalyticsSection 
            title="Meetings Generation (Current Period)"
            isOnTrack={analytics.meeting_generation.on_track}
            conclusion={analytics.meeting_generation.on_track 
              ? "You are on track to meet your meetings generation targets." 
              : "Need to increase prospecting efforts to reach targets."}
          >
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
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
                target={analytics.meeting_generation.inbound_target}
                icon={TrendingUp}
                color="green"
              />
              <MetricCard
                title="Outbound"
                value={analytics.meeting_generation.outbound}
                target={analytics.meeting_generation.outbound_target}
                icon={Target}
                color="orange"
              />
              <MetricCard
                title="Referrals"
                value={analytics.meeting_generation.referrals}
                target={analytics.meeting_generation.referral_target}
                icon={Users}
                color="purple"
              />
              <MetricCard
                title="Upsells / Cross-sell"
                value={analytics.dashboard_blocks?.block_1_meetings?.upsells_actual || 0}
                target={analytics.dashboard_blocks?.block_1_meetings?.upsells_target || 0}
                icon={TrendingUp}
                color="indigo"
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
                          <th className="text-center p-2">Role</th>
                          <th className="text-right p-2">Total Meetings</th>
                          <th className="text-right p-2">Relevant Meetings</th>
                          <th className="text-right p-2">Meeting Goal</th>
                          <th className="text-right p-2">Relevance Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(analytics.meeting_generation.bdr_performance).map(([bdr, stats]) => {
                          // Only BDR have meeting goals, not AE
                          let goalText = '-';
                          let isOnTrack = false;
                          
                          if (stats.role === 'BDR') {
                            const monthlyGoal = stats.meeting_target || 6;
                            goalText = `${stats.total_meetings}/${monthlyGoal}`;
                            isOnTrack = stats.total_meetings >= monthlyGoal;
                          }
                          
                          return (
                            <tr key={bdr} className="border-b">
                              <td className="p-2 font-medium">{bdr}</td>
                              <td className="text-center p-2">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  stats.role === 'BDR' ? 'bg-blue-100 text-blue-800' : 
                                  stats.role === 'AE' ? 'bg-purple-100 text-purple-800' : 
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {stats.role || 'N/A'}
                                </span>
                              </td>
                              <td className="text-right p-2">{stats.total_meetings}</td>
                              <td className="text-right p-2">{stats.relevant_meetings}</td>
                              <td className={`text-right p-2 font-medium ${
                                stats.role === 'BDR' ? (isOnTrack ? 'text-green-600' : 'text-orange-600') : 'text-gray-500'
                              }`}>
                                {goalText}
                              </td>
                              <td className="text-right p-2">
                                {((stats.relevant_meetings / stats.total_meetings) * 100).toFixed(1)}%
                              </td>
                            </tr>
                          );
                        })}
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
            {(() => {
              // Calculate period duration in months for dynamic targets
              let periodMonths = 1; // Default to 1 month
              
              if (useCustomDate && dateRange?.from && dateRange?.to) {
                // Custom date range
                const startDate = new Date(dateRange.from);
                const endDate = new Date(dateRange.to);
                const diffTime = Math.abs(endDate - startDate);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                periodMonths = Math.max(1, Math.round(diffDays / 30.44)); // Convert days to months
              } else if (viewMode === 'yearly') {
                // July to December = 6 months
                periodMonths = 6;
              } else {
                // Monthly view = 1 month
                periodMonths = 1;
              }

              // Base monthly targets
              const baseMeetingsScheduledTarget = 50;
              const basePOAGeneratedTarget = 18;
              const baseDealsClosedTarget = 6;

              // Dynamic targets based on period duration
              const dynamicMeetingsScheduledTarget = baseMeetingsScheduledTarget * periodMonths;
              const dynamicPOAGeneratedTarget = basePOAGeneratedTarget * periodMonths;
              const dynamicDealsClosedTarget = baseDealsClosedTarget * periodMonths;

              // Calculate achievement percentages
              const meetingsScheduledAchievement = analytics.meetings_attended.intro_metrics.scheduled / dynamicMeetingsScheduledTarget * 100;
              const poaGeneratedAchievement = analytics.meetings_attended.poa_generated_metrics.completed / dynamicPOAGeneratedTarget * 100;
              const dealsClosedAchievement = analytics.meetings_attended.deals_closed_metrics.generated / dynamicDealsClosedTarget * 100;

              return (
                <>
                  {/* Period and Target Info */}
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
                    <div className="text-sm text-gray-600">
                      <strong>Selected Period:</strong> {periodMonths} month{periodMonths > 1 ? 's' : ''} 
                      {viewMode === 'yearly' ? ' (July–December 2025)' : 
                       useCustomDate ? ` (${dateRange?.from?.toLocaleDateString()} - ${dateRange?.to?.toLocaleDateString()})` : 
                       ' (Current Month)'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Base monthly targets: Meetings Scheduled (50) • POA Generated (18) • Deals Closed (6)
                    </div>
                  </div>

                  {/* 📅 SECTION 1: MEETINGS & INTROS PERFORMANCE */}
                  <Card className="mb-6 border-blue-200">
                    <CardHeader className="bg-blue-50">
                      <CardTitle className="text-xl flex items-center gap-2">
                        <Calendar className="h-6 w-6 text-blue-600" />
                        Meetings & Intros Performance
                      </CardTitle>
                      <CardDescription>Meeting scheduling, attendance and intro metrics with dynamic targets</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <MetricCard
                          title="Meetings Scheduled"
                          value={analytics.meetings_attended.intro_metrics.scheduled}
                          target={dynamicMeetingsScheduledTarget}
                          icon={Calendar}
                          color={meetingsScheduledAchievement >= 80 ? "green" : meetingsScheduledAchievement >= 60 ? "orange" : "red"}
                          statusBadge={meetingsScheduledAchievement >= 80 ? "On Track" : "Needs Attention"}
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
                    </CardContent>
                  </Card>

                  {/* 🎯 SECTION 2: POA & DEALS PERFORMANCE */}
                  <Card className="mb-6 border-purple-200">
                    <CardHeader className="bg-purple-50">
                      <CardTitle className="text-xl flex items-center gap-2">
                        <Target className="h-6 w-6 text-purple-600" />
                        POA & Deals Performance
                      </CardTitle>
                      <CardDescription>POA generation and deal closing metrics with dynamic targets</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <MetricCard
                          title="POA Generated"
                          value={analytics.meetings_attended.poa_generated_metrics.completed}
                          target={dynamicPOAGeneratedTarget}
                          icon={Target}
                          color={poaGeneratedAchievement >= 80 ? "green" : poaGeneratedAchievement >= 60 ? "orange" : "red"}
                          statusBadge={poaGeneratedAchievement >= 80 ? "On Track" : "Needs Attention"}
                        />
                        <MetricCard
                          title="Deals Closed"
                          value={analytics.meetings_attended.deals_closed_metrics.generated}
                          target={dynamicDealsClosedTarget}
                          icon={DollarSign}
                          color={dealsClosedAchievement >= 80 ? "green" : dealsClosedAchievement >= 60 ? "orange" : "red"}
                          statusBadge={dealsClosedAchievement >= 80 ? "On Track" : "Needs Attention"}
                        />
                      </div>
                    </CardContent>
                  </Card>
                </>
              );
            })()}

            {/* Removed duplicate detail tables - now organized in structured sections below */}

            {/* 👥 SECTION 3: AE PERFORMANCE BREAKDOWN */}
            <Card className="mb-6 border-green-200">
              <CardHeader className="bg-green-50">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Users className="h-6 w-6 text-green-600" />
                  AE Performance Breakdown
                </CardTitle>
                <CardDescription>Individual AE performance for meetings, intros, and POA</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {/* AE Performance Section - Meetings & Intros */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                  {/* AE Performance Table - Meetings & Intros */}
                  <div className="lg:col-span-1">
                    <Card className="border-blue-100">
                      <CardHeader className="bg-blue-25">
                        <CardTitle className="text-lg text-blue-700">AE Meetings & Intros</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <SortableTableHeader sortKey="ae" requestSort={requestAeIntrosSort} sortConfig={aeIntrosSortConfig} className="text-left p-2 font-semibold">
                                  AE
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="intros_attended" requestSort={requestAeIntrosSort} sortConfig={aeIntrosSortConfig} className="text-right p-2 font-semibold">
                                  Intros Attended
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="relevant_intro" requestSort={requestAeIntrosSort} sortConfig={aeIntrosSortConfig} className="text-right p-2 font-semibold">
                                  Relevant Intro
                                </SortableTableHeader>
                              </tr>
                            </thead>
                            <tbody>
                              {sortedAeIntros.map((ae, index) => (
                                <tr key={index} className="border-b hover:bg-gray-50">
                                  <td className="p-2 font-medium">{ae.ae}</td>
                                  <td className="text-right p-2">{ae.intros_attended}</td>
                                  <td className="text-right p-2">{ae.relevant_intro}</td>
                                </tr>
                              ))}
                              {/* Total Row */}
                              <tr className="border-t-2 font-bold">
                                <td className="p-2">Total</td>
                                <td className="text-right p-2">{analytics.ae_performance.total_metrics.total_intros}</td>
                                <td className="text-right p-2">{analytics.ae_performance.total_metrics.total_relevant}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Intros Details List */}
                  <div className="lg:col-span-2">
                    <Card className="border-blue-100">
                      <CardHeader className="bg-blue-25">
                        <CardTitle className="text-lg text-blue-700">Intros Attended Details</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto max-h-96">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b sticky top-0 bg-white">
                                <SortableTableHeader sortKey="date" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Date
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="client" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Client
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="ae" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-left p-2 font-semibold">
                                  AE
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="stage" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Stage
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="relevance" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-center p-2 font-semibold">
                                  Relevance
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="expected_arr" requestSort={requestIntrosDetailsSort} sortConfig={introsDetailsSortConfig} className="text-right p-2 font-semibold">
                                  Expected ARR
                                </SortableTableHeader>
                              </tr>
                            </thead>
                            <tbody>
                              {sortedIntrosDetails.map((intro, index) => (
                                <tr key={index} className="border-b hover:bg-gray-50">
                                  <td className="p-2">{intro.date}</td>
                                  <td className="p-2 font-medium">{intro.client}</td>
                                  <td className="p-2">{intro.ae}</td>
                                  <td className="p-2">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                      intro.stage?.includes('Won') || intro.stage?.includes('Closed Won') ? 'bg-green-100 text-green-800' :
                                      intro.stage?.includes('Lost') ? 'bg-red-100 text-red-800' :
                                      intro.stage?.includes('POA') || intro.stage?.includes('Legal') ? 'bg-blue-100 text-blue-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {intro.stage}
                                    </span>
                                  </td>
                                  <td className="p-2 text-center">
                                    <span className={`inline-flex items-center w-3 h-3 rounded-full ${
                                      intro.relevance === 'Relevant' ? 'bg-green-500' :
                                      intro.relevance === 'Question mark' || intro.relevance === 'Maybe' ? 'bg-yellow-500' :
                                      intro.relevance === 'Not relevant' ? 'bg-red-500' :
                                      'bg-gray-500'
                                    }`}></span>
                                  </td>
                                  <td className="text-right p-2">
                                    ${intro.expected_arr.toLocaleString()}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* AE POA Performance Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* AE POA Performance Table */}
                  <div className="lg:col-span-1">
                    <Card className="border-purple-100">
                      <CardHeader className="bg-purple-25">
                        <CardTitle className="text-lg text-purple-700">AE POA Performance</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <SortableTableHeader sortKey="ae" requestSort={requestAePoaSort} sortConfig={aePoaSortConfig} className="text-left p-2 font-semibold">
                                  AE
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="poa_attended" requestSort={requestAePoaSort} sortConfig={aePoaSortConfig} className="text-right p-2 font-semibold">
                                  POA Attended
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="poa_closed" requestSort={requestAePoaSort} sortConfig={aePoaSortConfig} className="text-right p-2 font-semibold">
                                  POA Closed
                                </SortableTableHeader>
                              </tr>
                            </thead>
                            <tbody>
                              {sortedAePoa.map((ae, index) => (
                                <tr key={index} className="border-b hover:bg-gray-50">
                                  <td className="p-2 font-medium">{ae.ae}</td>
                                  <td className="text-right p-2">{ae.poa_attended}</td>
                                  <td className="text-right p-2">{ae.poa_closed}</td>
                                </tr>
                              ))}
                              {/* Total Row */}
                              <tr className="border-t-2 font-bold">
                                <td className="p-2">Total</td>
                                <td className="text-right p-2">{analytics.ae_performance.total_metrics.total_poa_attended}</td>
                                <td className="text-right p-2">{analytics.ae_performance.total_metrics.total_poa_closed}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* POA Attended Details List */}
                  <div className="lg:col-span-2">
                    <Card className="border-purple-100">
                      <CardHeader className="bg-purple-25">
                        <CardTitle className="text-lg text-purple-700">POA Attended Details</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto max-h-96">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b sticky top-0 bg-white">
                                <SortableTableHeader sortKey="date" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Date
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="client" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Client
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="ae" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-left p-2 font-semibold">
                                  AE
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="stage" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-left p-2 font-semibold">
                                  Stage
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="relevance" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-center p-2 font-semibold">
                                  Relevance
                                </SortableTableHeader>
                                <SortableTableHeader sortKey="expected_arr" requestSort={requestPoaDetailsSort} sortConfig={poaDetailsSortConfig} className="text-right p-2 font-semibold">
                                  Expected ARR
                                </SortableTableHeader>
                              </tr>
                            </thead>
                            <tbody>
                              {sortedPoaDetails.map((poa, index) => (
                                <tr key={index} className="border-b hover:bg-gray-50">
                                  <td className="p-2">{poa.date}</td>
                                  <td className="p-2 font-medium">{poa.client}</td>
                                  <td className="p-2">{poa.ae}</td>
                                  <td className="p-2">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                      poa.stage?.includes('Won') || poa.stage?.includes('Closed Won') ? 'bg-green-100 text-green-800' :
                                      poa.stage?.includes('Lost') ? 'bg-red-100 text-red-800' :
                                      poa.stage?.includes('POA') || poa.stage?.includes('Legal') ? 'bg-blue-100 text-blue-800' :
                                      poa.stage?.includes('Proposal') ? 'bg-purple-100 text-purple-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {poa.stage}
                                    </span>
                                  </td>
                                  <td className="p-2 text-center">
                                    <span className={`inline-flex items-center w-3 h-3 rounded-full ${
                                      poa.relevance === 'Relevant' ? 'bg-green-500' :
                                      poa.relevance === 'Question mark' || poa.relevance === 'Maybe' ? 'bg-yellow-500' :
                                      poa.relevance === 'Not relevant' ? 'bg-red-500' :
                                      'bg-gray-500'
                                    }`}></span>
                                  </td>
                                  <td className="text-right p-2">
                                    ${poa.expected_arr.toLocaleString()}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AE Performance Blocks - 4 blocks similar to dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
              {analytics.ae_performance.ae_performance.slice(0, 4).map((ae, index) => (
                <Card key={index}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-center">AE #{index + 1}</CardTitle>
                    <CardDescription className="text-center font-medium text-blue-600">
                      {ae.ae}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Intro Attended:</span>
                        <span className="font-medium">{ae.intros_attended}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>POA Done:</span>
                        <span className="font-medium">{ae.poa_fait}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Closing:</span>
                        <span className="font-medium">{ae.closing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Closing Value:</span>
                        <span className="font-medium text-green-600">
                          ${ae.valeur_closing.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Cette section a été déplacée dans la Section 3 ci-dessus */}

            {/* 🔄 SECTION 4: CONVERSION RATES */}
            <Card className="mb-6 border-orange-200">
              <CardHeader className="bg-orange-50">
                <CardTitle className="text-xl flex items-center gap-2">
                  <BarChart3 className="h-6 w-6 text-orange-600" />
                  Conversion Rates Analysis
                </CardTitle>
                <CardDescription>Intro to POA and POA to Closing conversion metrics by AE</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Intro → POA Conversion Rate */}
              <Card>
                <CardHeader>
                  <CardTitle>Intro → POA Conversion Rate</CardTitle>
                  <CardDescription>Conversion from Intros Attended to POA Generated</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Global Rate */}
                  <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {analytics.meetings_attended.conversion_rates.intro_to_poa.global_rate.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Global Conversion Rate
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {analytics.meetings_attended.conversion_rates.intro_to_poa.total_poas} POAs / {analytics.meetings_attended.conversion_rates.intro_to_poa.total_intros} Intros
                      </div>
                    </div>
                  </div>

                  {/* By AE */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-semibold">AE</th>
                          <th className="text-right p-2 font-semibold">Intros</th>
                          <th className="text-right p-2 font-semibold">POAs</th>
                          <th className="text-right p-2 font-semibold">Conv Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.meetings_attended.conversion_rates.intro_to_poa.by_ae.map((ae, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-medium">{ae.ae}</td>
                            <td className="text-right p-2">{ae.intros}</td>
                            <td className="text-right p-2">{ae.poas}</td>
                            <td className="text-right p-2">
                              <span className={`font-medium ${
                                ae.rate >= 70 ? 'text-green-600' : 
                                ae.rate >= 40 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {ae.rate.toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* POA → Closing Conversion Rate */}
              <Card>
                <CardHeader>
                  <CardTitle>POA → Closing Conversion Rate</CardTitle>
                  <CardDescription>Conversion from POA Generated to Deals Closed</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Global Rate */}
                  <div className="mb-6 p-4 bg-green-50 rounded-lg">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {analytics.meetings_attended.conversion_rates.poa_to_closing.global_rate.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Global Conversion Rate
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {analytics.meetings_attended.conversion_rates.poa_to_closing.total_closed} Closed / {analytics.meetings_attended.conversion_rates.poa_to_closing.total_poas} POAs
                      </div>
                    </div>
                  </div>

                  {/* By AE */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-semibold">AE</th>
                          <th className="text-right p-2 font-semibold">POAs</th>
                          <th className="text-right p-2 font-semibold">Closed</th>
                          <th className="text-right p-2 font-semibold">Conv Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.meetings_attended.conversion_rates.poa_to_closing.by_ae.map((ae, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-medium">{ae.ae}</td>
                            <td className="text-right p-2">{ae.poas}</td>
                            <td className="text-right p-2">{ae.closed}</td>
                            <td className="text-right p-2">
                              <span className={`font-medium ${
                                ae.rate >= 30 ? 'text-green-600' : 
                                ae.rate >= 15 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {ae.rate.toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Reports section has been removed as requested */}
          </AnalyticsSection>
        </TabsContent>

        {/* Deals & Pipeline */}
        <TabsContent value="deals">
          <div className="space-y-6">
            {/* Year 2025 Performance and Selected Month Performance sections have been removed */}

            {/* Deals Closed Details */}
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
              isOnTrack={analytics.pipe_metrics.total_pipe.on_track}
              conclusion={analytics.pipe_metrics.total_pipe.on_track 
                ? "Pipeline creation and weighting aligned with Excel methodology and targets." 
                : "Need to accelerate pipeline generation and improve deal quality."}
            >
              {/* Excel Formula Reference */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
                <div className="font-semibold text-gray-800 mb-1">🧮 Excel-Based Weighted Calculation</div>
                <div className="text-xs text-gray-600">
                  Weighted values calculated using exact Excel formula: Stage probability × Source factor × Recency adjustment
                  <br />
                  <strong>Stages:</strong> E Intro attended, D POA Booked, C Proposal sent, B Legals
                  <br />
                  <strong>Sources:</strong> Outbound, Inbound, Client referral, Internal referral, Partnership
                </div>
              </div>
              {/* Pipeline Overview - 4 blocks uniformisées avec Dashboard */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                  title="New Pipe Created (month)"
                  value={analytics.pipe_metrics.created_pipe.value}
                  target={analytics.pipe_metrics.created_pipe.target}
                  unit="$"
                  icon={TrendingUp}
                  color="green"
                  tooltip="Sum of ARR from all deals created this period, including Closed, Lost, and Not Relevant."
                />
                <MetricCard
                  title="Created Weighted Pipe (month)"
                  value={analytics.pipe_metrics.created_pipe.weighted_value}
                  target={analytics.pipe_metrics.created_pipe.target_weighted}
                  unit="$"
                  icon={Target}
                  color="blue"
                  tooltip="ARR × stage-weight by source and recency, includes all deals created this period."
                />
                <MetricCard
                  title="Total Pipe (period)"
                  value={analytics.pipe_metrics.total_pipe.value}
                  target={analytics.pipe_metrics.total_pipe.target}
                  unit="$"
                  icon={BarChart3}
                  color="purple"
                  tooltip="Sum of ARR for all active deals (excluding Closed, Lost, and Not Relevant)."
                />
                <MetricCard
                  title="Total Weighted Pipe (period)"
                  value={analytics.pipe_metrics.total_pipe.weighted_value}
                  target={analytics.pipe_metrics.total_pipe.target_weighted}
                  unit="$"
                  icon={DollarSign}
                  color="orange"
                  tooltip="ARR × stage-weight for all active deals."
                />
              </div>
              
              {/* Pipeline Logic Explanation */}
              <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="font-semibold text-blue-800 mb-2">📋 Pipeline Logic Summary</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
                  <div>
                    <span className="font-medium">Created Metrics:</span> All deals created in selected period (includes Closed/Lost/Not Relevant)
                  </div>
                  <div>
                    <span className="font-medium">Total Metrics:</span> All active deals (excludes Closed/Lost/Not Relevant)
                  </div>
                  <div>
                    <span className="font-medium">Weighted Value:</span> Uses Excel formula with stage × source × recency factors
                  </div>
                  <div>
                    <span className="font-medium">Dynamic Targets:</span> Scaled by selected period duration
                  </div>
                </div>
              </div>

              {/* AE Breakdown Table */}
              {analytics.pipe_metrics.ae_breakdown && analytics.pipe_metrics.ae_breakdown.length > 0 && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>AE Pipeline Performance</CardTitle>
                    <CardDescription>Pipeline breakdown by Account Executive</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-3 font-semibold">AE</th>
                            <th className="text-right p-3 font-semibold">Total Pipe</th>
                            <th className="text-right p-3 font-semibold">Weighted Pipe</th>
                            <th className="text-right p-3 font-semibold">New Pipe Created</th>
                            <th className="text-right p-3 font-semibold">Deals Count</th>
                            <th className="text-right p-3 font-semibold">New Deals</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.pipe_metrics.ae_breakdown.map((ae, index) => (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="p-3 font-medium">{ae.ae}</td>
                              <td className="text-right p-3 font-semibold text-purple-600">
                                ${ae.total_pipe.toLocaleString()}
                              </td>
                              <td className="text-right p-3 font-semibold text-orange-600">
                                ${ae.weighted_pipe.toLocaleString()}
                              </td>
                              <td className="text-right p-3 font-semibold text-green-600">
                                ${ae.new_pipe_created.toLocaleString()}
                              </td>
                              <td className="text-right p-3">{ae.deals_count}</td>
                              <td className="text-right p-3">{ae.new_deals_count}</td>
                            </tr>
                          ))}
                          {/* Total Row */}
                          <tr className="border-t-2 font-bold bg-gray-50">
                            <td className="p-3">Total</td>
                            <td className="text-right p-3 text-purple-600">
                              ${analytics.pipe_metrics.total_pipe.value.toLocaleString()}
                            </td>
                            <td className="text-right p-3 text-orange-600">
                              ${analytics.pipe_metrics.total_pipe.weighted_value.toLocaleString()}
                            </td>
                            <td className="text-right p-3 text-green-600">
                              ${analytics.pipe_metrics.created_pipe.value.toLocaleString()}
                            </td>
                            <td className="text-right p-3">
                              {analytics.pipe_metrics.total_pipe.count}
                            </td>
                            <td className="text-right p-3">
                              {analytics.pipe_metrics.created_pipe.count}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Pipeline Details */}
              {analytics.pipe_metrics.pipe_details && analytics.pipe_metrics.pipe_details.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Active Pipeline Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Client</th>
                            <th className="text-right p-2">Pipeline Value</th>
                            <th className="text-right p-2">Weighted Value</th>
                            <th className="text-left p-2">Stage</th>
                            <th className="text-center p-2">Probability</th>
                            <th className="text-left p-2">Owner</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.pipe_metrics.pipe_details.map((deal, index) => (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="p-2 font-medium">{deal.client}</td>
                              <td className="text-right p-2">${deal.pipeline?.toLocaleString()}</td>
                              <td className="text-right p-2 font-medium text-orange-600">
                                ${deal.weighted_value?.toLocaleString()}
                              </td>
                              <td className="p-2">
                                <Badge variant="outline">{deal.stage}</Badge>
                              </td>
                              <td className="text-center p-2">
                                <span className={`font-medium ${
                                  deal.probability >= 70 ? 'text-green-600' :
                                  deal.probability >= 50 ? 'text-yellow-600' :
                                  deal.probability >= 30 ? 'text-orange-600' : 'text-gray-600'
                                }`}>
                                  {deal.probability}%
                                </span>
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

        {/* Upsell & Renew */}
        <TabsContent value="upsell">
          {upsellRenewData ? (
            <div className="space-y-6">
              <AnalyticsSection
                title={`Upsells & Renewals - ${upsellRenewData.period}`}
                isOnTrack={upsellRenewData.closing_value >= upsellRenewData.closing_value_target}
                conclusion={
                  upsellRenewData.closing_value >= upsellRenewData.closing_value_target
                    ? "Great performance on upsell and renewal activities."
                    : "Need to increase upsell and renewal prospecting efforts."
                }
              >
                {/* 3 Large Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <MetricCard
                    title="Valeur Closing Upsells"
                    value={upsellRenewData.closing_value}
                    target={upsellRenewData.closing_value_target}
                    unit="$"
                    icon={DollarSign}
                    color="green"
                  />
                  <MetricCard
                    title="POA Generated"
                    value={upsellRenewData.poa_actual}
                    target={upsellRenewData.poa_target}
                    icon={Target}
                    color="orange"
                  />
                  <MetricCard
                    title="Closing"
                    value={upsellRenewData.closing_actual}
                    target={upsellRenewData.closing_target}
                    icon={CheckCircle}
                    color="green"
                  />
                </div>

                {/* 4 Small Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <Card className="border-2 border-purple-200 bg-purple-50">
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-purple-600 mb-1">
                        {upsellRenewData.upsells_actual}
                      </div>
                      <div className="text-sm text-gray-600">Upsells / Cross-sell</div>
                    </CardContent>
                  </Card>
                  <Card className="border-2 border-green-200 bg-green-50">
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-green-600 mb-1">
                        {upsellRenewData.renewals_actual}
                      </div>
                      <div className="text-sm text-gray-600">Renewals</div>
                    </CardContent>
                  </Card>
                  <Card className="border-2 border-green-200 bg-green-50">
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-green-600 mb-1">
                        {upsellRenewData.intros_details?.filter(i => i.status === 'Show').length || 0}
                      </div>
                      <div className="text-sm text-gray-600">Show</div>
                    </CardContent>
                  </Card>
                  <Card className="border-2 border-red-200 bg-red-50">
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-red-600 mb-1">
                        {upsellRenewData.intros_details?.filter(i => i.status === 'No Show').length || 0}
                      </div>
                      <div className="text-sm text-gray-600">No Show</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Partner Performance Table */}
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Partner Performance</span>
                      <Badge variant="destructive">Needs Improvement</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {upsellRenewData.partner_performance && upsellRenewData.partner_performance.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">PARTNER</th>
                              <th className="text-center p-2">INTROS ATTENDED</th>
                              <th className="text-center p-2">POA GENERATED</th>
                              <th className="text-center p-2">UPSELLS</th>
                              <th className="text-center p-2">RENEWALS</th>
                              <th className="text-center p-2">CLOSING</th>
                              <th className="text-right p-2">CLOSING VALUE</th>
                            </tr>
                          </thead>
                          <tbody>
                            {upsellRenewData.partner_performance.map((partner, index) => (
                              <tr key={index} className="border-b hover:bg-gray-50">
                                <td className="p-2 font-medium">{partner.partner_name}</td>
                                <td className="text-center p-2">{partner.intros_attended}</td>
                                <td className="text-center p-2">{partner.poa_generated}</td>
                                <td className="text-center p-2">{partner.upsells}</td>
                                <td className="text-center p-2">{partner.renewals}</td>
                                <td className="text-center p-2">{partner.closing}</td>
                                <td className="text-right p-2 font-medium">
                                  ${(partner.closing_value / 1000).toFixed(0)}K
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        No partner data available for this period
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Intros Attended Details Table */}
                {upsellRenewData.intros_details && upsellRenewData.intros_details.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Intros Attended Details</span>
                        <Badge variant="destructive">Needs Improvement</Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Client</th>
                              <th className="text-left p-2">Partner</th>
                              <th className="text-left p-2">Owner (AE)</th>
                              <th className="text-left p-2">Stage</th>
                              <th className="text-left p-2">Type</th>
                              <th className="text-right p-2">Expected ARR</th>
                            </tr>
                          </thead>
                          <tbody>
                            {upsellRenewData.intros_details.map((intro, index) => (
                              <tr key={index} className="border-b hover:bg-gray-50">
                                <td className="p-2">{intro.date}</td>
                                <td className="p-2 font-medium">{intro.client}</td>
                                <td className="p-2">{intro.partner || '-'}</td>
                                <td className="p-2">{intro.owner}</td>
                                <td className="p-2">
                                  <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                                    {intro.stage}
                                  </span>
                                </td>
                                <td className="p-2">
                                  <span className={`text-xs px-2 py-1 rounded-full ${
                                    intro.type_of_deal === 'Upsell' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'
                                  }`}>
                                    {intro.type_of_deal}
                                  </span>
                                </td>
                                <td className="p-2 text-right font-medium">
                                  ${(intro.expected_arr / 1000).toFixed(0)}K
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* POA Generated Details Table */}
                {upsellRenewData.poa_details && upsellRenewData.poa_details.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>POA Generated Details</span>
                        <Badge variant="destructive">Needs Improvement</Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">POA Date</th>
                              <th className="text-left p-2">Client</th>
                              <th className="text-left p-2">Partner</th>
                              <th className="text-left p-2">Owner (AE)</th>
                              <th className="text-left p-2">Stage</th>
                              <th className="text-left p-2">Type</th>
                              <th className="text-right p-2">Expected ARR</th>
                            </tr>
                          </thead>
                          <tbody>
                            {upsellRenewData.poa_details.map((poa, index) => (
                              <tr key={index} className="border-b hover:bg-gray-50">
                                <td className="p-2">{poa.date}</td>
                                <td className="p-2 font-medium">{poa.client}</td>
                                <td className="p-2">{poa.partner || '-'}</td>
                                <td className="p-2">{poa.owner}</td>
                                <td className="p-2">
                                  <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                                    {poa.stage}
                                  </span>
                                </td>
                                <td className="p-2">
                                  <span className={`text-xs px-2 py-1 rounded-full ${
                                    poa.type_of_deal === 'Upsell' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'
                                  }`}>
                                    {poa.type_of_deal}
                                  </span>
                                </td>
                                <td className="p-2 text-right font-medium">
                                  ${(poa.expected_arr / 1000).toFixed(0)}K
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
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600">Loading Upsell & Renew data...</p>
            </div>
          )}
        </TabsContent>

        {/* Projections */}
        <TabsContent value="projections">
          <div className="space-y-6">
            {/* Closing Projections - Enhanced */}
            <Card>
              <CardHeader>
                <CardTitle>Closing Projections</CardTitle>
                <CardDescription>Pipeline metrics with advanced weighting methodology</CardDescription>
                
                {/* Pipeline Metrics Explanation */}
                <div className="mt-3 p-3 bg-gray-50 rounded-lg text-xs">
                  <div className="font-semibold mb-2">📊 Pipeline Metrics Explained:</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="font-medium text-purple-700">• Total Pipeline:</span>
                      <br />Valeur brute (sauf Lost/Not Relevant)
                    </div>
                    <div>
                      <span className="font-medium text-blue-700">• Weighted Value:</span>
                      <br />Pondéré par stage/source/temps
                    </div>
                    <div>
                      <span className="font-medium text-green-700">• Aggregate Pipe:</span>
                      <br />Cumul historique pondéré
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  {/* Card 1: Legals Count - Use master data from hot-deals */}
                  <Card className="border-2 border-purple-200 bg-purple-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <FileText className="h-4 w-4 text-purple-600" />
                        Legals
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2 text-gray-800">
                        {hotDeals.filter(deal => deal.stage === 'B Legals').length}
                      </div>
                      <div className="text-xs text-gray-600">
                        Deals in Legals
                      </div>
                    </CardContent>
                  </Card>

                  {/* Card 2: Proposal Sent Count - Use master data from hot-leads */}
                  <Card className="border-2 border-indigo-200 bg-indigo-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Target className="h-4 w-4 text-indigo-600" />
                        Proposal Sent
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2 text-gray-800">
                        {hotLeads.filter(deal => deal.stage === 'C Proposal sent').length}
                      </div>
                      <div className="text-xs text-gray-600">
                        Deals in Proposal
                      </div>
                    </CardContent>
                  </Card>

                  {/* Card 3: Combined Value - Use master data pipeline values */}
                  <Card className="border-2 border-green-200 bg-green-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        Legals + Proposal Value
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-bold mb-2 text-gray-800">
                        ${(() => {
                          // Sum RAW deal values (expected_arr field - no weighting/probability)
                          const legalsValue = hotDeals
                            .filter(deal => deal.stage === 'B Legals')
                            .reduce((sum, deal) => sum + (deal.expected_arr || deal.pipeline || 0), 0);
                          
                          const proposalValue = hotLeads
                            .filter(deal => deal.stage === 'C Proposal sent')
                            .reduce((sum, deal) => sum + (deal.expected_arr || deal.pipeline || 0), 0);
                          
                          return (legalsValue + proposalValue);
                        })().toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-600">
                        Combined Pipeline Value
                      </div>
                    </CardContent>
                  </Card>

                  {/* Card 4: Upcoming POAs - Show count and total value */}
                  <Card className="border-2 border-blue-200 bg-blue-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-blue-600" />
                        Upcoming POAs
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        // Get upcoming POA from hot-leads with future poa_date
                        const today = new Date();
                        const upcomingPOAs = hotLeads.filter(deal => {
                          const poaDate = deal.poa_date ? new Date(deal.poa_date) : null;
                          return poaDate && poaDate > today;
                        });
                        const upcomingCount = upcomingPOAs.length;
                        const upcomingValue = upcomingPOAs.reduce((sum, deal) => 
                          sum + (parseFloat(deal.expected_arr) || 0), 0
                        );
                        
                        return (
                          <div className="space-y-2">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-blue-600">
                                {upcomingCount}
                              </div>
                              <div className="text-xs text-gray-600">Upcoming POAs</div>
                            </div>
                            <div className="text-center pt-2 border-t border-blue-200">
                              <div className="text-lg font-bold text-green-600">
                                ${(upcomingValue / 1000).toFixed(0)}K
                              </div>
                              <div className="text-xs text-gray-600">Total Value</div>
                            </div>
                          </div>
                        );
                      })()}
                    </CardContent>
                  </Card>
                </div>

                {/* Upcoming High-Priority Meetings (Next 7 Days) with POA Dates */}
                {(() => {
                  // Get upcoming POA meetings from hot leads that have dates after today
                  const today = new Date();
                  const next7Days = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
                  
                  // Combine all deals with POA dates or discovery dates
                  const upcomingMeetings = [
                    ...(analytics.closing_projections.current_month.deals || []),
                    ...(analytics.closing_projections.next_quarter.deals || [])
                  ].filter(deal => {
                    // Check if deal has POA date or discovery date in next 7 days
                    const poaDate = deal.poa_date ? new Date(deal.poa_date) : null;
                    const discoveryDate = deal.discovery_date ? new Date(deal.discovery_date) : null;
                    
                    return (poaDate && poaDate > today && poaDate <= next7Days) ||
                           (discoveryDate && discoveryDate > today && discoveryDate <= next7Days);
                  }).slice(0, 6); // Limit to 6 meetings
                  
                  return upcomingMeetings.length > 0 ? (
                    <Card className="mb-6 bg-yellow-50 border-yellow-200">
                      <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                          <AlertCircle className="h-5 w-5 text-yellow-600" />
                          Upcoming High-Priority Meetings (Next 7 Days)
                        </CardTitle>
                        <CardDescription>POA and Discovery meetings scheduled in the next week</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                          {upcomingMeetings.map((deal, index) => {
                            const poaDate = deal.poa_date ? new Date(deal.poa_date) : null;
                            const discoveryDate = deal.discovery_date ? new Date(deal.discovery_date) : null;
                            const meetingDate = poaDate || discoveryDate;
                            const meetingType = poaDate ? 'POA' : 'Discovery';
                            
                            return (
                              <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                                <div className="flex-1">
                                  <div className="font-medium">{deal.client || deal.company || 'Deal'}</div>
                                  <div className="text-sm text-gray-600">Owner: {deal.owner || 'TBD'}</div>
                                  <div className="text-xs font-medium text-blue-600">
                                    📅 {meetingType}: {meetingDate.toLocaleDateString('en-US', { 
                                      weekday: 'short', 
                                      month: 'short', 
                                      day: 'numeric' 
                                    })}
                                  </div>
                                </div>
                                <div className="text-right ml-3">
                                  <div className="text-sm font-bold">${(deal.pipeline || 0).toLocaleString()}</div>
                                  <Badge className={`text-xs ${
                                    (deal.probability || 0) >= 70 ? 'bg-green-100 text-green-800' : 
                                    (deal.probability || 0) >= 50 ? 'bg-yellow-100 text-yellow-800' : 
                                    'bg-orange-100 text-orange-800'
                                  }`}>
                                    {deal.probability || 50}%
                                  </Badge>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  ) : null;
                })()}

              </CardContent>
            </Card>

            {/* Upcoming High-Priority Meetings (Next 7 Days) */}
            {analytics.meetings_attended?.upcoming_poa && analytics.meetings_attended.upcoming_poa.filter(poa => {
              const poaDate = new Date(poa.poa_date);
              const today = new Date();
              const next7Days = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
              return poaDate > today && poaDate <= next7Days;
            }).length > 0 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2">
                    <Calendar className="h-6 w-6 text-blue-600" />
                    Upcoming High-Priority Meetings (Next 7 Days)
                  </CardTitle>
                  <CardDescription>POA meetings scheduled in the next week</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {analytics.meetings_attended.upcoming_poa
                      .filter(poa => {
                        const poaDate = new Date(poa.poa_date);
                        const today = new Date();
                        const next7Days = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
                        return poaDate > today && poaDate <= next7Days;
                      })
                      .map((poa, index) => (
                        <div key={index} className="p-4 border rounded-lg bg-blue-50 border-blue-200">
                          <div className="font-semibold text-blue-800">{poa.client || 'Client TBD'}</div>
                          <div className="text-sm text-gray-600">AE: {poa.owner || 'TBD'}</div>
                          <div className="text-sm font-medium text-blue-600">
                            📅 {new Date(poa.poa_date).toLocaleDateString('en-US', { 
                              weekday: 'short', 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </div>
                          {poa.pipeline && (
                            <div className="text-xs text-gray-500">
                              Pipeline: ${poa.pipeline.toLocaleString()}
                            </div>
                          )}
                        </div>
                      ))
                    }
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Interactive Closing Projections Drag & Drop Board */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Target className="h-6 w-6 text-green-600" />
                  Closing Projections — Interactive Board
                </CardTitle>
                <CardDescription>
                  Drag & drop deals to simulate closing timelines. Changes are visual only and don't affect source data.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DragDropContext onDragEnd={onDragEnd}>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Next 14 Days Column */}
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-green-800 text-center mb-2">
                          Next 14 Days
                        </div>
                        {(() => {
                          const columnValue = hotDeals.filter(deal => deal.column === 'next14').reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const monthlyTarget = 750000; // $750K per month
                          const columnTarget = Math.round(monthlyTarget / 3); // Divide by 3 columns
                          const percentage = Math.round((columnValue / columnTarget) * 100);
                          const isOnTrack = columnValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-2xl font-bold text-green-800 text-center">
                                  ${(columnValue / 1000).toFixed(0)}K
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: ${(columnTarget / 1000).toFixed(0)}K
                                </div>
                                <Progress value={Math.min(percentage, 100)} className="h-2" />
                                <div className="text-xs text-center mt-1">
                                  <span className={isOnTrack ? "text-green-600 font-medium" : "text-orange-600 font-medium"}>
                                    {percentage}% of target
                                  </span>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })()}
                      </div>
                      <Droppable droppableId="next14">
                        {(provided) => (
                          <div 
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            className="space-y-2 min-h-96 max-h-96 overflow-y-auto"
                          >
                            {hotDeals.filter(deal => deal.column === 'next14').map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={deal} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>

                    {/* Next 30 Days Column */}
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-yellow-800 text-center mb-2">
                          Next 30 Days
                        </div>
                        {(() => {
                          const columnValue = hotDeals.filter(deal => deal.column === 'next30').reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const monthlyTarget = 750000; // $750K per month
                          const columnTarget = Math.round(monthlyTarget / 3); // Divide by 3 columns
                          const percentage = Math.round((columnValue / columnTarget) * 100);
                          const isOnTrack = columnValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-2xl font-bold text-yellow-800 text-center">
                                  ${(columnValue / 1000).toFixed(0)}K
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: ${(columnTarget / 1000).toFixed(0)}K
                                </div>
                                <Progress value={Math.min(percentage, 100)} className="h-2" />
                                <div className="text-xs text-center mt-1">
                                  <span className={isOnTrack ? "text-green-600 font-medium" : "text-orange-600 font-medium"}>
                                    {percentage}% of target
                                  </span>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })()}
                      </div>
                      <Droppable droppableId="next30">
                        {(provided) => (
                          <div 
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            className="space-y-2 min-h-96 max-h-96 overflow-y-auto"
                          >
                            {hotDeals.filter(deal => deal.column === 'next30').map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={deal} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>

                    {/* Next 60-90 Days Column */}
                    <div className="bg-orange-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-orange-800 text-center mb-2">
                          Next 60–90 Days
                        </div>
                        {(() => {
                          const columnValue = hotDeals.filter(deal => deal.column === 'next60').reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const monthlyTarget = 750000; // $750K per month
                          const columnTarget = Math.round(monthlyTarget / 3); // Divide by 3 columns
                          const percentage = Math.round((columnValue / columnTarget) * 100);
                          const isOnTrack = columnValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-2xl font-bold text-orange-800 text-center">
                                  ${(columnValue / 1000).toFixed(0)}K
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: ${(columnTarget / 1000).toFixed(0)}K
                                </div>
                                <Progress value={Math.min(percentage, 100)} className="h-2" />
                                <div className="text-xs text-center mt-1">
                                  <span className={isOnTrack ? "text-green-600 font-medium" : "text-orange-600 font-medium"}>
                                    {percentage}% of target
                                  </span>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })()}
                      </div>
                      <Droppable droppableId="next60">
                        {(provided) => (
                          <div 
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            className="space-y-2 min-h-96 max-h-96 overflow-y-auto"
                          >
                            {hotDeals.filter(deal => deal.column === 'next60').map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={deal} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  </div>
                </DragDropContext>
              </CardContent>
            </Card>

            {/* Projections by AE - Moved after Interactive Board */}
            {Object.keys(analytics.closing_projections.ae_projections).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Projections by AE</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left p-2 font-semibold">AE</th>
                          <th className="text-right p-2 font-semibold">
                            Total Pipeline
                            <div className="text-xs font-normal text-gray-500">Brut (sauf Lost)</div>
                          </th>
                          <th className="text-right p-2 font-semibold">
                            Weighted Value
                            <div className="text-xs font-normal text-gray-500">Pondéré période</div>
                          </th>
                          <th className="text-right p-2 font-semibold">
                            Aggregate Pipe
                            <div className="text-xs font-normal text-gray-500">Cumul historique</div>
                          </th>
                          <th className="text-right p-2 font-semibold">Proposal/Legals</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(analytics.closing_projections.ae_projections).map(([ae, stats]) => {
                          // Find corresponding AE in pipe_metrics.ae_breakdown for aggregate data
                          const aeBreakdown = analytics.pipe_metrics?.ae_breakdown?.find(item => item.ae === ae) || {};
                          
                          // Count deals in Proposal sent or Legals stage for this AE
                          const proposalLegalsDeals = (analytics.closing_projections.current_month.deals || [])
                            .concat(analytics.closing_projections.next_quarter.deals || [])
                            .filter(deal => deal.owner === ae && (deal.stage === 'C Proposal sent' || deal.stage === 'B Legals')).length;
                          
                          return (
                            <tr key={ae} className="border-b">
                              <td className="p-2 font-medium">{ae}</td>
                              <td className="text-right p-2">${stats.pipeline?.toLocaleString()}</td>
                              <td className="text-right p-2">${stats.weighted_value?.toLocaleString()}</td>
                              <td className="text-right p-2">${aeBreakdown.weighted_pipe?.toLocaleString() || 0}</td>
                              <td className="text-right p-2">{proposalLegalsDeals}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function App() {
  const { user, loading } = useAuth();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!user) {
    return <LoginPage />;
  }

  // Show dashboard with header if authenticated
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
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