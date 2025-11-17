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
import { Label } from '@/components/ui/label';
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
import AdminTargetsPage from './components/AdminTargetsPage';
import UserManagementPage from './components/UserManagementPage';
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

function MetricCard({ title, value, target, unit = '', trend, icon: Icon, color = 'blue', statusBadge, selectedPeriodValue, periodMonths }) {
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
              {selectedPeriodValue && periodMonths && (
                <div className="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded">
                  📊 Selected Period: {selectedPeriodValue.toLocaleString()} {unit} ({periodMonths} {periodMonths === 1 ? 'month' : 'months'})
                </div>
              )}
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

function DraggableDealItem({ deal, index, onHide, onDelete, showActions = false, onProbabilityChange }) {
  const [isVisible, setIsVisible] = useState(true);
  const [status, setStatus] = useState(deal.status || 'active');
  const [label, setLabel] = useState(deal.label || '');
  const [probability, setProbability] = useState(deal.probability || 75); // Default 75%

  if (!isVisible || status === 'won' || status === 'lost') return null;

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    // Visual only - no backend update
  };

  const handleDelete = () => {
    setIsVisible(false);
    if (onDelete) {
      onDelete(deal.id); // Mark as permanently deleted (user-specific)
    }
    // Note: Don't call onHide here - deleted is permanent, hidden is temporary
  };

  const handleProbabilityChange = (newProb) => {
    setProbability(newProb);
    if (onProbabilityChange) {
      onProbabilityChange(deal.id, newProb);
    }
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
              {/* Probability Selector */}
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-gray-500">Close %:</span>
                <select
                  value={probability}
                  onChange={(e) => handleProbabilityChange(Number(e.target.value))}
                  className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value={50}>50%</option>
                  <option value={75}>75%</option>
                  <option value={90}>90%</option>
                </select>
                <span className="text-xs font-semibold text-green-600">
                  ${((deal.pipeline || 0) * probability / 100 / 1000).toFixed(0)}K proj.
                </span>
              </div>
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

function DataManagementSection({ onDataUpdated, currentView }) {
  const [dataStatus, setDataStatus] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const loadDataStatus = async () => {
    try {
      const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
      const response = await axios.get(`${API}/data/status${viewParam}`);
      setDataStatus(response.data);
    } catch (error) {
      console.error('Error loading data status:', error);
    }
  };

  const handleRefreshGoogleSheet = async () => {
    setIsRefreshing(true);
    try {
      const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
      await axios.post(`${API}/data/refresh-google-sheet${viewParam}`, {}, {
        withCredentials: true
      });
      await loadDataStatus();
      if (onDataUpdated) onDataUpdated();
    } catch (error) {
      console.error('Refresh failed:', error);
      alert(`❌ Refresh failed: ${error.response?.data?.detail || error.message}`);
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
    if (currentView) {
      loadDataStatus();
    }
  }, [currentView]);

  if (!dataStatus) return null;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Sheet className="h-5 w-5" />
            Data Management
          </CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            {dataStatus.source_type === 'google_sheets' && (
              <Button onClick={handleRefreshGoogleSheet} disabled={isRefreshing} size="sm" className="text-xs sm:text-sm">
                <Download className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">{isRefreshing ? 'Refreshing...' : 'Refresh Sheet'}</span>
              </Button>
            )}
            <Button onClick={() => setShowUpload(!showUpload)} variant="outline" size="sm" className="text-xs sm:text-sm">
              <Upload className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">{showUpload ? 'Hide Upload' : 'Upload New Data'}</span>
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
                {dataStatus.last_update ? (
                  <>
                    {new Date(dataStatus.last_update).toLocaleDateString('fr-FR', { 
                      day: '2-digit', 
                      month: '2-digit', 
                      year: 'numeric',
                      timeZone: 'Europe/Paris'
                    })}
                    {' à '}
                    {new Date(dataStatus.last_update).toLocaleTimeString('fr-FR', { 
                      hour: '2-digit', 
                      minute: '2-digit',
                      timeZone: 'Europe/Paris'
                    })}
                  </>
                ) : 'Never'}
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

function MainDashboard({ analytics, currentView, tabTargets, actualPeriodMonths }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for chart series visibility
  const [visibleSeries, setVisibleSeries] = useState({
    'Closed Revenue': true,
    'Target Revenue': false,  // Hidden by default
    'New Weighted Pipe': false,  // Hidden by default  
    'Aggregate Weighted Pipe': true,
    'Created Pipe': false  // Hidden by default
  });

  const loadDashboard = async () => {
    try {
      setLoading(true);
      // Build view_id parameter if available
      const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
      const response = await axios.get(`${API}/analytics/dashboard${viewParam}`);
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
    // Only load if currentView is defined
    if (currentView) {
      loadDashboard();
    }
  }, [currentView]); // Reload when view changes

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
      <DataManagementSection onDataUpdated={handleDataUpdated} currentView={currentView} />
      
      {/* Key Metrics - 5 Simple Cards */}
      {(() => {
        // Dynamic targets - get from backend analytics instead of hardcoding
        // Backend returns targets from admin configuration (dashboard_bottom_cards)
        const baseNewPipeMonthlyTarget = analytics.pipe_metrics?.created_pipe?.target || 2000000; // Fallback to 2M
        const baseWeightedPipeMonthlyTarget = analytics.pipe_metrics?.created_pipe?.target_weighted || 800000; // Fallback to 800K
        
        // Note: Backend already multiplies by period, so we don't need to do it here
        // The target from backend is already: monthly_target × period_duration_months
        const dynamicNewPipeTarget = baseNewPipeMonthlyTarget;
        const dynamicWeightedPipeTarget = baseWeightedPipeMonthlyTarget;
        
        // Use data from analytics (changes with period selector) instead of dashboardData
        const newPipeCreated = analytics.dashboard_blocks?.block_3_pipe_creation?.new_pipe_created || 0;
        const weightedPipe = analytics.dashboard_blocks?.block_3_pipe_creation?.weighted_pipe_created || 0;
        
        return (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
              title="New Pipe Created"
              value={newPipeCreated}
              target={dynamicNewPipeTarget}
              unit="$"
              icon={TrendingUp}
              color="purple"
            />
            <MetricCard
              title="Created Weighted Pipe"
              value={weightedPipe}
              target={dynamicWeightedPipeTarget}
              unit="$"
              icon={Target}
              color="blue"
            />
            <MetricCard
              title="Active Deals"
              value={dashboardData.key_metrics.deals_count}
              icon={Users}
              color="blue"
            />
          </div>
        );
      })()}

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
              {visibleSeries['Created Pipe'] && (
                <Bar 
                  dataKey="new_pipe_created" 
                  fill="#8b5cf6" 
                  name="Created Pipe"
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
                'Aggregate Weighted Pipe': '#4ECDC4',
                'Created Pipe': '#8b5cf6'
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
              value={dashboardData.key_metrics.ytd_revenue}
              target={dashboardData.key_metrics.annual_target_2025}
              unit="$"
              icon={CheckCircle2}
              color="green"
            />
            <MetricCard
              title="Remaining H2 Target"
              value={dashboardData.key_metrics.annual_target_2025 - dashboardData.key_metrics.ytd_revenue}
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
          <Card className="dark:bg-[#1e2128] dark:border-[#2a2d35]">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center dark:text-white">Meetings Generation</CardTitle>
              <CardDescription className="text-center font-medium text-blue-600 dark:text-blue-400">
                {analytics.dashboard_blocks?.block_1_meetings?.period || 'Current Period'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {analytics.dashboard_blocks.block_1_meetings.total_actual}/{analytics.dashboard_blocks.block_1_meetings.total_target}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-slate-400">Total Target</div>
                </div>
                <div className="space-y-2 text-sm dark:text-slate-300">
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
                    <span className="font-medium text-purple-600 dark:text-purple-400">{analytics.dashboard_blocks.block_1_meetings.upsells_actual}/{analytics.dashboard_blocks.block_1_meetings.upsells_target}</span>
                  </div>
                  {analytics.dashboard_blocks.block_1_meetings.unassigned_actual > 0 && (
                    <div className="flex justify-between">
                      <span>Unassigned:</span>
                      <span className="font-medium text-orange-600 dark:text-orange-400">{analytics.dashboard_blocks.block_1_meetings.unassigned_actual}</span>
                    </div>
                  )}
                  <div className="border-t dark:border-[#2a2d35] pt-2 mt-2">
                    <div className="flex justify-between">
                      <span>Show:</span>
                      <span className="font-medium text-green-600 dark:text-green-400">{analytics.dashboard_blocks.block_1_meetings.show_actual}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>No Show:</span>
                      <span className="font-medium text-red-600 dark:text-red-400">{analytics.dashboard_blocks.block_1_meetings.no_show_actual}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 2: Intro & POA */}
          <Card className="dark:bg-[#1e2128] dark:border-[#2a2d35]">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-center dark:text-white">Intro & POA</CardTitle>
              <CardDescription className="text-center font-medium text-green-600 dark:text-green-400">
                {analytics.dashboard_blocks?.block_2_intro_poa?.period || 'Current Period'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {analytics.dashboard_blocks.block_2_intro_poa.intro_actual}/{analytics.dashboard_blocks.block_2_intro_poa.intro_target}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-slate-400">Intro</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {analytics.dashboard_blocks.block_2_intro_poa.poa_actual}/{analytics.dashboard_blocks.block_2_intro_poa.poa_target}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-slate-400">POA</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Block 3: New Pipe Created */}
          <Card className="border-2 border-purple-200 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-center font-semibold">New Pipe Created</CardTitle>
              <p className="text-center text-sm font-medium text-purple-600">
                {analytics.dashboard_blocks?.block_3_pipe_creation?.period || 'Current Period'}
              </p>
            </CardHeader>
            <CardContent className="space-y-2">
              {(() => {
                // Get targets from backend
                const newPipeTarget = analytics.dashboard_blocks?.block_3_pipe_creation?.target_pipe_created || 2000000;
                const weightedPipeTarget = analytics.dashboard_blocks?.block_3_pipe_creation?.target_weighted_pipe || 800000;
                
                const actualNewPipe = analytics.dashboard_blocks.block_3_pipe_creation.new_pipe_created || 0;
                const actualWeightedPipe = analytics.dashboard_blocks.block_3_pipe_creation.aggregate_weighted_pipe || 0;
                
                return (
                  <>
                    {/* Total Pipe Generation */}
                    <div className="p-4 bg-white rounded-lg border border-purple-200 shadow-sm">
                      <div className="text-xs text-gray-600 mb-1">📊 Total Pipe Generation</div>
                      <div className="text-3xl font-bold text-purple-600">
                        ${(actualNewPipe / 1000000).toFixed(1)}M
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        Target: <span className="font-bold text-purple-700">
                          ${(newPipeTarget / 1000000).toFixed(1)}M
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div 
                          className={`h-2.5 rounded-full transition-all ${
                            actualNewPipe >= newPipeTarget ? 'bg-green-500' : 'bg-orange-500'
                          }`}
                          style={{ 
                            width: `${Math.min((actualNewPipe / newPipeTarget * 100), 100)}%` 
                          }}
                        ></div>
                      </div>
                      <div className="text-center text-xs font-semibold text-gray-700 mt-1">
                        {newPipeTarget ? ((actualNewPipe / newPipeTarget * 100).toFixed(1)) : 0}% of target
                      </div>
                    </div>
                    
                    {/* Aggregate Weighted Pipe */}
                    <div className="p-4 bg-white rounded-lg border border-purple-200 shadow-sm">
                      <div className="text-xs text-gray-600 mb-1">⚖️ Aggregate Weighted Pipe</div>
                      <div className="text-3xl font-bold text-purple-600">
                        ${(actualWeightedPipe / 1000000).toFixed(1)}M
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        Target: <span className="font-bold text-purple-700">
                          ${(weightedPipeTarget / 1000000).toFixed(1)}M
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div 
                          className={`h-2.5 rounded-full transition-all ${
                            actualWeightedPipe >= weightedPipeTarget ? 'bg-green-500' : 'bg-orange-500'
                          }`}
                          style={{ 
                            width: `${Math.min((actualWeightedPipe / weightedPipeTarget * 100), 100)}%` 
                          }}
                        ></div>
                      </div>
                      <div className="text-center text-xs font-semibold text-gray-700 mt-1">
                        {weightedPipeTarget ? ((actualWeightedPipe / weightedPipeTarget * 100).toFixed(1)) : 0}% of target
                      </div>
                    </div>
                  </>
                );
              })()}
            </CardContent>
          </Card>

          {/* Block 5: Deals Closed (Current Period) - Uses NEW tab targets from BO (MONTHLY) */}
          {analytics.deals_closed_current_period && (() => {
            // Use actualPeriodMonths passed from parent Dashboard component
            const periodMonths = actualPeriodMonths || 1;
            const periodStr = analytics.deals_closed_current_period?.period || 'Monthly';
            
            // Calculate dynamic targets (monthly target × period)
            const dealsTarget = tabTargets.deals_closed_tab.deals_closed_target * periodMonths;
            const arrTarget = tabTargets.deals_closed_tab.arr_closed_target * periodMonths;
            
            return (
              <Card className="border-2 border-blue-200 bg-blue-50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg text-center font-semibold">Deals Closed (Current Period)</CardTitle>
                  <CardDescription className="text-center font-medium text-blue-600">
                    {periodStr} {periodMonths > 1 ? `(${periodMonths} months)` : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center bg-white p-3 rounded-lg">
                      <div className="text-3xl font-bold text-gray-800">
                        {analytics.deals_closed_current_period?.deals_closed || 0}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Deals Closed</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Target: {dealsTarget || 0}
                      </div>
                    </div>
                    <div className="text-center bg-white p-3 rounded-lg">
                      <div className="text-3xl font-bold text-green-600">
                        ${analytics.deals_closed_current_period?.arr_closed ? (analytics.deals_closed_current_period.arr_closed / 1000000).toFixed(1) + 'M' : '0'}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">ARR Closed</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Target: ${arrTarget ? (arrTarget / 1000000).toFixed(1) + 'M' : '0'}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className={`h-2.5 rounded-full transition-all ${
                          (analytics.deals_closed_current_period?.arr_closed || 0) >= arrTarget 
                            ? 'bg-green-500' 
                            : 'bg-orange-500'
                        }`}
                        style={{ 
                          width: `${Math.min(
                            arrTarget 
                              ? ((analytics.deals_closed_current_period.arr_closed || 0) / arrTarget * 100) 
                              : 0, 
                            100
                          )}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-center text-sm font-semibold text-gray-700 mt-2">
                      {arrTarget 
                        ? (((analytics.deals_closed_current_period.arr_closed || 0) / arrTarget * 100).toFixed(1)) 
                        : 0}% of ARR target
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })()}
        </div>
      )}
    </div>
  );
}

function Dashboard() {
  const { viewConfig, currentView, user } = useAuth(); // Get current view configuration and user
  const [analytics, setAnalytics] = useState(null);
  const [yearlyData, setYearlyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [monthOffset, setMonthOffset] = useState(0);
  const [forceCurrentMonth, setForceCurrentMonth] = useState(false); // Force to load actual current month
  const [dateRange, setDateRange] = useState(null);
  const [useCustomDate, setUseCustomDate] = useState(false);
  const [importMethod, setImportMethod] = useState('csv'); // 'csv' or 'sheets'
  const [viewMode, setViewMode] = useState('monthly'); // 'monthly' or 'yearly'
  const [activeTab, setActiveTab] = useState(() => {
    // Persist active tab in localStorage
    return localStorage.getItem('activeTab') || 'dashboard';
  }); // Track active tab
  
  // Save activeTab to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);
  
  // Reset AE filter when switching tabs to avoid confusion
  useEffect(() => {
    setSelectedAE('all');
  }, [activeTab]);
  
  // Listen for view config updates from other admins
  useEffect(() => {
    const handleConfigUpdate = () => {
      console.log('View config updated, reloading analytics...');
      // Reload current analytics
      if (viewMode === 'monthly') {
        loadAnalytics();
      } else {
        loadAnalytics(); // Use loadAnalytics for all view modes
      }
      // Note: loadDashboard is no longer needed here as loadAnalytics handles it
    };

    window.addEventListener('viewConfigUpdated', handleConfigUpdate);
    return () => window.removeEventListener('viewConfigUpdated', handleConfigUpdate);
  }, [viewMode, monthOffset]);
  
  // New states for projections
  const [hotDeals, setHotDeals] = useState([]);
  const [originalHotDeals, setOriginalHotDeals] = useState([]); // Store original state for reset
  const [hotLeads, setHotLeads] = useState([]);
  const [performanceSummary, setPerformanceSummary] = useState(null);
  const [hiddenDeals, setHiddenDeals] = useState(new Set());
  const [deletedDeals, setDeletedDeals] = useState(new Set()); // Permanently deleted deals
  const [hiddenLeads, setHiddenLeads] = useState(new Set());
  const [loadingProjections, setLoadingProjections] = useState(false);
  const [selectedAE, setSelectedAE] = useState('all'); // Filter by AE
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [hasSavedPreferences, setHasSavedPreferences] = useState(false); // Track if user has saved preferences in DB
  const [dealProbabilities, setDealProbabilities] = useState({}); // Store probability for each deal {dealId: probability}
  const [isAsherPOVActive, setIsAsherPOVActive] = useState(false); // Simple state, no localStorage
  const [asherPOVTimestamp, setAsherPOVTimestamp] = useState(null); // Store when POV was saved
  
  // Check if current user is Asher
  const isAsher = user?.email === 'asher@primelis.com';
  
  // State for Upsell & Renew tab
  const [upsellRenewData, setUpsellRenewData] = useState(null);
  
  // State for AE Pipeline Breakdown sorting
  const [aeSortConfig, setAESortConfig] = useState({ key: null, direction: 'asc' });
  
  // State for chart legend visibility (meetings attended evolution)
  const [attendedChartVisibility, setAttendedChartVisibility] = useState({
    attended: true,
    poa_generated: true,
    deals_closed: true
  });
  
  // State for Monthly Meetings Evolution chart (Meetings Generation tab)
  const [meetingsEvolutionVisibility, setMeetingsEvolutionVisibility] = useState({
    Inbound: true,
    Outbound: true,
    Referral: true,
    'Upsells/Cross-sell': true,
    Total: true
  });
  
  // State for Monthly Pipeline Evolution chart
  const [pipelineEvolutionVisibility, setPipelineEvolutionVisibility] = useState({
    new_pipe_created: true,
    new_weighted_pipe: true,
    total_pipe: true,
    total_weighted: true
  });
  
  // State for Upsell & Renew Evolution chart
  const [upsellEvolutionVisibility, setUpsellEvolutionVisibility] = useState({
    intro_meetings: true,
    poa_attended: true,
    deals_closed: true
  });
  
  // State for Deals Closed Evolution chart
  const [dealsClosedEvolutionVisibility, setDealsClosedEvolutionVisibility] = useState({
    deals_closed: true,
    arr_closed: true
  });
  
  // State for Deal Pipeline Board (Meetings Generation tab)
  const [pipelineDeals, setPipelineDeals] = useState([]);
  const [originalPipelineDeals, setOriginalPipelineDeals] = useState([]);
  const [selectedPipelineAE, setSelectedPipelineAE] = useState('all');
  const [hasUnsavedPipelineChanges, setHasUnsavedPipelineChanges] = useState(false);
  
  // NEW: Tab targets (direct from BO, no multiplication)
  const [tabTargets, setTabTargets] = useState({
    meetings_attended_tab: {
      meetings_scheduled_target: 50,
      poa_generated_target: 18,
      deals_closed_target: 6
    },
    deals_closed_tab: {
      deals_closed_target: 10,
      arr_closed_target: 500000
    }
  });

  // Helper function to get view-specific targets or fall back to defaults
  const getViewTargets = () => {
    if (viewConfig && viewConfig.targets) {
      return {
        dashboard: viewConfig.targets.dashboard || {},
        meeting_generation: viewConfig.targets.meeting_generation || {},
        meeting_attended: viewConfig.targets.meeting_attended || {}
      };
    }
    // Default targets for Organic view (existing behavior)
    return {
      dashboard: {
        objectif_6_mois: 4500000,
        deals: 25,
        new_pipe_created: 2000000,
        weighted_pipe: 800000
      },
      meeting_generation: {
        intro: 45,
        inbound: 22,
        outbound: 17,
        referrals: 11,
        upsells_x: 0
      },
      meeting_attended: {
        poa: 18,
        deals_closed: 6
      }
    };
  };

  const loadTabTargets = async () => {
    try {
      if (currentView?.id) {
        const response = await axios.get(`${API}/views/${currentView.id}/tab-targets`);
        setTabTargets(response.data);
      }
    } catch (error) {
      console.error('Error loading tab targets:', error);
    }
  };

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      let yearlyResponse;
      
      // Build view_id parameter if available
      const viewParam = currentView?.id ? `&view_id=${currentView.id}` : '';
      
      if (useCustomDate && dateRange?.from && dateRange?.to) {
        // Use custom date range
        const startDate = format(dateRange.from, 'yyyy-MM-dd');
        const endDate = format(dateRange.to, 'yyyy-MM-dd');
        response = await axios.get(`${API}/analytics/custom?start_date=${startDate}&end_date=${endDate}${viewParam}`);
        // Also load yearly data for comparison
        yearlyResponse = await axios.get(`${API}/analytics/yearly?year=2025${viewParam}`);
      } else if (viewMode === 'yearly') {
        // Use yearly view
        response = await axios.get(`${API}/analytics/yearly?year=2025${viewParam}`);
        yearlyResponse = response; // Same data
      } else {
        // Use monthly offset
        response = await axios.get(`${API}/analytics/monthly?month_offset=${monthOffset}${viewParam}`);
        // Also load yearly data for Deals & Pipeline comparison
        yearlyResponse = await axios.get(`${API}/analytics/yearly?year=2025${viewParam}`);
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
    // Don't reload projections data if user is viewing Asher's POV
    if (!isAsherPOVActive) {
      loadProjectionsData();
    }
    loadUpsellRenewData();
    loadTabTargets(); // Load tab targets when view changes
  }, [monthOffset, dateRange, useCustomDate, viewMode, currentView]); // Added currentView to reload when view changes

  const handleUploadSuccess = () => {
    loadAnalytics();
    // Don't reload projections if viewing Asher POV
    if (!isAsherPOVActive) {
      loadProjectionsData();
    }
    loadUpsellRenewData();
  };

  // Load Upsell & Renew data - synchronized with loadAnalytics
  const loadUpsellRenewData = async () => {
    try {
      let startDate, endDate;
      
      if (useCustomDate && dateRange?.from && dateRange?.to) {
        // Custom date range
        startDate = format(dateRange.from, 'yyyy-MM-dd');
        endDate = format(dateRange.to, 'yyyy-MM-dd');
      } else if (viewMode === 'yearly') {
        // July To Dec view (H2 2025)
        startDate = '2025-07-01';
        endDate = '2025-12-31';
      } else {
        // Monthly view with offset
        const now = new Date();
        const targetDate = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1);
        startDate = format(new Date(targetDate.getFullYear(), targetDate.getMonth(), 1), 'yyyy-MM-dd');
        endDate = format(new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0), 'yyyy-MM-dd');
      }
      
      // Build view_id parameter if available
      const viewParam = currentView?.id ? `&view_id=${currentView.id}` : '';
      
      const response = await axios.get(`${API}/analytics/upsell-renewals?start_date=${startDate}&end_date=${endDate}${viewParam}`);
      setUpsellRenewData(response.data);
    } catch (error) {
      console.error('Error loading upsell/renew data:', error);
    }
  };

  // New functions for projections data
  // Load user's saved projections preferences from backend
  const loadProjectionsPreferences = async () => {
    if (!currentView?.id) return null;
    
    try {
      const response = await axios.get(`${API}/user/projections-preferences`, {
        params: { view_id: currentView.id },
        withCredentials: true
      });
      
      if (response.data.has_preferences) {
        console.log('✅ Loaded saved projections preferences:', response.data);
        return response.data.preferences;
      }
      return null;
    } catch (error) {
      console.error('Error loading projections preferences:', error);
      return null;
    }
  };

  // Load Asher's projections preferences from CURRENT view (for "Asher POV" feature)
  // Load and apply Asher POV (NEW - uses dedicated backend endpoint)
  const applyAsherPOV = async () => {
    if (!currentView?.id) {
      alert('⚠️ No view selected');
      return;
    }
    
    try {
      // Load Asher POV from dedicated endpoint
      const response = await axios.get(`${API}/asher-pov/load`, {
        params: { view_id: currentView.id },
        withCredentials: true
      });
      
      if (!response.data.has_pov) {
        const viewName = currentView?.name || 'this view';
        alert(`⚠️ Asher has not saved a POV for ${viewName} yet.`);
        return;
      }
      
      const asherPrefs = response.data.preferences;
      const timestamp = response.data.timestamp;
      
      // Reload fresh data from CURRENT view
      const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
      const [hotDealsResponse, hotLeadsResponse] = await Promise.all([
        axios.get(`${API}/projections/hot-deals${viewParam}`),
        axios.get(`${API}/projections/hot-leads${viewParam}`)
      ]);
      
      const combinedDeals = [
        ...hotDealsResponse.data.map(deal => ({...deal, source: 'hot-deals'})),
        ...hotLeadsResponse.data.map(lead => ({...lead, source: 'hot-leads'}))
      ];
      
      // Deduplicate deals
      const seenDeals = new Map();
      const uniqueDeals = combinedDeals.filter(deal => {
        const dealKey = `${deal.client || deal.company || deal.lead_name}-${deal.stage}`;
        if (seenDeals.has(dealKey)) {
          return false;
        }
        seenDeals.set(dealKey, true);
        return true;
      });
      
      const dealsWithColumns = uniqueDeals.map((deal, index) => ({
        ...deal,
        client: deal.client || deal.company || deal.lead_name || `Deal ${index + 1}`,
        pipeline: deal.pipeline || deal.expected_arr || deal.value || 0,
        owner: deal.owner || deal.ae || 'TBD',
        column: deal.column || (() => {
          if (deal.stage === 'B Legals') return 'next14';
          if (deal.stage === 'C Proposal sent') return 'next30';
          if (deal.stage === 'D POA Booked') return 'next60';
          return index % 3 === 0 ? 'next14' : index % 3 === 1 ? 'next30' : 'next60';
        })()
      }));
      
      // Apply Asher's organization (with MERGE: new deals appear too!)
      const reconstructedDeals = [];
      const hiddenSet = new Set();
      const deletedSet = new Set();
      const probabilities = {};
      const processedDealIds = new Set();
      
      // First pass: reconstruct saved deals in their saved order
      ['next14', 'next30', 'next60', 'delayed'].forEach(columnKey => {
        const savedColumn = asherPrefs[columnKey] || [];
        savedColumn.sort((a, b) => (a.order || 0) - (b.order || 0));
        
        savedColumn.forEach(savedDeal => {
          if (savedDeal.deleted) {
            deletedSet.add(savedDeal.id);
            processedDealIds.add(savedDeal.id);
            return;
          }
          
          const dealData = dealsWithColumns.find(d => d.id === savedDeal.id);
          if (dealData) {
            dealData.column = columnKey;
            reconstructedDeals.push(dealData);
            processedDealIds.add(savedDeal.id);
            
            if (savedDeal.hidden) {
              hiddenSet.add(savedDeal.id);
            }
            if (savedDeal.probability) {
              probabilities[savedDeal.id] = savedDeal.probability;
            }
          }
        });
      });
      
      // Second pass: ADD NEW DEALS (that weren't in Asher's saved preferences)
      // These are new deals that appeared since Asher last saved
      const newDeals = dealsWithColumns.filter(deal => 
        !processedDealIds.has(deal.id) && !deletedSet.has(deal.id)
      );
      
      if (newDeals.length > 0) {
        console.log(`📝 ${newDeals.length} new deals added to Asher POV:`, newDeals.map(d => d.client));
        reconstructedDeals.push(...newDeals);
      }
      
      setHotDeals(reconstructedDeals);
      setHiddenDeals(hiddenSet);
      setDeletedDeals(deletedSet);
      setDealProbabilities(probabilities);
      setHasUnsavedChanges(false); // POV is clean (loaded from server)
      setIsAsherPOVActive(true); // Mark that we're viewing Asher's POV
      setAsherPOVTimestamp(timestamp);
      
      const viewName = currentView?.name || 'current view';
      console.log(`👁️ Asher POV loaded for ${viewName}: ${reconstructedDeals.length} deals (${newDeals.length} new), ${deletedSet.size} deleted, ${hiddenSet.size} hidden`);
      alert(`👁️ Asher's POV applied for ${viewName}!\n\nSaved: ${timestamp}\nDeals: ${reconstructedDeals.length} (${newDeals.length} new)`);
      
    } catch (error) {
      console.error('Error applying Asher\'s POV:', error);
      alert('❌ Failed to apply Asher\'s POV. Please try again.');
    }
  };

  // Save projections preferences to backend
  const saveProjectionsPreferences = async (dealsData, hiddenDealsSet, deletedDealsSet = deletedDeals) => {
    if (!currentView?.id) return;
    
    try {
      // Organize deals by column with hidden, deleted status AND ORDER (index)
      const next14Deals = dealsData
        .filter(d => d.column === 'next14')
        .map((d, index) => ({ 
          id: d.id, 
          hidden: hiddenDealsSet.has(d.id), 
          deleted: deletedDealsSet.has(d.id),
          probability: dealProbabilities[d.id] || 75, // Save custom probability
          order: index 
        }));
      
      const next30Deals = dealsData
        .filter(d => d.column === 'next30')
        .map((d, index) => ({ 
          id: d.id, 
          hidden: hiddenDealsSet.has(d.id), 
          deleted: deletedDealsSet.has(d.id),
          probability: dealProbabilities[d.id] || 75,
          order: index 
        }));
      
      const next60Deals = dealsData
        .filter(d => d.column === 'next60')
        .map((d, index) => ({ 
          id: d.id, 
          hidden: hiddenDealsSet.has(d.id), 
          deleted: deletedDealsSet.has(d.id),
          probability: dealProbabilities[d.id] || 75,
          order: index 
        }));
      
      const delayedDeals = dealsData
        .filter(d => d.column === 'delayed')
        .map((d, index) => ({ 
          id: d.id, 
          hidden: hiddenDealsSet.has(d.id), 
          deleted: deletedDealsSet.has(d.id),
          probability: dealProbabilities[d.id] || 75,
          order: index 
        }));
      
      await axios.post(`${API}/user/projections-preferences`, {
        view_id: currentView.id,
        preferences: {
          next14: next14Deals,
          next30: next30Deals,
          next60: next60Deals,
          delayed: delayedDeals
        }
      }, {
        withCredentials: true
      });
      
      console.log('✅ Projections preferences saved successfully (with deleted flag and probabilities)');
    } catch (error) {
      console.error('Error saving projections preferences:', error);
      throw error;
    }
  };

  // Reset projections preferences (delete from backend)
  const resetProjectionsPreferences = async () => {
    if (!currentView?.id) return;
    
    try {
      await axios.delete(`${API}/user/projections-preferences`, {
        params: { view_id: currentView.id },
        withCredentials: true
      });
      
      console.log('✅ Projections preferences reset successfully');
    } catch (error) {
      console.error('Error resetting projections preferences:', error);
      throw error;
    }
  };

  const loadProjectionsData = async () => {
    setLoadingProjections(true);
    try {
      // Build view_id parameter if available
      const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
      
      const [hotDealsResponse, hotLeadsResponse, performanceResponse] = await Promise.all([
        axios.get(`${API}/projections/hot-deals${viewParam}`),
        axios.get(`${API}/projections/hot-leads${viewParam}`),
        axios.get(`${API}/projections/performance-summary${viewParam}`)
      ]);
      
      // Combine hot deals (B Legals) and hot leads (POA Booked + Proposal sent) for the interactive board
      const combinedDeals = [
        ...hotDealsResponse.data.map(deal => ({...deal, source: 'hot-deals'})),
        ...hotLeadsResponse.data.map(lead => ({...lead, source: 'hot-leads'}))
      ];

      // Deduplicate deals based on client name + stage (same client in same stage = duplicate)
      const seenDeals = new Map();
      const uniqueDeals = combinedDeals.filter(deal => {
        const dealKey = `${deal.client || deal.company || deal.lead_name}-${deal.stage}`;
        if (seenDeals.has(dealKey)) {
          console.log(`⚠️ Duplicate detected and removed: ${dealKey}`);
          return false; // Skip duplicate
        }
        seenDeals.set(dealKey, true);
        return true;
      });
      
      console.log(`📊 Deals loaded: ${combinedDeals.length} total, ${uniqueDeals.length} unique (${combinedDeals.length - uniqueDeals.length} duplicates removed)`);

      // Assign columns based on deal stage for logical grouping
      const dealsWithColumns = uniqueDeals.map((deal, index) => ({
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
      
      // Try to load saved preferences from backend
      const savedPreferences = await loadProjectionsPreferences();
      
      if (savedPreferences) {
        try {
          // Rebuild deals array from saved preferences WITH ORDER
          const reconstructedDeals = [];
          const hiddenSet = new Set();
          const deletedSet = new Set();
          const probabilities = {};
          
          // Process each column from saved preferences (including delayed)
          ['next14', 'next30', 'next60', 'delayed'].forEach(columnKey => {
            const savedColumn = savedPreferences[columnKey] || [];
            
            // Sort by order to maintain saved sequence
            savedColumn.sort((a, b) => (a.order || 0) - (b.order || 0));
            
            savedColumn.forEach(savedDeal => {
              // Skip permanently deleted deals
              if (savedDeal.deleted) {
                deletedSet.add(savedDeal.id);
                return;
              }
              
              // Find the deal in our fresh data
              const dealData = dealsWithColumns.find(d => d.id === savedDeal.id);
              if (dealData) {
                // Update its column from saved preferences
                dealData.column = columnKey;
                reconstructedDeals.push(dealData);
                if (savedDeal.hidden) {
                  hiddenSet.add(savedDeal.id);
                }
                // Load saved probability
                if (savedDeal.probability) {
                  probabilities[savedDeal.id] = savedDeal.probability;
                }
              }
            });
          });
          
          // Add any new deals that weren't in saved preferences (and not deleted)
          dealsWithColumns.forEach(deal => {
            if (!reconstructedDeals.find(d => d.id === deal.id) && !deletedSet.has(deal.id)) {
              reconstructedDeals.push(deal);
            }
          });
          
          setHotDeals(reconstructedDeals);
          setHiddenDeals(hiddenSet);
          setDeletedDeals(deletedSet);
          setDealProbabilities(probabilities);
          setHasSavedPreferences(true); // User has saved preferences
          setOriginalHotDeals(JSON.parse(JSON.stringify(dealsWithColumns.filter(d => !deletedSet.has(d.id))))); // Keep original for reset (excluding deleted)
          console.log('✅ Applied saved projections preferences with order, deleted filter, and probabilities');
          console.log(`   Deleted ${deletedSet.size} deals permanently`);
        } catch (e) {
          console.error('Error applying saved preferences:', e);
          // Fall back to fresh data
          setHotDeals(dealsWithColumns);
          setOriginalHotDeals(JSON.parse(JSON.stringify(dealsWithColumns)));
          setHiddenDeals(new Set());
          setDeletedDeals(new Set());
          setHasSavedPreferences(false);
        }
      } else {
        setHotDeals(dealsWithColumns);
        setOriginalHotDeals(JSON.parse(JSON.stringify(dealsWithColumns))); // Deep copy for reset
        setHiddenDeals(new Set());
        setDeletedDeals(new Set());
        setHasSavedPreferences(false); // No saved preferences = default state
      }
      
      setHotLeads(hotLeadsResponse.data);
      setPerformanceSummary(performanceResponse.data);
      setHasUnsavedChanges(false); // Reset unsaved changes flag
    } catch (error) {
      console.error('Error loading projections data:', error);
    } finally {
      setLoadingProjections(false);
    }
  };

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const { source, destination } = result;
    
    // Handle column-based drag and drop for the new interactive board (including delayed column)
    if (['next14', 'next30', 'next60', 'delayed'].includes(source.droppableId) || 
        ['next14', 'next30', 'next60', 'delayed'].includes(destination.droppableId)) {
      
      const newDeals = Array.from(hotDeals);
      const draggedDeal = newDeals.find(deal => deal.id === result.draggableId);
      
      if (draggedDeal) {
        // Update the deal's column assignment
        draggedDeal.column = destination.droppableId;
        setHotDeals(newDeals);
        setHasUnsavedChanges(true); // Mark as changed
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

  // Handle permanent deletion of a deal
  const handleDeleteDeal = (dealId) => {
    setDeletedDeals(prev => {
      const newSet = new Set(prev);
      newSet.add(dealId);
      return newSet;
    });
    setHasUnsavedChanges(true);
    console.log(`🗑️ Deal ${dealId} marked as permanently deleted`);
  };

  // Save current board state to backend
  const handleSaveBoard = async () => {
    try {
      await saveProjectionsPreferences(hotDeals, hiddenDeals, deletedDeals);
      setOriginalHotDeals(JSON.parse(JSON.stringify(hotDeals))); // Update original to current
      setHasUnsavedChanges(false);
      setHasSavedPreferences(true); // Mark that user now has saved preferences
      setIsAsherPOVActive(false); // Exit Asher POV mode after saving your own preferences
      alert('💾 Board state saved successfully! (including deleted deals)');
    } catch (error) {
      console.error('Error saving board state:', error);
      alert('❌ Failed to save board state. Please try again.');
    }
  };

  // Save as Asher POV (Asher only) - NEW dedicated endpoint
  const handleSaveAsAsherPOV = async () => {
    if (!isAsher) {
      alert('❌ Only Asher can save as Asher POV');
      return;
    }
    
    if (!currentView?.id) {
      alert('⚠️ No view selected');
      return;
    }
    
    try {
      // Organize deals by column with order, hidden, deleted, probability
      const next14Deals = hotDeals
        .filter(deal => deal.column === 'next14')
        .map((deal, index) => ({
          id: deal.id,
          order: index,
          hidden: hiddenDeals.has(deal.id),
          deleted: deletedDeals.has(deal.id),
          probability: dealProbabilities[deal.id] || 75
        }));

      const next30Deals = hotDeals
        .filter(deal => deal.column === 'next30')
        .map((deal, index) => ({
          id: deal.id,
          order: index,
          hidden: hiddenDeals.has(deal.id),
          deleted: deletedDeals.has(deal.id),
          probability: dealProbabilities[deal.id] || 75
        }));

      const next60Deals = hotDeals
        .filter(deal => deal.column === 'next60')
        .map((deal, index) => ({
          id: deal.id,
          order: index,
          hidden: hiddenDeals.has(deal.id),
          deleted: deletedDeals.has(deal.id),
          probability: dealProbabilities[deal.id] || 75
        }));

      const delayedDeals = hotDeals
        .filter(deal => deal.column === 'delayed')
        .map((deal, index) => ({
          id: deal.id,
          order: index,
          hidden: hiddenDeals.has(deal.id),
          deleted: deletedDeals.has(deal.id),
          probability: dealProbabilities[deal.id] || 75
        }));

      // Save to dedicated Asher POV endpoint
      const response = await axios.post(`${API}/asher-pov/save`, {
        view_id: currentView.id,
        preferences: {
          next14: next14Deals,
          next30: next30Deals,
          next60: next60Deals,
          delayed: delayedDeals
        }
      }, {
        withCredentials: true
      });
      
      const timestamp = response.data.timestamp;
      
      setOriginalHotDeals(JSON.parse(JSON.stringify(hotDeals)));
      setHasUnsavedChanges(false);
      setHasSavedPreferences(true);
      setIsAsherPOVActive(true); // Stay in Asher POV mode
      setAsherPOVTimestamp(timestamp);
      
      const viewName = currentView?.name || 'current view';
      alert(`👁️ Saved as Asher POV for ${viewName}!\n\n${timestamp}\n\nOther users can now load this view.`);
      console.log(`✅ Asher POV saved for ${viewName} at ${timestamp}`);
      
    } catch (error) {
      console.error('Error saving Asher POV:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`❌ Failed to save Asher POV: ${errorMsg}`);
    }
  };

  // Reset board to original state (reload fresh data from server)
  const handleResetBoard = async () => {
    if (window.confirm('⚠️ Are you sure you want to reset all changes? This will restore all deals and clear all deletions, hidden cards, and custom %.')) {
      try {
        // Delete user preferences from backend first
        await resetProjectionsPreferences();
        
        // Force reload fresh default data (bypass any cached preferences)
        const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
        const [hotDealsResponse, hotLeadsResponse] = await Promise.all([
          axios.get(`${API}/projections/hot-deals${viewParam}`),
          axios.get(`${API}/projections/hot-leads${viewParam}`)
        ]);
        
        const combinedDeals = [
          ...hotDealsResponse.data.map(deal => ({...deal, source: 'hot-deals'})),
          ...hotLeadsResponse.data.map(lead => ({...lead, source: 'hot-leads'}))
        ];
        
        // Deduplicate deals
        const seenDeals = new Map();
        const uniqueDeals = combinedDeals.filter(deal => {
          const dealKey = `${deal.client || deal.company || deal.lead_name}-${deal.stage}`;
          if (seenDeals.has(dealKey)) {
            return false;
          }
          seenDeals.set(dealKey, true);
          return true;
        });
        
        const dealsWithColumns = uniqueDeals.map((deal, index) => ({
          ...deal,
          client: deal.client || deal.company || deal.lead_name || `Deal ${index + 1}`,
          pipeline: deal.pipeline || deal.expected_arr || deal.value || 0,
          owner: deal.owner || deal.ae || 'TBD',
          column: deal.column || (() => {
            if (deal.stage === 'B Legals') return 'next14';
            if (deal.stage === 'C Proposal sent') return 'next30';
            if (deal.stage === 'D POA Booked') return 'next60';
            return index % 3 === 0 ? 'next14' : index % 3 === 1 ? 'next30' : 'next60';
          })()
        }));
        
        // Set to pure default state (no preferences applied)
        setHotDeals(dealsWithColumns);
        setOriginalHotDeals(JSON.parse(JSON.stringify(dealsWithColumns)));
        setHiddenDeals(new Set());
        setDeletedDeals(new Set());
        setDealProbabilities({});
        setHasUnsavedChanges(false);
        setHasSavedPreferences(false);
        setIsAsherPOVActive(false); // Exit Asher POV mode
        
        console.log('✅ Board reset to pure default state');
        alert('✅ Board reset to default state! All deals restored.');
      } catch (error) {
        console.error('Error resetting board:', error);
        alert('❌ Failed to reset board. Please try again.');
      }
    }
  };

  // Reset Asher POV (Asher only) - resets Asher's saved preferences
  // Reset Asher POV (Asher only) - NEW dedicated endpoint
  const handleResetAsAsherPOV = async () => {
    if (!isAsher) {
      alert('❌ Only Asher can reset Asher POV');
      return;
    }
    
    if (!currentView?.id) {
      alert('⚠️ No view selected');
      return;
    }
    
    const viewName = currentView?.name || 'this view';
    
    if (window.confirm(`⚠️ Are you sure you want to reset Asher POV for ${viewName}?\n\nThis will delete your saved POV and others will see the default state.`)) {
      try {
        // Delete from dedicated Asher POV endpoint
        await axios.delete(`${API}/asher-pov/reset`, {
          params: { view_id: currentView.id },
          withCredentials: true
        });
        
        // Reload fresh default data
        const viewParam = currentView?.id ? `?view_id=${currentView.id}` : '';
        const [hotDealsResponse, hotLeadsResponse] = await Promise.all([
          axios.get(`${API}/projections/hot-deals${viewParam}`),
          axios.get(`${API}/projections/hot-leads${viewParam}`)
        ]);
        
        const combinedDeals = [
          ...hotDealsResponse.data.map(deal => ({...deal, source: 'hot-deals'})),
          ...hotLeadsResponse.data.map(lead => ({...lead, source: 'hot-leads'}))
        ];
        
        // Deduplicate deals
        const seenDeals = new Map();
        const uniqueDeals = combinedDeals.filter(deal => {
          const dealKey = `${deal.client || deal.company || deal.lead_name}-${deal.stage}`;
          if (seenDeals.has(dealKey)) {
            return false;
          }
          seenDeals.set(dealKey, true);
          return true;
        });
        
        const dealsWithColumns = uniqueDeals.map((deal, index) => ({
          ...deal,
          client: deal.client || deal.company || deal.lead_name || `Deal ${index + 1}`,
          pipeline: deal.pipeline || deal.expected_arr || deal.value || 0,
          owner: deal.owner || deal.ae || 'TBD',
          column: deal.column || (() => {
            if (deal.stage === 'B Legals') return 'next14';
            if (deal.stage === 'C Proposal sent') return 'next30';
            if (deal.stage === 'D POA Booked') return 'next60';
            return index % 3 === 0 ? 'next14' : index % 3 === 1 ? 'next30' : 'next60';
          })()
        }));
        
        setHotDeals(dealsWithColumns);
        setOriginalHotDeals(JSON.parse(JSON.stringify(dealsWithColumns)));
        setHiddenDeals(new Set());
        setDeletedDeals(new Set());
        setDealProbabilities({});
        setHasUnsavedChanges(false);
        setHasSavedPreferences(false);
        setIsAsherPOVActive(false);
        setAsherPOVTimestamp(null);
        
        console.log(`✅ Asher POV reset for ${viewName}`);
        alert(`✅ Asher POV reset for ${viewName}!\n\nOthers will now see the default state when they click "Asher POV".`);
      } catch (error) {
        console.error('Error resetting Asher POV:', error);
        const errorMsg = error.response?.data?.detail || error.message;
        alert(`❌ Failed to reset Asher POV: ${errorMsg}`);
      }
    }
  };

  // Get unique AEs from deals for filter dropdown
  const getUniqueAEs = () => {
    const aes = new Set();
    hotDeals.forEach(deal => {
      if (deal.owner) aes.add(deal.owner);
    });
    return Array.from(aes).sort();
  };

  // Filter deals by selected AE
  const getFilteredDeals = () => {
    if (selectedAE === 'all') return hotDeals;
    return hotDeals.filter(deal => deal.owner === selectedAE);
  };

  const hideItem = (type, id) => {
    if (type === 'deals') {
      setHiddenDeals(prev => new Set([...prev, id]));
      setHasUnsavedChanges(true); // Mark as changed
    } else if (type === 'leads') {
      setHiddenLeads(prev => new Set([...prev, id]));
    }
  };

  // Handler for deal probability changes
  const handleDealProbabilityChange = (dealId, probability) => {
    setDealProbabilities(prev => ({
      ...prev,
      [dealId]: probability
    }));
    setHasUnsavedChanges(true);
  };


  const resetView = (type) => {
    if (type === 'deals') {
      setHiddenDeals(new Set());
      if (!isAsherPOVActive) {
        loadProjectionsData(); // Reload original data
      }
    } else if (type === 'leads') {
      setHiddenLeads(new Set());
      if (!isAsherPOVActive) {
        loadProjectionsData(); // Reload original data
      }
    }
  };

  const filteredHotDeals = hotDeals.filter(deal => !hiddenDeals.has(deal.id));
  const filteredHotLeads = hotLeads.filter(lead => !hiddenLeads.has(lead.id));

  // Sortable data hooks for AE Performance tables
  const { items: sortedAeIntros, requestSort: requestAeIntrosSort, sortConfig: aeIntrosSortConfig } = 
    useSortableData(analytics?.ae_performance?.ae_performance || []);
  const { items: sortedIntrosDetails, requestSort: requestIntrosDetailsSort, sortConfig: introsDetailsSortConfig } = 
    useSortableData(analytics?.ae_performance?.intros_details || []);
  const { items: sortedAePoa, requestSort: requestAePoaSort, sortConfig: aePoaSortConfig} = 
    useSortableData(analytics?.ae_performance?.ae_poa_performance || []);
  const { items: sortedPoaDetails, requestSort: requestPoaDetailsSort, sortConfig: poaDetailsSortConfig } = 
    useSortableData(analytics?.ae_performance?.poa_attended_details || []);
  
  // State for AE Pipeline Breakdown sorting
  const [aePipelineSortConfig, setAePipelineSortConfig] = useState({ key: 'total', direction: 'descending' });
  
  // State for Meeting Details filters and sorting
  const [meetingDetailsFilters, setMeetingDetailsFilters] = useState({
    bdr: 'all',
    source: 'all',
    relevance: 'all',
    stage: 'all'
  });
  const { items: sortedMeetingDetails, requestSort: requestMeetingDetailsSort, sortConfig: meetingDetailsSortConfig } = 
    useSortableData(analytics?.meeting_generation?.meetings_details || []);

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

  // Calculate actual period months based on view mode and date range
  let actualPeriodMonths = 1; // Default to 1 month
  
  if (useCustomDate && dateRange?.from && dateRange?.to) {
    // Calculate months from custom date range
    const diffTime = Math.abs(dateRange.to - dateRange.from);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    actualPeriodMonths = Math.max(1, Math.round(diffDays / 30.44)); // Convert days to months
  } else if (viewMode === 'yearly') {
    // July to December = 6 months
    actualPeriodMonths = 6;
  } else {
    // Monthly view = 1 month
    actualPeriodMonths = 1;
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold dark:text-white">
            {useCustomDate ? 'Custom Report' : 
             viewMode === 'yearly' ? 'July To Dec 2025 Report' : 'Monthly Report'}
          </h1>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 w-full sm:w-auto">
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                variant={!useCustomDate && viewMode === 'monthly' ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setUseCustomDate(false);
                  setViewMode('monthly');
                }}
                className="flex items-center gap-1 text-xs sm:text-sm"
              >
                <Calendar className="h-3 w-3 sm:h-4 sm:w-4" />
                Monthly
              </Button>
              <Button
                variant={!useCustomDate && viewMode === 'yearly' ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setUseCustomDate(false);
                  setViewMode('yearly');
                }}
                className="flex items-center gap-1 text-xs sm:text-sm"
              >
                <CalendarDays className="h-3 w-3 sm:h-4 sm:w-4" />
                July To Dec
              </Button>
              <Button
                variant={useCustomDate ? 'default' : 'outline'}
                size="sm"
                onClick={() => setUseCustomDate(true)}
                className="flex items-center gap-1 text-xs sm:text-sm"
              >
                <CalendarDays className="h-3 w-3 sm:h-4 sm:w-4" />
                Custom Period
              </Button>
            </div>
            {!useCustomDate && viewMode === 'monthly' && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setMonthOffset(monthOffset + 1);
                    setForceCurrentMonth(false);
                  }}
                >
                  ← Previous Month
                </Button>
                <span className="px-3 py-1 text-sm font-medium bg-slate-100 dark:bg-[#24272e] rounded-md whitespace-nowrap">
                  {forceCurrentMonth ? '📅 Current Month' : monthOffset === 0 ? 'Latest Data' : `${Math.abs(monthOffset)} ${Math.abs(monthOffset) === 1 ? 'month' : 'months'} ${monthOffset > 0 ? 'ago' : 'ahead'}`}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setMonthOffset(monthOffset - 1);
                    setForceCurrentMonth(false);
                  }}
                  disabled={monthOffset <= 0 && !forceCurrentMonth}
                >
                  Next Month →
                </Button>
                {(monthOffset !== 0 || !forceCurrentMonth) && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setMonthOffset(0);
                      setForceCurrentMonth(true);
                    }}
                    className="ml-2"
                  >
                    📅 Current Month
                  </Button>
                )}
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

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="w-full flex overflow-x-auto overflow-y-hidden scrollbar-hide">
          <TabsTrigger value="dashboard" className="flex-shrink-0">Dashboard</TabsTrigger>
          <TabsTrigger value="meetings" className="flex-shrink-0 whitespace-nowrap">Meetings Generation</TabsTrigger>
          <TabsTrigger value="attended" className="flex-shrink-0 whitespace-nowrap">Meetings Attended</TabsTrigger>
          <TabsTrigger value="upsell" className="flex-shrink-0 whitespace-nowrap">Upsell & Renew</TabsTrigger>
          <TabsTrigger value="deals" className="flex-shrink-0 whitespace-nowrap">Deals & Pipeline</TabsTrigger>
          <TabsTrigger value="projections" className="flex-shrink-0">Projections</TabsTrigger>
        </TabsList>

        {/* Main Dashboard */}
        <TabsContent value="dashboard">
          <MainDashboard analytics={analytics} currentView={currentView} tabTargets={tabTargets} actualPeriodMonths={actualPeriodMonths} />
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
              <div className="relative">
                <MetricCard
                  title="Referrals"
                  value={analytics.meeting_generation.referrals}
                  target={analytics.meeting_generation.referral_target}
                  icon={Users}
                  color="purple"
                />
                <div className="text-xs text-gray-500 italic mt-1 px-2">
                  * Includes: Internal, External & Client Referrals
                </div>
              </div>
              <MetricCard
                title="Upsells / Cross-sell"
                value={analytics.dashboard_blocks?.block_1_meetings?.upsells_actual || 0}
                target={analytics.dashboard_blocks?.block_1_meetings?.upsells_target || 0}
                icon={TrendingUp}
                color="indigo"
              />
              <MetricCard
                title="Event"
                value={analytics.meeting_generation.event || 0}
                target={analytics.meeting_generation.event_target || 0}
                icon={Calendar}
                color="teal"
              />
              <MetricCard
                title="None & Non assigned"
                value={analytics.meeting_generation.none_unassigned || 0}
                target={0}
                icon={AlertCircle}
                color="gray"
              />
            </div>

            {/* Deal Pipeline Board moved after Source Distribution */}

            {/* Monthly Meetings Evolution Chart - MOVED TO TOP */}
            {analytics.meeting_generation.meetings_details && analytics.meeting_generation.meetings_details.length > 0 && (() => {
              // Group meetings by month and source
              const monthlyData = {};
              
              analytics.meeting_generation.meetings_details.forEach(meeting => {
                if (meeting.discovery_date) {
                  // Extract month (YYYY-MM format)
                  const date = new Date(meeting.discovery_date);
                  const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                  const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                  
                  if (!monthlyData[monthKey]) {
                    monthlyData[monthKey] = {
                      month: monthLabel,
                      sortKey: monthKey,
                      Inbound: 0,
                      Outbound: 0,
                      Referral: 0,
                      'Upsells/Cross-sell': 0,
                      Total: 0
                    };
                  }
                  
                  // Categorize by source
                  const source = meeting.type_of_source || 'Other';
                  if (source.toLowerCase().includes('inbound')) {
                    monthlyData[monthKey].Inbound++;
                  } else if (source.toLowerCase().includes('outbound')) {
                    monthlyData[monthKey].Outbound++;
                  } else if (source.toLowerCase().includes('referral') || source.toLowerCase().includes('référence')) {
                    monthlyData[monthKey].Referral++;
                  } else if (source.toLowerCase().includes('upsell') || source.toLowerCase().includes('cross')) {
                    monthlyData[monthKey]['Upsells/Cross-sell']++;
                  } else {
                    monthlyData[monthKey].Outbound++; // Default to outbound
                  }
                  
                  monthlyData[monthKey].Total++;
                }
              });
              
              // Convert to array and sort by month
              const chartData = Object.values(monthlyData)
                .sort((a, b) => a.sortKey.localeCompare(b.sortKey));
              
              const handleLegendClick = (dataKey) => {
                setMeetingsEvolutionVisibility(prev => ({
                  ...prev,
                  [dataKey]: !prev[dataKey]
                }));
              };
              
              // Custom legend with checkboxes
              const legendData = [
                { key: 'Inbound', color: '#10b981', label: 'Inbound' },
                { key: 'Outbound', color: '#f97316', label: 'Outbound' },
                { key: 'Referral', color: '#a855f7', label: 'Referral' },
                { key: 'Upsells/Cross-sell', color: '#6366f1', label: 'Upsells/Cross-sell' },
                { key: 'Total', color: '#1e40af', label: 'Total Meetings' }
              ];
              
              return (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>Monthly Meetings Evolution</CardTitle>
                    <CardDescription>
                      Total meetings generated per month with breakdown by source
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={350}>
                      <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        {meetingsEvolutionVisibility.Inbound && (
                          <Bar dataKey="Inbound" fill="#10b981" name="Inbound" />
                        )}
                        {meetingsEvolutionVisibility.Outbound && (
                          <Bar dataKey="Outbound" fill="#f97316" name="Outbound" />
                        )}
                        {meetingsEvolutionVisibility.Referral && (
                          <Bar dataKey="Referral" fill="#a855f7" name="Referral" />
                        )}
                        {meetingsEvolutionVisibility['Upsells/Cross-sell'] && (
                          <Bar dataKey="Upsells/Cross-sell" fill="#6366f1" name="Upsells/Cross-sell" />
                        )}
                        {meetingsEvolutionVisibility.Total && (
                          <Line 
                            type="monotone" 
                            dataKey="Total" 
                            stroke="#1e40af" 
                            strokeWidth={3}
                            name="Total Meetings" 
                          />
                        )}
                      </ComposedChart>
                    </ResponsiveContainer>
                    
                    {/* Custom Legend */}
                    <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
                      {legendData.map(({ key, color, label }) => (
                        <button
                          key={key}
                          onClick={() => handleLegendClick(key)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                            meetingsEvolutionVisibility[key] 
                              ? 'bg-white shadow-sm border border-gray-200' 
                              : 'bg-gray-100 opacity-60 hover:opacity-80'
                          }`}
                        >
                          <div 
                            className="w-3 h-3 rounded-sm"
                            style={{ backgroundColor: color }}
                          />
                          <span className={`text-sm ${meetingsEvolutionVisibility[key] ? 'text-gray-700 font-medium' : 'text-gray-500'}`}>
                            {label}
                          </span>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

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

            {/* Deal Pipeline Board - Inbox vs Intro Attended */}
            {analytics.meeting_generation.meetings_details && analytics.meeting_generation.meetings_details.length > 0 && (() => {
              // Calculate days since creation
              const calculateDaysOld = (discoveryDate) => {
                if (!discoveryDate) return 0;
                const created = new Date(discoveryDate);
                const now = new Date();
                const diffTime = Math.abs(now - created);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                return diffDays;
              };

              // Get aging color
              const getAgingColor = (days) => {
                if (days < 30) return 'bg-green-100 border-green-300 dark:bg-green-900/20 dark:border-green-700/50';
                if (days < 60) return 'bg-orange-100 border-orange-300 dark:bg-orange-900/20 dark:border-orange-700/50';
                return 'bg-red-100 border-red-300 dark:bg-red-900/20 dark:border-red-700/50';
              };

              // Get aging badge
              const getAgingBadge = (days) => {
                if (days < 30) return { text: 'Fresh', color: 'bg-green-500' };
                if (days < 60) return { text: 'Aging', color: 'bg-orange-500' };
                return { text: 'Stale', color: 'bg-red-500' };
              };

              // Get unique AEs for filter dropdown
              const uniqueAEsTracking = Array.from(new Set(
                analytics.meeting_generation.meetings_details
                  .map(m => m.owner)
                  .filter(Boolean)
              )).sort();

              // Filter deals for Inbox (F Inbox) and Intro Attended (E Intro Attended) with AE filter
              const inboxDeals = analytics.meeting_generation.meetings_details
                .filter(meeting => meeting.stage === 'F Inbox')
                .filter(meeting => selectedAE === 'all' || meeting.owner === selectedAE)
                .map(meeting => ({
                  id: meeting.client || Math.random().toString(),
                  client: meeting.client,
                  pipeline: meeting.expected_arr || 0,
                  stage: meeting.stage,
                  ae: meeting.owner || 'Unassigned',
                  intro_date: meeting.discovery_date,
                  days_old: calculateDaysOld(meeting.discovery_date)
                }))
                .sort((a, b) => b.pipeline - a.pipeline);

              const introAttendedDeals = analytics.meeting_generation.meetings_details
                .filter(meeting => meeting.stage === 'E Intro attended')
                .filter(meeting => selectedAE === 'all' || meeting.owner === selectedAE)
                .map(meeting => ({
                  id: meeting.client || Math.random().toString(),
                  client: meeting.client,
                  pipeline: meeting.expected_arr || 0,
                  stage: meeting.stage,
                  ae: meeting.owner || 'Unassigned',
                  intro_date: meeting.discovery_date,
                  intro_attended_date: meeting.intro_attended_date || meeting.discovery_date,
                  days_old: calculateDaysOld(meeting.discovery_date)
                }))
                .sort((a, b) => b.pipeline - a.pipeline);

              const formatDate = (dateStr) => {
                if (!dateStr) return 'N/A';
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
              };

              return (
                <Card className="mb-6 dark:bg-[#1e2128] dark:border-[#2a2d35]">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="dark:text-white">Deal Pipeline Board — Tracking</CardTitle>
                        <CardDescription className="dark:text-slate-400">
                          Track deal progression from Inbox to Intro Attended. 🟢 Fresh &lt;30d • 🟠 Aging 30-60d • 🔴 Stale &gt;60d
                        </CardDescription>
                      </div>
                      {/* AE Filter Dropdown */}
                      <select
                        value={selectedAE}
                        onChange={(e) => setSelectedAE(e.target.value)}
                        className="px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-[#1e2128] dark:text-white rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All AEs</option>
                        {uniqueAEsTracking.map(ae => (
                          <option key={ae} value={ae}>{ae}</option>
                        ))}
                      </select>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Inbox Column */}
                      <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-700/50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-bold text-lg text-blue-900 dark:text-blue-300">Inbox</h3>
                          <span className="text-sm bg-blue-200 dark:bg-blue-800 text-blue-900 dark:text-blue-200 px-3 py-1 rounded-full font-semibold">
                            {inboxDeals.length} deals • ${(inboxDeals.reduce((sum, d) => sum + d.pipeline, 0) / 1000).toFixed(0)}K
                          </span>
                        </div>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto">
                          {inboxDeals.map(deal => {
                            const agingBadge = getAgingBadge(deal.days_old);
                            return (
                              <div
                                key={deal.id}
                                className={`${getAgingColor(deal.days_old)} border-2 rounded-lg p-3 hover:shadow-md transition-shadow`}
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="font-semibold text-gray-900 dark:text-white text-sm flex-1 mr-2">
                                    {deal.client}
                                  </div>
                                  <span className={`${agingBadge.color} text-white text-xs px-2 py-1 rounded-full`}>
                                    {agingBadge.text}
                                  </span>
                                </div>
                                <div className="text-2xl font-bold text-blue-700 dark:text-blue-400 mb-2">
                                  ${(deal.pipeline / 1000).toFixed(0)}K
                                </div>
                                <div className="text-xs text-gray-700 dark:text-slate-300 space-y-1">
                                  <div className="flex justify-between">
                                    <span className="font-medium">📅 Created:</span>
                                    <span className="font-semibold">{formatDate(deal.intro_date)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="font-medium">👤 AE:</span>
                                    <span className="font-semibold">{deal.ae}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="font-medium">⏱️ Age:</span>
                                    <span className="font-semibold">{deal.days_old} days</span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Intro Attended Column */}
                      <div className="bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-700/50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-bold text-lg text-purple-900 dark:text-purple-300">Intro Attended</h3>
                          <span className="text-sm bg-purple-200 dark:bg-purple-800 text-purple-900 dark:text-purple-200 px-3 py-1 rounded-full font-semibold">
                            {introAttendedDeals.length} deals • ${(introAttendedDeals.reduce((sum, d) => sum + d.pipeline, 0) / 1000).toFixed(0)}K
                          </span>
                        </div>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto">
                          {introAttendedDeals.map(deal => {
                            const agingBadge = getAgingBadge(deal.days_old);
                            return (
                              <div
                                key={deal.id}
                                className={`${getAgingColor(deal.days_old)} border-2 rounded-lg p-3 hover:shadow-md transition-shadow`}
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="font-semibold text-gray-900 dark:text-white text-sm flex-1 mr-2">
                                    {deal.client}
                                  </div>
                                  <span className={`${agingBadge.color} text-white text-xs px-2 py-1 rounded-full`}>
                                    {agingBadge.text}
                                  </span>
                                </div>
                                <div className="text-2xl font-bold text-purple-700 dark:text-purple-400 mb-2">
                                  ${(deal.pipeline / 1000).toFixed(0)}K
                                </div>
                                <div className="text-xs text-gray-700 dark:text-slate-300 space-y-1">
                                  <div className="flex justify-between">
                                    <span className="font-medium">📅 Created:</span>
                                    <span className="font-semibold">{formatDate(deal.intro_date)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="font-medium">✅ Intro Date:</span>
                                    <span className="font-semibold text-purple-700 dark:text-purple-400">{formatDate(deal.intro_attended_date)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="font-medium">👤 AE:</span>
                                    <span className="font-semibold">{deal.ae}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="font-medium">⏱️ Age:</span>
                                    <span className="font-semibold">{deal.days_old} days</span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Meetings Details Table */}
            {analytics.meeting_generation.meetings_details && analytics.meeting_generation.meetings_details.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Meeting Details</CardTitle>
                  <CardDescription>Detailed list of all meetings with filters and sorting</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <Label htmlFor="filter-bdr" className="text-xs font-semibold">Filter by BDR</Label>
                      <select
                        id="filter-bdr"
                        className="w-full mt-1 p-2 border rounded text-sm"
                        value={meetingDetailsFilters.bdr}
                        onChange={(e) => setMeetingDetailsFilters({...meetingDetailsFilters, bdr: e.target.value})}
                      >
                        <option value="all">All BDRs</option>
                        {Array.from(new Set(analytics.meeting_generation.meetings_details.map(m => m.bdr).filter(Boolean))).map(bdr => (
                          <option key={bdr} value={bdr}>{bdr}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="filter-source" className="text-xs font-semibold">Filter by Source</Label>
                      <select
                        id="filter-source"
                        className="w-full mt-1 p-2 border rounded text-sm"
                        value={meetingDetailsFilters.source}
                        onChange={(e) => setMeetingDetailsFilters({...meetingDetailsFilters, source: e.target.value})}
                      >
                        <option value="all">All Sources</option>
                        <option value="Inbound">Inbound</option>
                        <option value="Outbound">Outbound</option>
                        <option value="referral">Referral</option>
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="filter-relevance" className="text-xs font-semibold">Filter by Relevance</Label>
                      <select
                        id="filter-relevance"
                        className="w-full mt-1 p-2 border rounded text-sm"
                        value={meetingDetailsFilters.relevance}
                        onChange={(e) => setMeetingDetailsFilters({...meetingDetailsFilters, relevance: e.target.value})}
                      >
                        <option value="all">All Relevance</option>
                        <option value="Relevant">Relevant</option>
                        <option value="Question mark">Question mark</option>
                        <option value="Maybe">Maybe</option>
                        <option value="Not relevant">Not relevant</option>
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="filter-stage" className="text-xs font-semibold">Filter by Stage</Label>
                      <select
                        id="filter-stage"
                        className="w-full mt-1 p-2 border rounded text-sm"
                        value={meetingDetailsFilters.stage}
                        onChange={(e) => setMeetingDetailsFilters({...meetingDetailsFilters, stage: e.target.value})}
                      >
                        <option value="all">All Stages</option>
                        {Array.from(new Set(analytics.meeting_generation.meetings_details.map(m => m.stage).filter(Boolean))).map(stage => (
                          <option key={stage} value={stage}>{stage}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <SortableTableHeader sortKey="date" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Date
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="client" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Client / Prospect
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="bdr" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Owner (BDR)
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="source" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Source
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="relevance" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-center p-2 font-semibold">
                            Relevance
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="owner" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Owner (AE)
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="stage" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-left p-2 font-semibold">
                            Stage
                          </SortableTableHeader>
                          <SortableTableHeader sortKey="expected_arr" requestSort={requestMeetingDetailsSort} sortConfig={meetingDetailsSortConfig} className="text-right p-2 font-semibold">
                            Expected ARR
                          </SortableTableHeader>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedMeetingDetails
                          .filter(meeting => {
                            // Apply filters
                            if (meetingDetailsFilters.bdr !== 'all' && meeting.bdr !== meetingDetailsFilters.bdr) return false;
                            if (meetingDetailsFilters.source !== 'all') {
                              if (meetingDetailsFilters.source === 'referral' && !meeting.source?.toLowerCase().includes('referral')) return false;
                              if (meetingDetailsFilters.source !== 'referral' && meeting.source !== meetingDetailsFilters.source) return false;
                            }
                            if (meetingDetailsFilters.relevance !== 'all' && meeting.relevance !== meetingDetailsFilters.relevance) return false;
                            if (meetingDetailsFilters.stage !== 'all' && meeting.stage !== meetingDetailsFilters.stage) return false;
                            return true;
                          })
                          .map((meeting, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-2">{meeting.date}</td>
                            <td className="p-2 font-medium">{meeting.client}</td>
                            <td className="p-2">{meeting.bdr}</td>
                            <td className="p-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                meeting.source === 'Inbound' ? 'bg-blue-100 text-blue-800' :
                                meeting.source === 'Outbound' ? 'bg-green-100 text-green-800' :
                                meeting.source?.toLowerCase().includes('referral') ? 'bg-purple-100 text-purple-800' :
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
                            <td className="p-2 text-right font-medium text-green-600">
                              ${(meeting.expected_arr || 0).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Results count */}
                  <div className="mt-4 text-sm text-gray-600">
                    Showing {sortedMeetingDetails.filter(meeting => {
                      if (meetingDetailsFilters.bdr !== 'all' && meeting.bdr !== meetingDetailsFilters.bdr) return false;
                      if (meetingDetailsFilters.source !== 'all') {
                        if (meetingDetailsFilters.source === 'referral' && !meeting.source?.toLowerCase().includes('referral')) return false;
                        if (meetingDetailsFilters.source !== 'referral' && meeting.source !== meetingDetailsFilters.source) return false;
                      }
                      if (meetingDetailsFilters.relevance !== 'all' && meeting.relevance !== meetingDetailsFilters.relevance) return false;
                      if (meetingDetailsFilters.stage !== 'all' && meeting.stage !== meetingDetailsFilters.stage) return false;
                      return true;
                    }).length} of {sortedMeetingDetails.length} meetings
                  </div>
                </CardContent>
              </Card>
            )}

            {/* BDR Performance */}
            {Object.keys(analytics.meeting_generation.bdr_performance).length > 0 && (() => {
              // Get unique AEs from bdr_performance
              const uniqueAEs = Object.keys(analytics.meeting_generation.bdr_performance);
              
              // Filter BDR performance data based on selectedAE
              const filteredBDRPerformance = selectedAE === 'all' 
                ? analytics.meeting_generation.bdr_performance 
                : (analytics.meeting_generation.bdr_performance[selectedAE] 
                    ? { [selectedAE]: analytics.meeting_generation.bdr_performance[selectedAE] }
                    : {});
              
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
              
              return (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>BDR Performance</CardTitle>
                      {/* AE Filter Dropdown */}
                      <select
                        value={selectedAE}
                        onChange={(e) => setSelectedAE(e.target.value)}
                        className="px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-[#1e2128] dark:text-white rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All AEs</option>
                        {uniqueAEs.map(ae => (
                          <option key={ae} value={ae}>{ae}</option>
                        ))}
                      </select>
                    </div>
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
                          {Object.entries(filteredBDRPerformance).map(([bdr, stats]) => {
                            // Determine if this is Fady (Referrals Manager)
                            const isFady = bdr.toLowerCase().includes('fady');
                            
                            // Determine monthly target based on role and person
                            let monthlyGoal = 0;
                            let goalText = '-';
                            let isOnTrack = false;
                            let displayRole = stats.role || 'N/A';
                            
                            if (isFady) {
                              monthlyGoal = 4; // Fady (Referrals Manager): 4 per month
                              displayRole = 'Referrals Manager';
                            } else if (stats.role === 'BDR') {
                              monthlyGoal = 6; // BDR: 6 per month
                            } else if (stats.role === 'AE') {
                              monthlyGoal = 1; // AE (Rémi, Sadie, Guillaume, François): 1 per month
                            } else if (stats.role === 'Partner') {
                              monthlyGoal = 1; // Partner: 1 per month
                            }
                            
                            // Calculate period target (monthly × months)
                            if (monthlyGoal > 0) {
                              const periodGoal = monthlyGoal * periodMonths;
                              goalText = `${stats.total_meetings}/${periodGoal}`;
                              isOnTrack = stats.total_meetings >= periodGoal;
                            }
                            
                            return (
                              <tr key={bdr} className="border-b">
                                <td className="p-2 font-medium">{bdr}</td>
                                <td className="text-center p-2">
                                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                    stats.role === 'BDR' ? 'bg-blue-100 text-blue-800' : 
                                    stats.role === 'AE' ? 'bg-purple-100 text-purple-800' : 
                                    stats.role === 'Partner' ? 'bg-green-100 text-green-800' :
                                    isFady ? 'bg-orange-100 text-orange-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}>
                                    {displayRole}
                                  </span>
                                </td>
                                <td className="text-right p-2">{stats.total_meetings}</td>
                                <td className="text-right p-2">{stats.relevant_meetings}</td>
                                <td className={`text-right p-2 font-medium ${
                                  monthlyGoal > 0 ? (isOnTrack ? 'text-green-600' : 'text-orange-600') : 'text-gray-500'
                                }`}>
                                  {goalText}
                                </td>
                                <td className="text-right p-2">
                                  {stats.total_meetings > 0 ? ((stats.relevant_meetings / stats.total_meetings) * 100).toFixed(1) : '0.0'}%
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}
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

              // Use tab targets from Back Office (MONTHLY) and multiply by period duration
              const dynamicMeetingsScheduledTarget = tabTargets.meetings_attended_tab.meetings_scheduled_target * periodMonths;
              const dynamicPOAGeneratedTarget = tabTargets.meetings_attended_tab.poa_generated_target * periodMonths;
              const dynamicDealsClosedTarget = tabTargets.meetings_attended_tab.deals_closed_target * periodMonths;

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
                      Monthly targets from Back Office × Period duration
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

                  {/* Monthly Meetings Attended Evolution Chart - Positioned BEFORE AE Performance Breakdown */}
                  {analytics.meetings_attended.monthly_breakdown && analytics.meetings_attended.monthly_breakdown.months && analytics.meetings_attended.monthly_breakdown.months.length > 0 && (() => {
                    const chartData = analytics.meetings_attended.monthly_breakdown.months.map((month, index) => ({
                      month,
                      attended: analytics.meetings_attended.monthly_breakdown.attended[index],
                      poa_generated: analytics.meetings_attended.monthly_breakdown.poa_generated[index],
                      deals_closed: analytics.meetings_attended.monthly_breakdown.deals_closed[index]
                    }));
                    
                    // Function to toggle visibility of chart series
                    const handleLegendClick = (dataKey) => {
                      setAttendedChartVisibility(prev => ({
                        ...prev,
                        [dataKey]: !prev[dataKey]
                      }));
                    };
                    
                    // Custom legend data
                    const legendData = [
                      { key: 'attended', color: '#3b82f6', label: 'Meetings Attended' },
                      { key: 'poa_generated', color: '#10b981', label: 'POA Generated' },
                      { key: 'deals_closed', color: '#ef4444', label: 'Deals Closed' }
                    ];
                    
                    return (
                      <Card className="mb-6">
                        <CardHeader>
                          <CardTitle>Monthly Meetings Attended Evolution</CardTitle>
                          <CardDescription>
                            Track attended meetings, POA generated, and deals closed on a monthly basis (click legend to toggle)
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={350}>
                            <ComposedChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="month" />
                              <YAxis />
                              <Tooltip />
                              {attendedChartVisibility.attended && (
                                <Bar dataKey="attended" fill="#3b82f6" name="Meetings Attended" />
                              )}
                              {attendedChartVisibility.poa_generated && (
                                <Bar dataKey="poa_generated" fill="#10b981" name="POA Generated" />
                              )}
                              {attendedChartVisibility.deals_closed && (
                                <Line type="monotone" dataKey="deals_closed" stroke="#ef4444" strokeWidth={3} name="Deals Closed" />
                              )}
                            </ComposedChart>
                          </ResponsiveContainer>
                          
                          {/* Custom Legend with Checkboxes */}
                          <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
                            {legendData.map(({ key, color, label }) => (
                              <button
                                key={key}
                                onClick={() => handleLegendClick(key)}
                                className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                                  attendedChartVisibility[key] 
                                    ? 'bg-white shadow-sm border border-gray-200' 
                                    : 'bg-gray-100 opacity-60 hover:opacity-80'
                                }`}
                              >
                                <div 
                                  className="w-3 h-3 rounded-sm"
                                  style={{ backgroundColor: color }}
                                />
                                <span className={`text-sm ${attendedChartVisibility[key] ? 'text-gray-700 font-medium' : 'text-gray-500'}`}>
                                  {label}
                                </span>
                              </button>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })()}

                  {/* Deal Pipeline Board - POA → Proposal → Legals (3 columns) */}
                  {analytics.meeting_generation?.meetings_details && analytics.meeting_generation.meetings_details.length > 0 && (() => {
                    // Calculate days since creation
                    const calculateDaysOld = (discoveryDate) => {
                      if (!discoveryDate) return 0;
                      const created = new Date(discoveryDate);
                      const now = new Date();
                      const diffTime = Math.abs(now - created);
                      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                      return diffDays;
                    };

                    // Get aging color
                    const getAgingColor = (days) => {
                      if (days < 30) return 'bg-green-100 border-green-300 dark:bg-green-900/20 dark:border-green-700/50';
                      if (days < 60) return 'bg-orange-100 border-orange-300 dark:bg-orange-900/20 dark:border-orange-700/50';
                      return 'bg-red-100 border-red-300 dark:bg-red-900/20 dark:border-red-700/50';
                    };

                    // Get aging badge
                    const getAgingBadge = (days) => {
                      if (days < 30) return { text: 'Fresh', color: 'bg-green-500' };
                      if (days < 60) return { text: 'Aging', color: 'bg-orange-500' };
                      return { text: 'Stale', color: 'bg-red-500' };
                    };

                    // Get unique AEs for filter dropdown
                    const uniqueAEsAdvanced = Array.from(new Set(
                      analytics.meeting_generation.meetings_details
                        .map(m => m.owner)
                        .filter(Boolean)
                    )).sort();

                    // Filter deals for each stage with AE filter
                    const poaBookedDeals = analytics.meeting_generation.meetings_details
                      .filter(meeting => meeting.stage === 'D POA Booked')
                      .filter(meeting => selectedAE === 'all' || meeting.owner === selectedAE)
                      .map(meeting => ({
                        id: meeting.client || Math.random().toString(),
                        client: meeting.client,
                        pipeline: meeting.expected_arr || 0,
                        stage: meeting.stage,
                        ae: meeting.owner || 'Unassigned',
                        created_date: meeting.discovery_date,
                        stage_date: meeting.poa_date,
                        days_old: calculateDaysOld(meeting.discovery_date)
                      }))
                      .sort((a, b) => b.pipeline - a.pipeline);

                    const proposalSentDeals = analytics.meeting_generation.meetings_details
                      .filter(meeting => meeting.stage === 'C Proposal sent')
                      .filter(meeting => selectedAE === 'all' || meeting.owner === selectedAE)
                      .map(meeting => ({
                        id: meeting.client || Math.random().toString(),
                        client: meeting.client,
                        pipeline: meeting.expected_arr || 0,
                        stage: meeting.stage,
                        ae: meeting.owner || 'Unassigned',
                        created_date: meeting.discovery_date,
                        stage_date: meeting.poa_date,
                        days_old: calculateDaysOld(meeting.discovery_date)
                      }))
                      .sort((a, b) => b.pipeline - a.pipeline);

                    const formatDate = (dateStr) => {
                      if (!dateStr) return 'N/A';
                      const date = new Date(dateStr);
                      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    };

                    return (
                      <Card className="mb-6 dark:bg-[#1e2128] dark:border-[#2a2d35]">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div>
                              <CardTitle className="dark:text-white">Deal Pipeline Board — Advanced Stages</CardTitle>
                              <CardDescription className="dark:text-slate-400">
                                Track deal progression from POA Booked → Proposal Sent. 🟢 Fresh &lt;30d • 🟠 Aging 30-60d • 🔴 Stale &gt;60d
                              </CardDescription>
                            </div>
                            {/* AE Filter Dropdown */}
                            <select
                              value={selectedAE}
                              onChange={(e) => setSelectedAE(e.target.value)}
                              className="px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-[#1e2128] dark:text-white rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="all">All AEs</option>
                              {uniqueAEsAdvanced.map(ae => (
                                <option key={ae} value={ae}>{ae}</option>
                              ))}
                            </select>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* POA Booked Column */}
                            <div className="bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-700/50 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-lg text-purple-900 dark:text-purple-300">POA Booked</h3>
                                <span className="text-sm bg-purple-200 dark:bg-purple-800 text-purple-900 dark:text-purple-200 px-3 py-1 rounded-full font-semibold">
                                  {poaBookedDeals.length} • ${(poaBookedDeals.reduce((sum, d) => sum + d.pipeline, 0) / 1000).toFixed(0)}K
                                </span>
                              </div>
                              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                                {poaBookedDeals.map(deal => {
                                  const agingBadge = getAgingBadge(deal.days_old);
                                  return (
                                    <div
                                      key={deal.id}
                                      className={`${getAgingColor(deal.days_old)} border-2 rounded-lg p-3 hover:shadow-md transition-shadow`}
                                    >
                                      <div className="flex items-start justify-between mb-2">
                                        <div className="font-semibold text-gray-900 dark:text-white text-sm flex-1 mr-2">
                                          {deal.client}
                                        </div>
                                        <span className={`${agingBadge.color} text-white text-xs px-2 py-1 rounded-full`}>
                                          {agingBadge.text}
                                        </span>
                                      </div>
                                      <div className="text-xl font-bold text-purple-700 dark:text-purple-400 mb-2">
                                        ${(deal.pipeline / 1000).toFixed(0)}K
                                      </div>
                                      <div className="text-xs text-gray-700 dark:text-slate-300 space-y-1">
                                        <div className="flex justify-between">
                                          <span className="font-medium">📅 POA:</span>
                                          <span className="font-semibold">
                                            {deal.stage_date ? formatDate(deal.stage_date) : 'Not Booked Yet'}
                                          </span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="font-medium">🔍 Discovery:</span>
                                          <span className="font-semibold">{formatDate(deal.created_date)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="font-medium">👤 AE:</span>
                                          <span className="font-semibold">{deal.ae}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="font-medium">⏱️ Age:</span>
                                          <span className="font-semibold">{deal.days_old}d</span>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                            {/* Proposal Sent Column */}
                            <div className="bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-200 dark:border-indigo-700/50 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-lg text-indigo-900 dark:text-indigo-300">Proposal Sent</h3>
                                <span className="text-sm bg-indigo-200 dark:bg-indigo-800 text-indigo-900 dark:text-indigo-200 px-3 py-1 rounded-full font-semibold">
                                  {proposalSentDeals.length} • ${(proposalSentDeals.reduce((sum, d) => sum + d.pipeline, 0) / 1000).toFixed(0)}K
                                </span>
                              </div>
                              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                                {proposalSentDeals.map(deal => {
                                  const agingBadge = getAgingBadge(deal.days_old);
                                  return (
                                    <div
                                      key={deal.id}
                                      className={`${getAgingColor(deal.days_old)} border-2 rounded-lg p-3 hover:shadow-md transition-shadow`}
                                    >
                                      <div className="flex items-start justify-between mb-2">
                                        <div className="font-semibold text-gray-900 dark:text-white text-sm flex-1 mr-2">
                                          {deal.client}
                                        </div>
                                        <span className={`${agingBadge.color} text-white text-xs px-2 py-1 rounded-full`}>
                                          {agingBadge.text}
                                        </span>
                                      </div>
                                      <div className="text-xl font-bold text-indigo-700 dark:text-indigo-400 mb-2">
                                        ${(deal.pipeline / 1000).toFixed(0)}K
                                      </div>
                                      <div className="text-xs text-gray-700 dark:text-slate-300 space-y-1">
                                        <div className="flex justify-between">
                                          <span className="font-medium">📄 Proposal:</span>
                                          <span className="font-semibold">
                                            {deal.stage_date ? formatDate(deal.stage_date) : 'Not Sent Yet'}
                                          </span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="font-medium">👤 AE:</span>
                                          <span className="font-semibold">{deal.ae}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="font-medium">⏱️ Age:</span>
                                          <span className="font-semibold">{deal.days_old}d</span>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })()}
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

            {/* AE Performance Blocks - All AEs sorted by Closing Value (descending) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
              {analytics.ae_performance.ae_performance
                .sort((a, b) => b.valeur_closing - a.valeur_closing) // Sort by closing value descending
                .map((ae, index) => (
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

                // Calculate dynamic targets (monthly target × period)
                const dealsTarget = tabTargets.deals_closed_tab.deals_closed_target * periodMonths;
                const arrTarget = tabTargets.deals_closed_tab.arr_closed_target * periodMonths;

                return (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <MetricCard
                        title="Deals Closed"
                        value={analytics.deals_closed.deals_closed}
                        target={dealsTarget}
                        icon={CheckCircle2}
                        color="green"
                      />
                      <MetricCard
                        title="ARR Closed"
                        value={analytics.deals_closed.arr_closed}
                        target={arrTarget}
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
                  </>
                );
              })()}
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
              {/* Pipeline Overview - 4 blocks matching Dashboard logic */}
              {(() => {
                // BLOCKS 1 & 2: Use EXACT same logic and data as Dashboard
                // Dynamic targets - multiply by number of months in the period
                const baseNewPipeMonthlyTarget = 2000000; // $2M per month
                const baseWeightedPipeMonthlyTarget = 800000; // $800K per month
                
                // Get backend target which is already multiplied by period months
                const backendPipeTarget = analytics.dashboard_blocks?.block_3_pipe_creation?.target_pipe_created || baseNewPipeMonthlyTarget;
                
                // Calculate number of months from backend target (target / 2M base)
                const periodMonths = backendPipeTarget / baseNewPipeMonthlyTarget;
                
                // Calculate dynamic targets based on period (same as dashboard)
                const dynamicNewPipeTarget = backendPipeTarget; // Use backend's dynamic target
                const dynamicWeightedPipeTarget = baseWeightedPipeMonthlyTarget * periodMonths; // 800K × months
                
                // Use SAME data source as Dashboard
                const newPipeCreated = analytics.dashboard_blocks?.block_3_pipe_creation?.new_pipe_created || 0;
                const weightedPipe = analytics.dashboard_blocks?.block_3_pipe_creation?.weighted_pipe_created || 0;
                
                // YTD targets - get from backend view_targets, with fallback to defaults
                const fixedYTDPipelineTarget = analytics.view_targets?.dashboard?.ytd_aggregate_pipeline || 7500000; // Default: $7.5M
                const fixedYTDWeightedTarget = analytics.view_targets?.dashboard?.ytd_cumulative_weighted || 2500000; // Default: $2.5M
                
                return (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    {/* Block 1: New Pipe Created - SAME AS DASHBOARD */}
                    <MetricCard
                      title="New Pipe Created"
                      value={newPipeCreated}
                      target={dynamicNewPipeTarget}
                      unit="$"
                      icon={TrendingUp}
                      color="purple"
                      tooltip="Sum of ARR from all deals created this period. Target adjusts with period duration. (Same as Dashboard)"
                    />
                    
                    {/* Block 2: Created Weighted Pipe - SAME AS DASHBOARD */}
                    <MetricCard
                      title="Created Weighted Pipe"
                      value={weightedPipe}
                      target={dynamicWeightedPipeTarget}
                      unit="$"
                      icon={Target}
                      color="blue"
                      tooltip="Weighted ARR for deals created this period. Target adjusts with period duration. (Same as Dashboard)"
                    />
                    
                    {/* Block 3: YTD Aggregate Pipeline - Fixed Target 7.5M */}
                    <MetricCard
                      title="YTD Aggregate Pipeline"
                      value={analytics.pipe_metrics.total_pipe.value}
                      target={fixedYTDPipelineTarget}
                      unit="$"
                      icon={BarChart3}
                      color="green"
                      tooltip="YTD cumulative pipeline excluding Closed, Lost, and Not Relevant. Fixed target: $7.5M."
                    />
                    
                    {/* Block 4: YTD Cumulative Weighted Pipe - Fixed Target 2.5M */}
                    <MetricCard
                      title="YTD Cumulative Weighted"
                      value={analytics.pipe_metrics.total_pipe.weighted_value}
                      target={fixedYTDWeightedTarget}
                      unit="$"
                      icon={DollarSign}
                      color="orange"
                      tooltip="YTD cumulative weighted pipe excluding Wins, Lost, and Not Relevant. Fixed target: $2.5M."
                    />
                  </div>
                );
              })()}
              
              {/* Pipeline Logic Explanation */}
              <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="font-semibold text-blue-800 mb-2">📋 Pipeline Logic Summary</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
                  <div>
                    <span className="font-medium">Blocks 1 & 2 (Period-Based):</span> New Pipe Created and Created Weighted Pipe for selected period. Targets multiply by period duration (Monthly: 2M/800K, July-Dec: 12M/4.8M).
                  </div>
                  <div>
                    <span className="font-medium">Blocks 3 & 4 (YTD Cumulative):</span> YTD Aggregate Pipeline (excl. Closed/Lost/Not Relevant) and YTD Weighted Pipe (excl. Wins/Lost/Not Relevant). Fixed targets: 7.5M and 2.5M.
                  </div>
                  <div>
                    <span className="font-medium">Weighted Value:</span> Uses Excel formula with stage × source × recency factors
                  </div>
                  <div>
                    <span className="font-medium">Target Logic:</span> Blocks 1-2 dynamic (scale with period), Blocks 3-4 fixed (never change)
                  </div>
                </div>
              </div>

              {/* Monthly Pipeline Evolution Chart - ABOVE AE Breakdown Table */}
              {analytics.pipe_metrics.monthly_breakdown && analytics.pipe_metrics.monthly_breakdown.months && analytics.pipe_metrics.monthly_breakdown.months.length > 0 && (() => {
                // Filter data to start from July
                const allChartData = analytics.pipe_metrics.monthly_breakdown.months.map((month, index) => ({
                  month,
                  sortKey: month, // For sorting
                  new_pipe_created: analytics.pipe_metrics.monthly_breakdown.new_pipe_created[index],
                  new_weighted_pipe: analytics.pipe_metrics.monthly_breakdown.new_weighted_pipe[index],
                  total_pipe: analytics.pipe_metrics.monthly_breakdown.total_pipe[index],
                  total_weighted: analytics.pipe_metrics.monthly_breakdown.total_weighted[index]
                }));
                
                // Find July index and filter data from July onwards
                const julyIndex = allChartData.findIndex(item => 
                  item.month.toLowerCase().includes('jul')
                );
                
                const chartData = julyIndex >= 0 
                  ? allChartData.slice(julyIndex) 
                  : allChartData;
                
                const handleLegendClick = (dataKey) => {
                  setPipelineEvolutionVisibility(prev => ({
                    ...prev,
                    [dataKey]: !prev[dataKey]
                  }));
                };
                
                // Custom legend data
                const legendData = [
                  { key: 'new_pipe_created', color: '#8b5cf6', label: 'New Pipe Created' },
                  { key: 'new_weighted_pipe', color: '#3b82f6', label: 'New Weighted Pipe' },
                  { key: 'total_pipe', color: '#10b981', label: 'Total Pipeline' },
                  { key: 'total_weighted', color: '#f97316', label: 'Total Weighted' }
                ];
                
                return (
                  <Card className="mb-6">
                    <CardHeader>
                      <CardTitle>Monthly Pipeline Evolution</CardTitle>
                      <CardDescription>
                        Track new pipeline created and total pipeline value on a monthly basis (click legend to toggle)
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={350}>
                        <ComposedChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                          {pipelineEvolutionVisibility.new_pipe_created && <Bar dataKey="new_pipe_created" fill="#8b5cf6" name="New Pipe Created" />}
                          {pipelineEvolutionVisibility.new_weighted_pipe && <Bar dataKey="new_weighted_pipe" fill="#3b82f6" name="New Weighted Pipe" />}
                          {pipelineEvolutionVisibility.total_pipe !== false && <Line type="monotone" dataKey="total_pipe" stroke="#10b981" strokeWidth={3} name="Total Pipeline" />}
                          {pipelineEvolutionVisibility.total_weighted !== false && <Line type="monotone" dataKey="total_weighted" stroke="#f97316" strokeWidth={2} strokeDasharray="5 5" name="Total Weighted" />}
                        </ComposedChart>
                      </ResponsiveContainer>
                      
                      {/* Custom Legend with Checkboxes */}
                      <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
                        {legendData.map(({ key, color, label }) => (
                          <button
                            key={key}
                            onClick={() => handleLegendClick(key)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                              pipelineEvolutionVisibility[key] !== false
                                ? 'bg-white shadow-sm border border-gray-200' 
                                : 'bg-gray-100 opacity-60 hover:opacity-80'
                            }`}
                          >
                            <div 
                              className="w-3 h-3 rounded-sm"
                              style={{ backgroundColor: color }}
                            />
                            <span className={`text-sm ${pipelineEvolutionVisibility[key] !== false ? 'text-gray-700 font-medium' : 'text-gray-500'}`}>
                              {label}
                            </span>
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })()}

              {/* AE Breakdown Table */}
              {analytics.pipe_metrics.ae_breakdown && analytics.pipe_metrics.ae_breakdown.length > 0 && (() => {
                // Function to sort AE breakdown
                const sortAEBreakdown = (key) => {
                  let direction = 'asc';
                  if (aeSortConfig.key === key && aeSortConfig.direction === 'asc') {
                    direction = 'desc';
                  }
                  setAESortConfig({ key, direction });
                };

                // Sort the data based on current sort config
                const sortedAEBreakdown = [...analytics.pipe_metrics.ae_breakdown].sort((a, b) => {
                  if (!aeSortConfig.key) return 0;

                  let aValue, bValue;
                  switch (aeSortConfig.key) {
                    case 'ae':
                      aValue = a.ae || '';
                      bValue = b.ae || '';
                      break;
                    case 'new_pipe_created':
                      aValue = a.new_pipe_created || 0;
                      bValue = b.new_pipe_created || 0;
                      break;
                    case 'new_weighted_pipe':
                      aValue = a.new_weighted_pipe || 0;
                      bValue = b.new_weighted_pipe || 0;
                      break;
                    case 'total_pipe':
                      aValue = a.total_pipe || 0;
                      bValue = b.total_pipe || 0;
                      break;
                    case 'weighted_pipe':
                      aValue = a.weighted_pipe || 0;
                      bValue = b.weighted_pipe || 0;
                      break;
                    default:
                      return 0;
                  }

                  if (aValue < bValue) return aeSortConfig.direction === 'asc' ? -1 : 1;
                  if (aValue > bValue) return aeSortConfig.direction === 'asc' ? 1 : -1;
                  return 0;
                });

                return (
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
                            <th 
                              className="text-left p-3 font-semibold cursor-pointer hover:bg-gray-100"
                              onClick={() => sortAEBreakdown('ae')}
                            >
                              <div className="flex items-center gap-1">
                                AE
                                {aeSortConfig.key === 'ae' && (
                                  <span>{aeSortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                )}
                              </div>
                            </th>
                            <th 
                              className="text-right p-3 font-semibold cursor-pointer hover:bg-gray-100"
                              onClick={() => sortAEBreakdown('new_pipe_created')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                New Pipe Created
                                {aeSortConfig.key === 'new_pipe_created' && (
                                  <span>{aeSortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                )}
                              </div>
                            </th>
                            <th 
                              className="text-right p-3 font-semibold cursor-pointer hover:bg-gray-100"
                              onClick={() => sortAEBreakdown('new_weighted_pipe')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Created Weighted Pipe
                                {aeSortConfig.key === 'new_weighted_pipe' && (
                                  <span>{aeSortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                )}
                              </div>
                            </th>
                            <th 
                              className="text-right p-3 font-semibold cursor-pointer hover:bg-gray-100"
                              onClick={() => sortAEBreakdown('total_pipe')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Total Pipe
                                {aeSortConfig.key === 'total_pipe' && (
                                  <span>{aeSortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                )}
                              </div>
                            </th>
                            <th 
                              className="text-right p-3 font-semibold cursor-pointer hover:bg-gray-100"
                              onClick={() => sortAEBreakdown('weighted_pipe')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Total Weighted Pipe
                                {aeSortConfig.key === 'weighted_pipe' && (
                                  <span>{aeSortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                )}
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedAEBreakdown.map((ae, index) => (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="p-3 font-medium">{ae.ae}</td>
                              {/* Block 1: New Pipe Created */}
                              <td className="text-right p-3 font-semibold text-purple-600">
                                ${ae.new_pipe_created.toLocaleString()}
                              </td>
                              {/* Block 2: Created Weighted Pipe */}
                              <td className="text-right p-3 font-semibold text-blue-600">
                                ${(ae.new_weighted_pipe || 0).toLocaleString()}
                              </td>
                              {/* Block 3: Total Pipe (excl. Closed/Lost/Not Relevant) */}
                              <td className="text-right p-3 font-semibold text-green-600">
                                ${ae.total_pipe.toLocaleString()}
                              </td>
                              {/* Block 4: Total Weighted Pipe (excl. Wins/Lost/Not Relevant) */}
                              <td className="text-right p-3 font-semibold text-orange-600">
                                ${ae.weighted_pipe.toLocaleString()}
                              </td>
                            </tr>
                          ))}
                          {/* Total Row */}
                          <tr className="border-t-2 font-bold bg-gray-50">
                            <td className="p-3">Total</td>
                            {/* Block 1: New Pipe Created Total */}
                            <td className="text-right p-3 text-purple-600">
                              ${analytics.pipe_metrics.created_pipe.value.toLocaleString()}
                            </td>
                            {/* Block 2: Created Weighted Pipe Total */}
                            <td className="text-right p-3 text-blue-600">
                              ${analytics.pipe_metrics.created_pipe.weighted_value.toLocaleString()}
                            </td>
                            {/* Block 3: Total Pipe Total */}
                            <td className="text-right p-3 text-green-600">
                              ${analytics.pipe_metrics.total_pipe.value.toLocaleString()}
                            </td>
                            {/* Block 4: Total Weighted Pipe Total */}
                            <td className="text-right p-3 text-orange-600">
                              ${analytics.pipe_metrics.total_pipe.weighted_value.toLocaleString()}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
                );
              })()}

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
                {/* 3 Large Metric Cards with Fixed Targets */}
                {(() => {
                  // Fixed monthly targets for Upsell & Cross-sell
                  const monthlyIntroTarget = 11; // 11 intros per month
                  const monthlyPOATarget = 8; // 8 POA per month
                  const monthlyClosingTarget = 4; // 4 closing per month
                  const avgDealValue = 60000; // 60K average deal value
                  const monthlyClosingValueTarget = monthlyClosingTarget * avgDealValue; // 4 × 60K = 240K
                  
                  // Calculate period multiplier
                  const periodMonths = upsellRenewData.period_duration_months || 1;
                  
                  // Dynamic targets based on period
                  const periodIntroTarget = monthlyIntroTarget * periodMonths;
                  const periodPOATarget = monthlyPOATarget * periodMonths;
                  const periodClosingTarget = monthlyClosingTarget * periodMonths;
                  const periodClosingValueTarget = monthlyClosingValueTarget * periodMonths;
                  
                  return (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <MetricCard
                        title="Total Intro Meetings"
                        value={upsellRenewData.total_meetings}
                        target={periodIntroTarget}
                        icon={Users}
                        color="blue"
                      />
                      <MetricCard
                        title="POA Generated"
                        value={upsellRenewData.poa_actual}
                        target={periodPOATarget}
                        icon={Target}
                        color="orange"
                      />
                      <MetricCard
                        title="Closing Upsells"
                        value={upsellRenewData.closing_actual}
                        target={periodClosingTarget}
                        icon={CheckCircle}
                        color="green"
                      />
                    </div>
                  );
                })()}

                {/* 2 Summary Cards - Upsells and Renewals only */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
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
                </div>

                {/* Partner Performance Table - All partners who generated Upsell/Cross-sell at any stage */}
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Partner Performance</span>
                      <Badge variant="destructive">Needs Improvement</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      // Get all deals with Upsell/Cross-sell type
                      const introsDetails = upsellRenewData?.intros_details || [];
                      const poaDetails = upsellRenewData?.poa_details || [];
                      
                      // Aggregate data by partner from both intros and POA details
                      const partnerStats = {};
                      
                      [...introsDetails, ...poaDetails].forEach(deal => {
                        // Only count Upsell/Cross-sell deals
                        if ((deal.type_of_deal === 'Upsell' || deal.type_of_deal === 'Cross-sell') && deal.partner) {
                          const partnerName = deal.partner;
                          
                          if (!partnerStats[partnerName]) {
                            partnerStats[partnerName] = {
                              partner: partnerName,
                              deals: [],
                              total_arr: 0,
                              deal_count: 0
                            };
                          }
                          
                          partnerStats[partnerName].deals.push(deal);
                          partnerStats[partnerName].total_arr += deal.expected_arr || 0;
                          partnerStats[partnerName].deal_count += 1;
                        }
                      });
                      
                      // Convert to array and sort by total ARR descending
                      const partnerList = Object.values(partnerStats).sort((a, b) => b.total_arr - a.total_arr);
                      const hasData = partnerList.length > 0;
                      
                      return hasData ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b bg-gray-50">
                                <th className="text-left p-2 font-semibold">PARTNER</th>
                                <th className="text-right p-2 font-semibold">DEALS COUNT</th>
                                <th className="text-right p-2 font-semibold">TOTAL ARR</th>
                                <th className="text-center p-2 font-semibold">STAGES</th>
                              </tr>
                            </thead>
                            <tbody>
                              {partnerList.map((partnerData) => {
                                // Get unique stages for this partner
                                const stages = [...new Set(partnerData.deals.map(d => d.stage))];
                                const stagesSummary = stages.length > 3 
                                  ? `${stages.slice(0, 3).join(', ')}...` 
                                  : stages.join(', ');
                                
                                return (
                                  <tr key={partnerData.partner} className="border-b hover:bg-gray-50">
                                    <td className="p-2 font-medium">{partnerData.partner}</td>
                                    <td className="text-right p-2">{partnerData.deal_count}</td>
                                    <td className="text-right p-2 font-semibold text-green-600">
                                      ${(partnerData.total_arr / 1000).toFixed(0)}K
                                    </td>
                                    <td className="text-center p-2">
                                      <span className="text-xs text-gray-600">
                                        {stagesSummary || 'N/A'}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No partner data available for this period
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>

                {/* Monthly Upsell/Renew Evolution Chart - Moved AFTER Partner Performance */}
                {upsellRenewData && upsellRenewData.monthly_breakdown && upsellRenewData.monthly_breakdown.months && upsellRenewData.monthly_breakdown.months.length > 0 && (() => {
                  const chartData = upsellRenewData.monthly_breakdown.months.map((month, index) => ({
                    month,
                    intro_meetings: upsellRenewData.monthly_breakdown.meetings_attended[index],
                    poa_attended: upsellRenewData.monthly_breakdown.poa_generated[index],
                    deals_closed: upsellRenewData.monthly_breakdown.revenue_generated[index]
                  }));
                  
                  const handleLegendClick = (dataKey) => {
                    setUpsellEvolutionVisibility(prev => ({
                      ...prev,
                      [dataKey]: !prev[dataKey]
                    }));
                  };
                  
                  // Custom legend data
                  const legendData = [
                    { key: 'intro_meetings', color: '#6366f1', label: 'Intro Meetings' },
                    { key: 'poa_attended', color: '#10b981', label: 'POA Attended' },
                    { key: 'deals_closed', color: '#ef4444', label: 'Deals Closed' }
                  ];
                  
                  return (
                    <Card className="mb-6">
                      <CardHeader>
                        <CardTitle>Monthly Upsell & Renew Evolution</CardTitle>
                        <CardDescription>
                          Track upsell/renew meetings, POA generated, and revenue on a monthly basis (click legend to toggle)
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={350}>
                          <ComposedChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip 
                              formatter={(value, name) => {
                                if (name === 'Deals Closed') {
                                  return [`$${value.toLocaleString()}`, name];
                                }
                                return [value, name];
                              }}
                            />
                            {upsellEvolutionVisibility.intro_meetings && <Bar yAxisId="left" dataKey="intro_meetings" fill="#6366f1" name="Intro Meetings" />}
                            {upsellEvolutionVisibility.poa_attended && <Bar yAxisId="left" dataKey="poa_attended" fill="#10b981" name="POA Attended" />}
                            {upsellEvolutionVisibility.deals_closed && <Line yAxisId="right" type="monotone" dataKey="deals_closed" stroke="#ef4444" strokeWidth={3} name="Deals Closed" />}
                          </ComposedChart>
                        </ResponsiveContainer>
                        
                        {/* Custom Legend with Checkboxes */}
                        <div className="flex flex-wrap justify-center gap-4 mt-4 px-4">
                          {legendData.map(({ key, color, label }) => (
                            <button
                              key={key}
                              onClick={() => handleLegendClick(key)}
                              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                                upsellEvolutionVisibility[key] 
                                  ? 'bg-white shadow-sm border border-gray-200' 
                                  : 'bg-gray-100 opacity-60 hover:opacity-80'
                              }`}
                            >
                              <div 
                                className="w-3 h-3 rounded-sm"
                                style={{ backgroundColor: color }}
                              />
                              <span className={`text-sm ${upsellEvolutionVisibility[key] ? 'text-gray-700 font-medium' : 'text-gray-500'}`}>
                                {label}
                              </span>
                            </button>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })()}

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
            <Card className="dark:bg-[#1e2128] dark:border-[#2a2d35]">
              <CardHeader>
                <CardTitle className="dark:text-white">Closing Projections</CardTitle>
                <CardDescription className="dark:text-slate-400">Pipeline metrics with advanced weighting methodology</CardDescription>
                
                {/* Pipeline Metrics Explanation */}
                <div className="mt-3 p-3 bg-gray-50 dark:bg-[#252729] rounded-lg text-xs border dark:border-[#2a2d35]">
                  <div className="font-semibold mb-2 dark:text-white">📊 Pipeline Metrics Explained:</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                    <div className="dark:text-slate-300">
                      <span className="font-medium text-purple-700 dark:text-purple-400">• Total Pipeline:</span>
                      <br />Valeur brute (sauf Lost/Not Relevant)
                    </div>
                    <div className="dark:text-slate-300">
                      <span className="font-medium text-blue-700 dark:text-blue-400">• Weighted Value:</span>
                      <br />Pondéré par stage/source/temps
                    </div>
                    <div className="dark:text-slate-300">
                      <span className="font-medium text-green-700 dark:text-green-400">• Aggregate Pipe:</span>
                      <br />Cumul historique pondéré
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  {/* Card 1: Legals Count - Filtered by selected AE */}
                  <Card className="border-2 border-purple-200 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-700/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2 dark:text-white">
                        <FileText className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                        Legals
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const filteredDeals = getFilteredDeals();
                        const legalsDeals = filteredDeals.filter(deal => deal.stage === 'B Legals');
                        return (
                          <>
                            <div className="text-2xl font-bold mb-2 text-gray-800 dark:text-white">
                              {legalsDeals.length}
                            </div>
                            <div className="text-xs text-gray-600 dark:text-slate-400 mb-2">
                              Deals in Legals
                            </div>
                            <div className="text-lg font-semibold text-purple-700 dark:text-purple-400">
                              ${legalsDeals
                                .reduce((sum, deal) => sum + (deal.expected_arr || deal.pipeline || 0), 0)
                                .toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-slate-500">
                              Pipeline Value
                            </div>
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* Card 2: Proposal Sent Count - Filtered by selected AE */}
                  <Card className="border-2 border-indigo-200 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-700/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Target className="h-4 w-4 text-indigo-600" />
                        Proposal Sent
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const filteredDeals = getFilteredDeals();
                        const proposalDeals = filteredDeals.filter(deal => deal.stage === 'C Proposal sent');
                        return (
                          <>
                            <div className="text-2xl font-bold mb-2 text-gray-800">
                              {proposalDeals.length}
                            </div>
                            <div className="text-xs text-gray-600 mb-2">
                              Deals in Proposal
                            </div>
                            <div className="text-lg font-semibold text-indigo-700">
                              ${proposalDeals
                                .reduce((sum, deal) => sum + (deal.expected_arr || deal.value || deal.pipeline || 0), 0)
                                .toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              Pipeline Value
                            </div>
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* Card 3: Combined Value - Filtered by selected AE */}
                  <Card className="border-2 border-green-200 bg-green-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        Legals + Proposal Value
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const filteredDeals = getFilteredDeals();
                        // Sum RAW deal values (expected_arr field - no weighting/probability)
                        const legalsValue = filteredDeals
                          .filter(deal => deal.stage === 'B Legals')
                          .reduce((sum, deal) => sum + (deal.expected_arr || deal.pipeline || 0), 0);
                        
                        const proposalValue = filteredDeals
                          .filter(deal => deal.stage === 'C Proposal sent')
                          .reduce((sum, deal) => sum + (deal.expected_arr || deal.pipeline || 0), 0);
                        
                        return (
                          <>
                            <div className="text-xl font-bold mb-2 text-gray-800">
                              ${(legalsValue + proposalValue).toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-600">
                              Combined Pipeline Value
                            </div>
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* Card 4: Upcoming POAs - Filtered by selected AE */}
                  <Card className="border-2 border-blue-200 bg-blue-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-blue-600" />
                        Upcoming POAs
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        // Get filtered deals with future poa_date
                        const filteredDeals = getFilteredDeals();
                        const today = new Date();
                        const upcomingPOAs = filteredDeals.filter(deal => {
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
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <Target className="h-6 w-6 text-green-600" />
                      Closing Projections — Interactive Board
                      {hasUnsavedChanges && (
                        <Badge className="ml-2 bg-orange-100 text-orange-800">
                          Unsaved Changes
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription>
                      Drag & drop deals to simulate closing timelines. Changes are visual only and don't affect source data.
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                    {/* AE Filter Dropdown */}
                    <select
                      value={selectedAE}
                      onChange={(e) => setSelectedAE(e.target.value)}
                      className="px-2 sm:px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-[#1e2128] dark:text-white rounded-md text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All AEs</option>
                      {getUniqueAEs().map(ae => (
                        <option key={ae} value={ae}>{ae}</option>
                      ))}
                    </select>
                    
                    {/* Asher POV Button - Show for everyone */}
                    <button
                      onClick={applyAsherPOV}
                      className="px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors bg-purple-600 text-white hover:bg-purple-700 flex items-center gap-1 sm:gap-2"
                      title="Load Asher's saved board organization"
                    >
                      <span>👁️</span>
                      <span className="hidden sm:inline">Asher POV</span>
                    </button>
                    
                    {/* Reset Buttons */}
                    {isAsher ? (
                      <>
                        {/* Asher's Reset Button */}
                        <button
                          onClick={handleResetBoard}
                          disabled={!hasSavedPreferences && !hasUnsavedChanges}
                          className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            (hasSavedPreferences || hasUnsavedChanges)
                              ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
                              : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                          }`}
                          title="Reset your personal preferences"
                        >
                          Reset
                        </button>
                        {/* Asher's Reset POV Button */}
                        <button
                          onClick={handleResetAsAsherPOV}
                          disabled={!hasSavedPreferences && !hasUnsavedChanges}
                          className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            (hasSavedPreferences || hasUnsavedChanges)
                              ? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800'
                              : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                          }`}
                          title="Reset Asher POV that others see"
                        >
                          <span className="hidden sm:inline">Reset as Asher POV</span>
                          <span className="sm:hidden">Reset POV</span>
                        </button>
                      </>
                    ) : (
                      /* Normal Reset Button for non-Asher users */
                      <button
                        onClick={handleResetBoard}
                        disabled={!hasSavedPreferences && !hasUnsavedChanges}
                        className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                          (hasSavedPreferences || hasUnsavedChanges)
                            ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
                            : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                        }`}
                      >
                        Reset
                      </button>
                    )}
                    
                    {/* Save Buttons */}
                    {isAsher ? (
                      <>
                        {/* Asher's Normal Save Button */}
                        <button
                          onClick={handleSaveBoard}
                          disabled={!hasUnsavedChanges}
                          className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            hasUnsavedChanges
                              ? 'bg-blue-600 text-white hover:bg-blue-700'
                              : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                          }`}
                          title="Save your personal preferences"
                        >
                          Save
                        </button>
                        {/* Asher's Save as POV Button */}
                        <button
                          onClick={handleSaveAsAsherPOV}
                          disabled={!hasUnsavedChanges}
                          className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                            hasUnsavedChanges
                              ? 'bg-purple-600 text-white hover:bg-purple-700'
                              : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                          }`}
                          title="Save as Asher POV that others can load"
                        >
                          <span className="hidden md:inline">Save as Asher POV</span>
                          <span className="md:hidden">Save POV</span>
                        </button>
                      </>
                    ) : (
                      /* Normal Save Button for non-Asher users */
                      <button
                        onClick={handleSaveBoard}
                        disabled={!hasUnsavedChanges}
                        className={`px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                          hasUnsavedChanges
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                        }`}
                      >
                        Save
                      </button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <DragDropContext onDragEnd={onDragEnd}>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
                    {/* Next 30 Days Column */}
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-green-800 text-center mb-2">
                          Next 30 Days
                        </div>
                        {(() => {
                          // Format number with K (thousands) or M (millions)
                          const formatValue = (value) => {
                            if (value >= 1000000) {
                              return `$${(value / 1000000).toFixed(1)}M`;
                            } else if (value >= 1000) {
                              return `$${(value / 1000).toFixed(0)}K`;
                            }
                            return `$${value.toFixed(0)}`;
                          };
                          
                          // Calculate sum excluding hidden deals (with AE filter)
                          const filteredDeals = getFilteredDeals();
                          const columnDeals = filteredDeals.filter(deal => deal.column === 'next14' && !hiddenDeals.has(deal.id));
                          const columnValue = columnDeals.reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const weightedValue = columnDeals.reduce((sum, deal) => {
                            const prob = dealProbabilities[deal.id] || 75;
                            return sum + ((deal.pipeline || 0) * prob / 100);
                          }, 0);
                          const dealCount = columnDeals.length;
                          const columnTarget = viewConfig?.targets?.closing_projections?.next_30_days_target || 250000;
                          const percentage = Math.round((weightedValue / columnTarget) * 100);
                          const isOnTrack = weightedValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-sm font-semibold text-gray-700 text-center mb-1">
                                  Total ARR
                                </div>
                                <div className="text-2xl font-bold text-green-800 text-center">
                                  {formatValue(columnValue)}
                                </div>
                                <div className="text-sm font-semibold text-blue-700 text-center mt-2 mb-1">
                                  Projected (Weighted)
                                </div>
                                <div className="text-xl font-bold text-blue-600 text-center">
                                  {formatValue(weightedValue)}
                                </div>
                                <div className="text-xs text-gray-500 text-center mt-2 mb-1">
                                  {dealCount} deal{dealCount !== 1 ? 's' : ''}
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: {formatValue(columnTarget)}
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
                            className="space-y-2 min-h-[600px] max-h-[600px] overflow-y-auto"
                          >
                            {getFilteredDeals()
                              .filter(deal => deal.column === 'next14')
                              .sort((a, b) => (b.pipeline || 0) - (a.pipeline || 0)) // Sort by pipeline descending
                              .map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={{...deal, probability: dealProbabilities[deal.id] || 75}} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                                onDelete={handleDeleteDeal}
                                onProbabilityChange={handleDealProbabilityChange}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>

                    {/* Next 60 Days Column */}
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-yellow-800 text-center mb-2">
                          Next 60 Days
                        </div>
                        {(() => {
                          // Format number with K (thousands) or M (millions)
                          const formatValue = (value) => {
                            if (value >= 1000000) {
                              return `$${(value / 1000000).toFixed(1)}M`;
                            } else if (value >= 1000) {
                              return `$${(value / 1000).toFixed(0)}K`;
                            }
                            return `$${value.toFixed(0)}`;
                          };
                          
                          // Calculate sum excluding hidden deals (with AE filter)
                          const filteredDeals = getFilteredDeals();
                          const columnDeals = filteredDeals.filter(deal => deal.column === 'next30' && !hiddenDeals.has(deal.id));
                          const columnValue = columnDeals.reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const weightedValue = columnDeals.reduce((sum, deal) => {
                            const prob = dealProbabilities[deal.id] || 75;
                            return sum + ((deal.pipeline || 0) * prob / 100);
                          }, 0);
                          const dealCount = columnDeals.length;
                          const columnTarget = viewConfig?.targets?.closing_projections?.next_60_days_target || 500000;
                          const percentage = Math.round((weightedValue / columnTarget) * 100);
                          const isOnTrack = weightedValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-sm font-semibold text-gray-700 text-center mb-1">
                                  Total ARR
                                </div>
                                <div className="text-2xl font-bold text-yellow-800 text-center">
                                  {formatValue(columnValue)}
                                </div>
                                <div className="text-sm font-semibold text-blue-700 text-center mt-2 mb-1">
                                  Projected (Weighted)
                                </div>
                                <div className="text-xl font-bold text-blue-600 text-center">
                                  {formatValue(weightedValue)}
                                </div>
                                <div className="text-xs text-gray-500 text-center mt-2 mb-1">
                                  {dealCount} deal{dealCount !== 1 ? 's' : ''}
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: {formatValue(columnTarget)}
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
                            className="space-y-2 min-h-[600px] max-h-[600px] overflow-y-auto"
                          >
                            {getFilteredDeals()
                              .filter(deal => deal.column === 'next30')
                              .sort((a, b) => (b.pipeline || 0) - (a.pipeline || 0)) // Sort by pipeline descending
                              .map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={{...deal, probability: dealProbabilities[deal.id] || 75}} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                                onDelete={handleDeleteDeal}
                                onProbabilityChange={handleDealProbabilityChange}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>

                    {/* Next 90 Days Column */}
                    <div className="bg-orange-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-orange-800 text-center mb-2">
                          Next 90 Days
                        </div>
                        {(() => {
                          // Format number with K (thousands) or M (millions)
                          const formatValue = (value) => {
                            if (value >= 1000000) {
                              return `$${(value / 1000000).toFixed(1)}M`;
                            } else if (value >= 1000) {
                              return `$${(value / 1000).toFixed(0)}K`;
                            }
                            return `$${value.toFixed(0)}`;
                          };
                          
                          // Calculate sum excluding hidden deals (with AE filter)
                          const filteredDeals = getFilteredDeals();
                          const columnDeals = filteredDeals.filter(deal => deal.column === 'next60' && !hiddenDeals.has(deal.id));
                          const columnValue = columnDeals.reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const weightedValue = columnDeals.reduce((sum, deal) => {
                            const prob = dealProbabilities[deal.id] || 75;
                            return sum + ((deal.pipeline || 0) * prob / 100);
                          }, 0);
                          const dealCount = columnDeals.length;
                          const columnTarget = viewConfig?.targets?.closing_projections?.next_90_days_target || 750000;
                          const percentage = Math.round((weightedValue / columnTarget) * 100);
                          const isOnTrack = weightedValue >= columnTarget;
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-sm font-semibold text-gray-700 text-center mb-1">
                                  Total ARR
                                </div>
                                <div className="text-2xl font-bold text-orange-800 text-center">
                                  {formatValue(columnValue)}
                                </div>
                                <div className="text-sm font-semibold text-blue-700 text-center mt-2 mb-1">
                                  Projected (Weighted)
                                </div>
                                <div className="text-xl font-bold text-blue-600 text-center">
                                  {formatValue(weightedValue)}
                                </div>
                                <div className="text-xs text-gray-500 text-center mt-2 mb-1">
                                  {dealCount} deal{dealCount !== 1 ? 's' : ''}
                                </div>
                                <div className="text-xs text-gray-600 text-center mb-2">
                                  Target: {formatValue(columnTarget)}
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
                            className="space-y-2 min-h-[600px] max-h-[600px] overflow-y-auto"
                          >
                            {getFilteredDeals()
                              .filter(deal => deal.column === 'next60')
                              .sort((a, b) => (b.pipeline || 0) - (a.pipeline || 0)) // Sort by pipeline descending
                              .map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={{...deal, probability: dealProbabilities[deal.id] || 75}} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                                onDelete={handleDeleteDeal}
                                onProbabilityChange={handleDealProbabilityChange}
                              />
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                    
                    {/* Potentially Delayed Deals Column */}
                    <div className="bg-red-50 rounded-lg p-4">
                      <div className="mb-4">
                        <div className="font-semibold text-red-800 text-center mb-2">
                          Potentially Delayed Deals
                        </div>
                        {(() => {
                          // Format number with K (thousands) or M (millions)
                          const formatValue = (value) => {
                            if (value >= 1000000) {
                              return `$${(value / 1000000).toFixed(1)}M`;
                            } else if (value >= 1000) {
                              return `$${(value / 1000).toFixed(0)}K`;
                            }
                            return `$${value.toFixed(0)}`;
                          };
                          
                          // Calculate sum excluding hidden deals (with AE filter)
                          const filteredDeals = getFilteredDeals();
                          const columnDeals = filteredDeals.filter(deal => deal.column === 'delayed' && !hiddenDeals.has(deal.id));
                          const columnValue = columnDeals.reduce((sum, deal) => sum + (deal.pipeline || 0), 0);
                          const weightedValue = columnDeals.reduce((sum, deal) => {
                            const prob = dealProbabilities[deal.id] || 75;
                            return sum + ((deal.pipeline || 0) * prob / 100);
                          }, 0);
                          
                          return (
                            <Card className="bg-white">
                              <CardContent className="p-3">
                                <div className="text-sm font-semibold text-gray-700 text-center mb-1">
                                  Total ARR
                                </div>
                                <div className="text-2xl font-bold text-red-800 text-center">
                                  {formatValue(columnValue)}
                                </div>
                                <div className="text-sm font-semibold text-blue-700 text-center mt-2 mb-1">
                                  Projected (Weighted)
                                </div>
                                <div className="text-xl font-bold text-blue-600 text-center">
                                  {formatValue(weightedValue)}
                                </div>
                                <div className="text-xs text-gray-600 text-center mt-2 mb-2">
                                  Deals at risk of delay
                                </div>
                                <div className="text-xs text-center mt-1">
                                  <span className="text-red-600 font-medium">
                                    {columnDeals.length} deal(s)
                                  </span>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })()}
                      </div>
                      <Droppable droppableId="delayed">
                        {(provided) => (
                          <div 
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            className="space-y-2 min-h-[600px] max-h-[600px] overflow-y-auto border-2 border-dashed border-red-300 rounded-lg bg-red-50/30 p-2"
                          >
                            {getFilteredDeals()
                              .filter(deal => deal.column === 'delayed')
                              .sort((a, b) => (b.pipeline || 0) - (a.pipeline || 0)) // Sort by pipeline descending
                              .map((deal, index) => (
                              <DraggableDealItem 
                                key={deal.id}
                                deal={{...deal, probability: dealProbabilities[deal.id] || 75}} 
                                index={index}
                                showActions={true}
                                onHide={() => hideItem('deals', deal.id)}
                                onDelete={handleDeleteDeal}
                                onProbabilityChange={handleDealProbabilityChange}
                              />
                            ))}
                            {getFilteredDeals().filter(deal => deal.column === 'delayed').length === 0 && (
                              <div className="text-center text-gray-400 text-sm mt-8">
                                <p className="font-medium">No delayed deals</p>
                                <p className="text-xs mt-1">Drag deals here if potentially delayed</p>
                              </div>
                            )}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  </div>
                </DragDropContext>
              </CardContent>
            </Card>

            {/* Projection by 30/60/90 days - Pipeline by AE per period */}
            {Object.keys(analytics.closing_projections.ae_projections).length > 0 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Projections breakdown</CardTitle>
                  <p className="text-sm text-gray-600">Pipeline values for each AE across different time periods</p>
                </CardHeader>
                <CardContent>
                  {(() => {
                    // Calculate pipeline by AE for each time period from hotDeals
                    const aeBreakdown = {};
                    
                    // Initialize AE breakdown
                    Object.keys(analytics.closing_projections.ae_projections).forEach(ae => {
                      aeBreakdown[ae] = {
                        next14: 0,
                        next30: 0,
                        next60: 0
                      };
                    });
                    
                    // Sum pipeline by AE and period (excluding hidden deals)
                    hotDeals.forEach(deal => {
                      if (!hiddenDeals.has(deal.id) && deal.owner && aeBreakdown[deal.owner]) {
                        if (deal.column === 'next14') {
                          aeBreakdown[deal.owner].next14 += deal.pipeline || 0;
                        } else if (deal.column === 'next30') {
                          aeBreakdown[deal.owner].next30 += deal.pipeline || 0;
                        } else if (deal.column === 'next60') {
                          aeBreakdown[deal.owner].next60 += deal.pipeline || 0;
                        }
                      }
                    });
                    
                    // Calculate totals
                    const totals = {
                      next14: Object.values(aeBreakdown).reduce((sum, ae) => sum + ae.next14, 0),
                      next30: Object.values(aeBreakdown).reduce((sum, ae) => sum + ae.next30, 0),
                      next60: Object.values(aeBreakdown).reduce((sum, ae) => sum + ae.next60, 0)
                    };
                    
                    // Format value with K/M
                    const formatValue = (value) => {
                      if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                      if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
                      return `$${value.toFixed(0)}`;
                    };
                    
                    // Handle sorting for AE Pipeline table
                    const requestAePipelineSort = (key) => {
                      let direction = 'ascending';
                      if (aePipelineSortConfig.key === key && aePipelineSortConfig.direction === 'ascending') {
                        direction = 'descending';
                      }
                      setAePipelineSortConfig({ key, direction });
                    };
                    
                    // Sort AE breakdown
                    const sortedAeBreakdown = Object.entries(aeBreakdown).sort(([aeA, valuesA], [aeB, valuesB]) => {
                      if (aePipelineSortConfig.key === 'ae') {
                        // Alphabetical sort
                        return aePipelineSortConfig.direction === 'ascending' 
                          ? aeA.localeCompare(aeB)
                          : aeB.localeCompare(aeA);
                      } else if (aePipelineSortConfig.key === 'next14') {
                        return aePipelineSortConfig.direction === 'ascending'
                          ? valuesA.next14 - valuesB.next14
                          : valuesB.next14 - valuesA.next14;
                      } else if (aePipelineSortConfig.key === 'next30') {
                        return aePipelineSortConfig.direction === 'ascending'
                          ? valuesA.next30 - valuesB.next30
                          : valuesB.next30 - valuesA.next30;
                      } else if (aePipelineSortConfig.key === 'next60') {
                        return aePipelineSortConfig.direction === 'ascending'
                          ? valuesA.next60 - valuesB.next60
                          : valuesB.next60 - valuesA.next60;
                      } else {
                        // Default: sort by total
                        const totalA = valuesA.next14 + valuesA.next30 + valuesA.next60;
                        const totalB = valuesB.next14 + valuesB.next30 + valuesB.next60;
                        return aePipelineSortConfig.direction === 'ascending'
                          ? totalA - totalB
                          : totalB - totalA;
                      }
                    });
                    
                    return (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b bg-gray-50">
                              <SortableTableHeader 
                                sortKey="ae" 
                                requestSort={requestAePipelineSort} 
                                sortConfig={aePipelineSortConfig} 
                                className="text-left p-3 font-semibold"
                              >
                                ACCOUNT EXECUTIVE
                              </SortableTableHeader>
                              <SortableTableHeader 
                                sortKey="next14" 
                                requestSort={requestAePipelineSort} 
                                sortConfig={aePipelineSortConfig} 
                                className="text-right p-3 font-semibold"
                              >
                                NEXT 30 DAYS<br /><span className="text-xs font-normal text-gray-600">Pipeline</span>
                              </SortableTableHeader>
                              <SortableTableHeader 
                                sortKey="next30" 
                                requestSort={requestAePipelineSort} 
                                sortConfig={aePipelineSortConfig} 
                                className="text-right p-3 font-semibold"
                              >
                                NEXT 60 DAYS<br /><span className="text-xs font-normal text-gray-600">Pipeline</span>
                              </SortableTableHeader>
                              <SortableTableHeader 
                                sortKey="next60" 
                                requestSort={requestAePipelineSort} 
                                sortConfig={aePipelineSortConfig} 
                                className="text-right p-3 font-semibold"
                              >
                                NEXT 90 DAYS<br /><span className="text-xs font-normal text-gray-600">Pipeline</span>
                              </SortableTableHeader>
                            </tr>
                          </thead>
                          <tbody>
                            {sortedAeBreakdown.map(([ae, values]) => (
                                <tr key={ae} className="border-b hover:bg-gray-50">
                                  <td className="p-3 font-medium">{ae}</td>
                                  <td className="text-right p-3">{formatValue(values.next14)}</td>
                                  <td className="text-right p-3">{formatValue(values.next30)}</td>
                                  <td className="text-right p-3">{formatValue(values.next60)}</td>
                                </tr>
                              ))
                            }
                            <tr className="border-t-2 bg-blue-50 font-bold">
                              <td className="p-3">TOTAL</td>
                              <td className="text-right p-3">{formatValue(totals.next14)}</td>
                              <td className="text-right p-3">{formatValue(totals.next30)}</td>
                              <td className="text-right p-3">{formatValue(totals.next60)}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    );
                  })()}
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
          <Route path="/admin/targets" element={<AdminTargetsPage />} />
          <Route path="/admin/users" element={<UserManagementPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;