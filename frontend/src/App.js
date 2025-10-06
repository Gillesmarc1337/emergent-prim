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
import { useDropzone } from 'react-dropzone';
import { Upload, Download, TrendingUp, TrendingDown, Users, Target, Calendar, DollarSign, BarChart3, PieChart, AlertCircle, CheckCircle2, Sheet, CalendarDays } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { DateRangePicker } from '@/components/DateRangePicker';
import { GoogleSheetsUpload } from '@/components/GoogleSheetsUpload';
import { format } from 'date-fns';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

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
        const response = await axios.post(`${API}/upload-data`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        setUploadStatus({ 
          type: 'success', 
          message: response.data.message,
          details: `${response.data.records_valid} enregistrements valides traités sur ${response.data.records_processed}` 
        });
        
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } catch (error) {
        setUploadStatus({ 
          type: 'error', 
          message: 'Erreur lors du téléchargement', 
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
          Import de Données
        </CardTitle>
        <CardDescription>
          Téléchargez votre fichier CSV avec les données de vente pour générer les analyses.
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
              ? 'Déposez le fichier ici...'
              : 'Glissez-déposez votre fichier CSV ici'}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            ou cliquez pour sélectionner un fichier (.csv, .xls, .xlsx)
          </p>
          <Button variant="outline" disabled={isUploading}>
            {isUploading ? 'Téléchargement...' : 'Sélectionner un fichier'}
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
                Objectif: {target.toLocaleString()} {unit}
              </div>
              <Progress value={percentage} className="h-2" />
              <div className="flex justify-between text-xs">
                <span className={isOnTrack ? 'text-green-600' : 'text-orange-600'}>
                  {percentage.toFixed(1)}% de l'objectif
                </span>
                <Badge variant={isOnTrack ? 'default' : 'secondary'}>
                  {isOnTrack ? 'Sur la bonne voie' : 'À surveiller'}
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
            {isOnTrack ? 'Sur la bonne voie' : 'À améliorer'}
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

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [dateRange, setDateRange] = useState(null);
  const [useCustomDate, setUseCustomDate] = useState(false);
  const [importMethod, setImportMethod] = useState('csv'); // 'csv' or 'sheets'

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
      } else {
        // Use weekly offset
        response = await axios.get(`${API}/analytics/weekly?week_offset=${weekOffset}`);
      }
      
      setAnalytics(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors du chargement des analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (analytics) {
      loadAnalytics();
    }
  }, [weekOffset, dateRange, useCustomDate]);

  const handleUploadSuccess = () => {
    loadAnalytics();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg font-medium">Chargement des analyses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <FileUpload onUploadSuccess={handleUploadSuccess} />
        <Alert className="border-red-500">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-medium">Erreur</div>
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
          <h1 className="text-3xl font-bold mb-2">Tableau de Bord Analytics Ventes</h1>
          <p className="text-gray-600">Analysez vos performances commerciales avec des rapports détaillés</p>
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

  const weekStart = new Date(analytics.week_start);
  const weekEnd = new Date(analytics.week_end);
  
  // Prepare chart data
  const sourceData = [
    { name: 'Inbound', value: analytics.meeting_generation.inbound },
    { name: 'Outbound', value: analytics.meeting_generation.outbound },
    { name: 'Referrals', value: analytics.meeting_generation.referrals }
  ];

  const relevanceData = [
    { name: 'Pertinent', value: analytics.meeting_generation.relevance_analysis.relevant, color: '#00C49F' },
    { name: 'À vérifier', value: analytics.meeting_generation.relevance_analysis.question_mark, color: '#FFBB28' },
    { name: 'Non pertinent', value: analytics.meeting_generation.relevance_analysis.not_relevant, color: '#FF8042' }
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">Rapport Hebdomadaire</h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setWeekOffset(weekOffset + 1)}
              >
                ← Semaine précédente
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setWeekOffset(weekOffset - 1)}
                disabled={weekOffset <= 0}
              >
                Semaine suivante →
              </Button>
            </div>
            <Button onClick={loadAnalytics} size="sm">
              Actualiser
            </Button>
          </div>
        </div>
        <p className="text-gray-600">
          Période: {weekStart.toLocaleDateString('fr-FR')} - {weekEnd.toLocaleDateString('fr-FR')}
        </p>
      </div>

      <Tabs defaultValue="meeting-generation" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="meeting-generation">Génération Meetings</TabsTrigger>
          <TabsTrigger value="meetings-attended">Meetings Réalisés</TabsTrigger>
          <TabsTrigger value="deals-pipeline">Deals & Pipeline</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
        </TabsList>

        {/* Meeting Generation */}
        <TabsContent value="meeting-generation">
          <AnalyticsSection 
            title="Génération de Meetings (7 derniers jours)"
            isOnTrack={analytics.meeting_generation.on_track}
            conclusion={analytics.meeting_generation.on_track 
              ? "Vous êtes sur la bonne voie pour atteindre vos objectifs de génération de meetings." 
              : "Il faut intensifier la prospection pour atteindre les objectifs."}
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <MetricCard
                title="Total Nouveaux Intros"
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
                  <CardTitle>Répartition par Source</CardTitle>
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
                  <CardTitle>Analyse de Pertinence</CardTitle>
                  <CardDescription>
                    Taux de pertinence: {analytics.meeting_generation.relevance_analysis.relevance_rate.toFixed(1)}%
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

            {/* BDR Performance */}
            {Object.keys(analytics.meeting_generation.bdr_performance).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Performance par BDR</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">BDR</th>
                          <th className="text-right p-2">Total Meetings</th>
                          <th className="text-right p-2">Meetings Pertinents</th>
                          <th className="text-right p-2">Taux de Pertinence</th>
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
        <TabsContent value="meetings-attended">
          <AnalyticsSection 
            title="Meetings Réalisés (7 derniers jours)"
            isOnTrack={analytics.meetings_attended.on_track}
            conclusion={analytics.meetings_attended.on_track 
              ? "Bonne performance sur les meetings réalisés et conversions." 
              : "Il faut améliorer le taux de présence et les conversions."}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <MetricCard
                title="Meetings Programmés"
                value={analytics.meetings_attended.intro_metrics.scheduled}
                target={analytics.meetings_attended.intro_metrics.target}
                icon={Calendar}
                color="blue"
              />
              <MetricCard
                title="Meetings Réalisés"
                value={analytics.meetings_attended.intro_metrics.attended}
                icon={CheckCircle2}
                color="green"
              />
              <MetricCard
                title="Taux de Présence"
                value={analytics.meetings_attended.intro_metrics.attendance_rate.toFixed(1)}
                unit="%"
                icon={BarChart3}
                color="orange"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <MetricCard
                title="Discoveries Réalisées"
                value={analytics.meetings_attended.discovery_metrics.completed}
                target={analytics.meetings_attended.discovery_metrics.target}
                icon={Target}
                color="purple"
              />
              <MetricCard
                title="POA Générées"
                value={analytics.meetings_attended.poa_metrics.generated}
                target={analytics.meetings_attended.poa_metrics.target}
                icon={DollarSign}
                color="green"
              />
            </div>

            {/* AE Performance */}
            {Object.keys(analytics.meetings_attended.ae_performance).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Performance par AE</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">AE</th>
                          <th className="text-right p-2">Programmés</th>
                          <th className="text-right p-2">Réalisés</th>
                          <th className="text-right p-2">POA Générées</th>
                          <th className="text-right p-2">Taux Conversion</th>
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
        <TabsContent value="deals-pipeline">
          <div className="space-y-6">
            {/* Deals Closed */}
            <AnalyticsSection 
              title="Deals Fermés (7 derniers jours)"
              isOnTrack={analytics.deals_closed.on_track}
              conclusion={analytics.deals_closed.on_track 
                ? "Excellente performance sur la fermeture de deals cette semaine." 
                : "Il faut accélérer la fermeture des deals en cours."}
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <MetricCard
                  title="Deals Fermés"
                  value={analytics.deals_closed.deals_closed}
                  target={analytics.deals_closed.target_deals}
                  icon={CheckCircle2}
                  color="green"
                />
                <MetricCard
                  title="ARR Fermé"
                  value={analytics.deals_closed.arr_closed}
                  target={analytics.deals_closed.target_arr}
                  unit="€"
                  icon={DollarSign}
                  color="green"
                />
                <MetricCard
                  title="MRR Fermé"
                  value={analytics.deals_closed.mrr_closed}
                  unit="€"
                  icon={TrendingUp}
                  color="blue"
                />
                <MetricCard
                  title="Taille Moyenne Deal"
                  value={analytics.deals_closed.avg_deal_size}
                  unit="€"
                  icon={BarChart3}
                  color="purple"
                />
              </div>

              {analytics.deals_closed.deals_detail.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Détail des Deals Fermés</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Client</th>
                            <th className="text-right p-2">ARR</th>
                            <th className="text-left p-2">Owner</th>
                            <th className="text-left p-2">Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.deals_closed.deals_detail.map((deal, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2 font-medium">{deal.client}</td>
                              <td className="text-right p-2">{deal.expected_arr?.toLocaleString()}€</td>
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
              title="Métriques du Pipeline"
              isOnTrack={analytics.pipe_metrics.total_aggregate_pipe.on_track}
              conclusion={analytics.pipe_metrics.total_aggregate_pipe.on_track 
                ? "Le pipeline total est en bonne santé et sur les objectifs." 
                : "Il faut renforcer la génération de pipeline pour atteindre les objectifs."}
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <MetricCard
                  title="Nouveau Pipeline Créé"
                  value={analytics.pipe_metrics.new_pipe_created.value}
                  target={analytics.pipe_metrics.new_pipe_created.target}
                  unit="€"
                  icon={TrendingUp}
                  color="green"
                />
                <MetricCard
                  title="Pipeline Chaud"
                  value={analytics.pipe_metrics.hot_pipe.value}
                  target={analytics.pipe_metrics.hot_pipe.target}
                  unit="€"
                  icon={DollarSign}
                  color="orange"
                />
                <MetricCard
                  title="Pipeline Total"
                  value={analytics.pipe_metrics.total_aggregate_pipe.value}
                  target={analytics.pipe_metrics.total_aggregate_pipe.target}
                  unit="€"
                  icon={BarChart3}
                  color="blue"
                />
              </div>

              {analytics.pipe_metrics.hot_pipe.deals.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Deals Chauds en Pipeline</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Client</th>
                            <th className="text-right p-2">Valeur</th>
                            <th className="text-left p-2">Stage</th>
                            <th className="text-left p-2">Owner</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analytics.pipe_metrics.hot_pipe.deals.map((deal, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2 font-medium">{deal.client}</td>
                              <td className="text-right p-2">{deal.pipeline?.toLocaleString()}€</td>
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
                <CardTitle>Pipeline Ancien (Réactivation)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <MetricCard
                    title="Deals en Attente"
                    value={analytics.old_pipe.total_stalled_deals}
                    icon={AlertCircle}
                    color="orange"
                  />
                  <MetricCard
                    title="Valeur Totale"
                    value={analytics.old_pipe.total_stalled_value}
                    unit="€"
                    icon={DollarSign}
                    color="red"
                  />
                  <MetricCard
                    title="Entreprises à Recontacter"
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
                <CardTitle>Projections de Fermeture</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">7 Prochains Jours</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        {analytics.closing_projections.next_7_days.total_value.toLocaleString()}€
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Valeur pondérée: {analytics.closing_projections.next_7_days.weighted_value.toLocaleString()}€
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.next_7_days.deals.length} deals potentiels
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Ce Mois</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        {analytics.closing_projections.current_month.total_value.toLocaleString()}€
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Valeur pondérée: {analytics.closing_projections.current_month.weighted_value.toLocaleString()}€
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.current_month.deals.length} deals potentiels
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Ce Trimestre</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold mb-2">
                        {analytics.closing_projections.next_quarter.total_value.toLocaleString()}€
                      </div>
                      <div className="text-sm text-gray-500 mb-2">
                        Valeur pondérée: {analytics.closing_projections.next_quarter.weighted_value.toLocaleString()}€
                      </div>
                      <div className="text-sm">
                        {analytics.closing_projections.next_quarter.deals.length} deals potentiels
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Projection par AE */}
                {Object.keys(analytics.closing_projections.ae_projections).length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Projections par AE</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">AE</th>
                              <th className="text-right p-2">Pipeline Total</th>
                              <th className="text-right p-2">Valeur Pondérée</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(analytics.closing_projections.ae_projections).map(([ae, stats]) => (
                              <tr key={ae} className="border-b">
                                <td className="p-2 font-medium">{ae}</td>
                                <td className="text-right p-2">{stats.pipeline?.toLocaleString()}€</td>
                                <td className="text-right p-2">{stats.weighted_value?.toLocaleString()}€</td>
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
                <CardTitle>Récapitulatif Général</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <MetricCard
                    title="Revenus YTD"
                    value={analytics.big_numbers_recap.ytd_revenue}
                    target={analytics.big_numbers_recap.ytd_target}
                    unit="€"
                    icon={DollarSign}
                    color="green"
                  />
                  <MetricCard
                    title="Objectif Restant"
                    value={analytics.big_numbers_recap.remaining_target}
                    unit="€"
                    icon={Target}
                    color="orange"
                  />
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="h-5 w-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-600">Statut Objectifs</span>
                      </div>
                      <Badge 
                        variant={analytics.big_numbers_recap.forecast_gap ? 'destructive' : 'default'}
                        className="text-sm"
                      >
                        {analytics.big_numbers_recap.forecast_gap 
                          ? 'Écart de prévision détecté' 
                          : 'Sur la bonne voie'}
                      </Badge>
                    </CardContent>
                  </Card>
                </div>

                {analytics.big_numbers_recap.forecast_gap && (
                  <Alert className="border-orange-500">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Action Requise:</strong> Il est nécessaire d'intensifier les efforts pour combler l'écart 
                      de {analytics.big_numbers_recap.remaining_target.toLocaleString()}€ et atteindre les objectifs annuels.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
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