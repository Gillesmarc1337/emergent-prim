import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings, Save, AlertCircle, CheckCircle2, Download, Info } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminTargetsPage() {
  const { user, views } = useAuth();
  const [selectedView, setSelectedView] = useState(null);
  const [targets, setTargets] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState(null);

  // Check if user is super_admin
  const isAdmin = user?.role === 'super_admin';

  useEffect(() => {
    if (views.length > 0 && !selectedView) {
      setSelectedView(views[0]);
    }
  }, [views, selectedView]);

  useEffect(() => {
    if (selectedView) {
      loadViewTargets(selectedView.id);
    }
  }, [selectedView]);

  const loadViewTargets = async (viewId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/views/${viewId}/config`, {
        withCredentials: true
      });
      
      // Initialize default structure if targets don't exist
      const defaultTargets = {
        revenue_2025: {
          jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0,
          jul: 120000, aug: 744000, sep: 1344000, oct: 528000, nov: 1068000, dec: 744000
        },
        dashboard_bottom_cards: {
          new_pipe_created: 2000000,
          created_weighted_pipe: 800000,
          ytd_revenue: 4500000
        },
        meeting_generation: {
          total_target: 50,
          inbound: 22,
          outbound: 17,
          referral: 11,
          upsells_cross: 5
        },
        intro_poa: {
          intro: 45,
          poa: 18
        }
      };

      setTargets(response.data.targets || defaultTargets);
    } catch (error) {
      console.error('Error loading targets:', error);
      setMessage({ type: 'error', text: 'Failed to load targets' });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromSheet = async () => {
    if (!selectedView) return;

    setSyncing(true);
    setMessage(null);

    try {
      const response = await axios.post(
        `${API}/admin/views/${selectedView.id}/sync-targets-from-sheet`,
        {},
        { withCredentials: true }
      );
      
      setMessage({ 
        type: 'info', 
        text: response.data.message || 'Sync initiated. Note: Full implementation coming soon.' 
      });
      
      // Reload targets after sync
      await loadViewTargets(selectedView.id);
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to sync from sheet' 
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleSave = async () => {
    if (!selectedView || !targets) return;

    setSaving(true);
    setMessage(null);

    try {
      await axios.put(
        `${API}/admin/views/${selectedView.id}/targets`,
        targets,
        { withCredentials: true }
      );
      
      setMessage({ type: 'success', text: 'Targets updated successfully!' });
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to update targets' 
      });
    } finally {
      setSaving(false);
    }
  };

  const updateRevenueTarget = (month, value) => {
    setTargets(prev => ({
      ...prev,
      revenue_2025: {
        ...prev.revenue_2025,
        [month]: parseFloat(value) || 0
      }
    }));
  };

  const updateMeetingTarget = (field, value) => {
    setTargets(prev => ({
      ...prev,
      meeting_generation: {
        ...prev.meeting_generation,
        [field]: parseFloat(value) || 0
      }
    }));
  };

  const updateIntroPOATarget = (field, value) => {
    setTargets(prev => ({
      ...prev,
      intro_poa: {
        ...prev.intro_poa,
        [field]: parseFloat(value) || 0
      }
    }));
  };

  const updateDashboardBottomCard = (field, value) => {
    setTargets(prev => ({
      ...prev,
      dashboard_bottom_cards: {
        ...prev.dashboard_bottom_cards,
        [field]: parseFloat(value) || 0
      }
    }));
  };

  if (!isAdmin) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Access denied. Only super administrators can access this page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading || !targets) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading targets...</div>
        </div>
      </div>
    );
  }

  const months2025 = [
    { key: 'jan', label: 'January' },
    { key: 'feb', label: 'February' },
    { key: 'mar', label: 'March' },
    { key: 'apr', label: 'April' },
    { key: 'may', label: 'May' },
    { key: 'jun', label: 'June' },
    { key: 'jul', label: 'July' },
    { key: 'aug', label: 'August' },
    { key: 'sep', label: 'September' },
    { key: 'oct', label: 'October' },
    { key: 'nov', label: 'November' },
    { key: 'dec', label: 'December' }
  ];

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Admin - Targets Configuration</h1>
        </div>
        <p className="text-gray-600">
          Configure revenue targets (2025) and meeting banners. Other KPIs are calculated from Google Sheet data.
        </p>
      </div>

      {/* Important Info */}
      <Alert className="mb-4 bg-blue-50 border-blue-300">
        <Info className="h-4 w-4 text-blue-600" />
        <AlertDescription className="text-blue-900">
          <strong>Note:</strong> Only <strong>Revenue Targets</strong> and <strong>Meeting Banners</strong> are configurable. 
          All other KPIs (deals count, pipe created, weighted pipe, etc.) are automatically calculated from the Google Sheet data.
        </AlertDescription>
      </Alert>

      {/* Message Alert */}
      {message && (
        <Alert variant={message.type === 'success' ? 'default' : message.type === 'error' ? 'destructive' : 'default'} className="mb-4">
          {message.type === 'success' ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* View Tabs */}
      <Tabs value={selectedView?.id} onValueChange={(viewId) => {
        const view = views.find(v => v.id === viewId);
        setSelectedView(view);
      }}>
        <TabsList className="mb-4">
          {views.map(view => (
            <TabsTrigger key={view.id} value={view.id}>
              {view.name}
              {view.is_master && ' (Master)'}
            </TabsTrigger>
          ))}
        </TabsList>

        {views.map(view => (
          <TabsContent key={view.id} value={view.id}>
            <div className="space-y-6">
              
              {/* Sync Button */}
              <div className="flex justify-end">
                <Button
                  onClick={handleSyncFromSheet}
                  disabled={syncing}
                  variant="outline"
                  size="sm"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {syncing ? 'Syncing...' : 'Sync from Google Sheet'}
                </Button>
              </div>

              {/* DASHBOARD TAB - Revenue Targets 2025 */}
              <Card className="border-purple-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded">DASHBOARD TAB</span>
                    Revenue Targets 2025 (Monthly)
                  </CardTitle>
                  <CardDescription>
                    Configure monthly revenue targets. These are read from Google Sheet column Y (row 19) but can be edited manually.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {months2025.map(month => (
                      <div key={month.key}>
                        <Label htmlFor={`revenue_${month.key}`} className="text-xs">
                          {month.label} 2025
                        </Label>
                        <Input
                          id={`revenue_${month.key}`}
                          type="number"
                          value={targets?.revenue_2025?.[month.key] || 0}
                          onChange={(e) => updateRevenueTarget(month.key, e.target.value)}
                          className="mt-1"
                        />
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
                    <strong>Total 2025:</strong> ${Object.values(targets?.revenue_2025 || {}).reduce((a, b) => a + b, 0).toLocaleString()}
                  </div>
                </CardContent>
              </Card>

              {/* MEETINGS GENERATION TAB - Banner Targets */}
              <Card className="border-green-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">MEETINGS GENERATION TAB</span>
                    Meeting Banners Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure targets displayed in the "Meetings Generation" banner at the top of the tab
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="total_target">Total Target (Monthly)</Label>
                      <Input
                        id="total_target"
                        type="number"
                        value={targets?.meeting_generation?.total_target || 0}
                        onChange={(e) => updateMeetingTarget('total_target', e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Total meetings expected per month</p>
                    </div>
                    <div>
                      <Label htmlFor="inbound">Inbound Target</Label>
                      <Input
                        id="inbound"
                        type="number"
                        value={targets?.meeting_generation?.inbound || 0}
                        onChange={(e) => updateMeetingTarget('inbound', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="outbound">Outbound Target</Label>
                      <Input
                        id="outbound"
                        type="number"
                        value={targets?.meeting_generation?.outbound || 0}
                        onChange={(e) => updateMeetingTarget('outbound', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="referral">Referral Target</Label>
                      <Input
                        id="referral"
                        type="number"
                        value={targets?.meeting_generation?.referral || 0}
                        onChange={(e) => updateMeetingTarget('referral', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="upsells_cross">Upsells / Cross-sell Target</Label>
                      <Input
                        id="upsells_cross"
                        type="number"
                        value={targets?.meeting_generation?.upsells_cross || 0}
                        onChange={(e) => updateMeetingTarget('upsells_cross', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-green-50 rounded">
                    <div className="text-sm font-semibold mb-2">Preview Banner:</div>
                    <div className="grid grid-cols-5 gap-2 text-xs">
                      <div className="border p-2 rounded bg-white">
                        <div className="font-semibold">Total</div>
                        <div className="text-gray-600">_/{targets?.meeting_generation?.total_target || 0}</div>
                      </div>
                      <div className="border p-2 rounded bg-white">
                        <div className="font-semibold">Inbound</div>
                        <div className="text-gray-600">_/{targets?.meeting_generation?.inbound || 0}</div>
                      </div>
                      <div className="border p-2 rounded bg-white">
                        <div className="font-semibold">Outbound</div>
                        <div className="text-gray-600">_/{targets?.meeting_generation?.outbound || 0}</div>
                      </div>
                      <div className="border p-2 rounded bg-white">
                        <div className="font-semibold">Referral</div>
                        <div className="text-gray-600">_/{targets?.meeting_generation?.referral || 0}</div>
                      </div>
                      <div className="border p-2 rounded bg-white">
                        <div className="font-semibold">Upsells</div>
                        <div className="text-gray-600">_/{targets?.meeting_generation?.upsells_cross || 0}</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* MEETINGS GENERATION TAB - Intro & POA Banner */}
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">MEETINGS GENERATION TAB</span>
                    Intro & POA Banner Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure targets displayed in the "Intro & POA" section of Meetings Generation tab
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="intro_target">Intro Target (Monthly)</Label>
                      <Input
                        id="intro_target"
                        type="number"
                        value={targets?.intro_poa?.intro || 0}
                        onChange={(e) => updateIntroPOATarget('intro', e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Total introductions expected</p>
                    </div>
                    <div>
                      <Label htmlFor="poa_target">POA Target (Monthly)</Label>
                      <Input
                        id="poa_target"
                        type="number"
                        value={targets?.intro_poa?.poa || 0}
                        onChange={(e) => updateIntroPOATarget('poa', e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Total POAs expected</p>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-blue-50 rounded">
                    <div className="text-sm font-semibold mb-2">Preview Banner:</div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="border p-3 rounded bg-white">
                        <div className="font-semibold text-lg">_/{targets?.intro_poa?.intro || 0}</div>
                        <div className="text-gray-600">Intro</div>
                      </div>
                      <div className="border p-3 rounded bg-white">
                        <div className="font-semibold text-lg">_/{targets?.intro_poa?.poa || 0}</div>
                        <div className="text-gray-600">POA</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Info sur autres KPIs */}
              <Alert className="bg-gray-50 border-gray-300">
                <Info className="h-4 w-4 text-gray-600" />
                <AlertDescription className="text-gray-700">
                  <strong>Calculated from Sheet Data:</strong> All other KPIs (Deals Count, New Pipe Created, 
                  Weighted Pipe, Active Deals, Pipeline Metrics, Projections, etc.) are automatically calculated 
                  from the Google Sheet data and cannot be manually configured.
                </AlertDescription>
              </Alert>

              {/* Save Button */}
              <div className="flex justify-end gap-3">
                <Button 
                  onClick={handleSave} 
                  disabled={saving}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {saving ? 'Saving...' : 'Save All Targets'}
                </Button>
              </div>

            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

export default AdminTargetsPage;
