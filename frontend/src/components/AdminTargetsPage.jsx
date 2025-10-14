import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings, Save, AlertCircle, CheckCircle2 } from 'lucide-react';
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
  const [message, setMessage] = useState(null);

  // Check if user is super_admin
  const isAdmin = user?.role === 'super_admin';

  useEffect(() => {
    if (views.length > 0 && !selectedView) {
      setSelectedView(views[0]);
    }
  }, [views]);

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
        dashboard: {
          objectif_mensuel: 750000,
          deals_mensuel: 4,
          new_pipe_created_mensuel: 333333,
          weighted_pipe_mensuel: 133333
        },
        meeting_generation: {
          intro_mensuel: 7,
          inbound_mensuel: 4,
          outbound_mensuel: 3,
          referrals_mensuel: 2,
          upsells_x_mensuel: 2
        },
        meeting_attended: {
          poa_mensuel: 3,
          deals_closed_mensuel: 1
        },
        pipeline_metrics: {
          cumulative_pipeline_ytd: 7500000,
          cumulative_weighted_ytd: 2500000
        },
        projections: {
          next_14_days: 375000,
          next_30_60_days: 1125000,
          next_60_90_days: 750000
        },
        upsell_renew: {
          partner_meetings_mensuel: 5,
          upsell_target_mensuel: 250000
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

  const updateTarget = (section, field, value) => {
    setTargets(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
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

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Admin - Targets Configuration</h1>
        </div>
        <p className="text-gray-600">
          Configure monthly targets for all views. All values are monthly and will be multiplied by the selected period.
        </p>
      </div>

      {/* Message Alert */}
      {message && (
        <Alert variant={message.type === 'success' ? 'default' : 'destructive'} className="mb-4">
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
              {view.is_default && ' (Default)'}
            </TabsTrigger>
          ))}
        </TabsList>

        {views.map(view => (
          <TabsContent key={view.id} value={view.id}>
            <div className="space-y-6">
              
              {/* Dashboard Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Dashboard Targets (Monthly)</CardTitle>
                  <CardDescription>
                    Base monthly targets - will be multiplied by period (1 month, 6 months, etc.)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="objectif_mensuel">Objectif Mensuel ($)</Label>
                      <Input
                        id="objectif_mensuel"
                        type="number"
                        value={targets?.dashboard?.objectif_mensuel || 0}
                        onChange={(e) => updateTarget('dashboard', 'objectif_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="deals_mensuel">Deals Mensuel</Label>
                      <Input
                        id="deals_mensuel"
                        type="number"
                        value={targets?.dashboard?.deals_mensuel || 0}
                        onChange={(e) => updateTarget('dashboard', 'deals_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="new_pipe_created_mensuel">New Pipe Created Mensuel ($)</Label>
                      <Input
                        id="new_pipe_created_mensuel"
                        type="number"
                        value={targets?.dashboard?.new_pipe_created_mensuel || 0}
                        onChange={(e) => updateTarget('dashboard', 'new_pipe_created_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="weighted_pipe_mensuel">Weighted Pipe Mensuel ($)</Label>
                      <Input
                        id="weighted_pipe_mensuel"
                        type="number"
                        value={targets?.dashboard?.weighted_pipe_mensuel || 0}
                        onChange={(e) => updateTarget('dashboard', 'weighted_pipe_mensuel', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Meeting Generation Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Meeting Generation Targets (Monthly)</CardTitle>
                  <CardDescription>
                    Monthly targets for meeting generation by source
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="intro_mensuel">Intro Mensuel</Label>
                      <Input
                        id="intro_mensuel"
                        type="number"
                        value={targets?.meeting_generation?.intro_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_generation', 'intro_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="inbound_mensuel">Inbound Mensuel</Label>
                      <Input
                        id="inbound_mensuel"
                        type="number"
                        value={targets?.meeting_generation?.inbound_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_generation', 'inbound_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="outbound_mensuel">Outbound Mensuel</Label>
                      <Input
                        id="outbound_mensuel"
                        type="number"
                        value={targets?.meeting_generation?.outbound_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_generation', 'outbound_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="referrals_mensuel">Referrals Mensuel</Label>
                      <Input
                        id="referrals_mensuel"
                        type="number"
                        value={targets?.meeting_generation?.referrals_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_generation', 'referrals_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="upsells_x_mensuel">Upsells/Cross-sell Mensuel</Label>
                      <Input
                        id="upsells_x_mensuel"
                        type="number"
                        value={targets?.meeting_generation?.upsells_x_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_generation', 'upsells_x_mensuel', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Meeting Attended Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Meeting Attended Targets (Monthly)</CardTitle>
                  <CardDescription>
                    Monthly targets for meetings attended and deals closed
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="poa_mensuel">POA Mensuel</Label>
                      <Input
                        id="poa_mensuel"
                        type="number"
                        value={targets?.meeting_attended?.poa_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_attended', 'poa_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="deals_closed_mensuel">Deals Closed Mensuel</Label>
                      <Input
                        id="deals_closed_mensuel"
                        type="number"
                        value={targets?.meeting_attended?.deals_closed_mensuel || 0}
                        onChange={(e) => updateTarget('meeting_attended', 'deals_closed_mensuel', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Pipeline Metrics Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Metrics Targets (YTD)</CardTitle>
                  <CardDescription>
                    Year-to-date cumulative targets for pipeline metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="cumulative_pipeline_ytd">Cumulative Pipeline YTD ($)</Label>
                      <Input
                        id="cumulative_pipeline_ytd"
                        type="number"
                        value={targets?.pipeline_metrics?.cumulative_pipeline_ytd || 0}
                        onChange={(e) => updateTarget('pipeline_metrics', 'cumulative_pipeline_ytd', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="cumulative_weighted_ytd">Cumulative Weighted YTD ($)</Label>
                      <Input
                        id="cumulative_weighted_ytd"
                        type="number"
                        value={targets?.pipeline_metrics?.cumulative_weighted_ytd || 0}
                        onChange={(e) => updateTarget('pipeline_metrics', 'cumulative_weighted_ytd', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Projections Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Projections Targets (Period-based)</CardTitle>
                  <CardDescription>
                    Targets for closing projections by time period
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="next_14_days">Next 14 Days Target ($)</Label>
                      <Input
                        id="next_14_days"
                        type="number"
                        value={targets?.projections?.next_14_days || 0}
                        onChange={(e) => updateTarget('projections', 'next_14_days', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="next_30_60_days">Next 30-60 Days Target ($)</Label>
                      <Input
                        id="next_30_60_days"
                        type="number"
                        value={targets?.projections?.next_30_60_days || 0}
                        onChange={(e) => updateTarget('projections', 'next_30_60_days', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="next_60_90_days">Next 60-90 Days Target ($)</Label>
                      <Input
                        id="next_60_90_days"
                        type="number"
                        value={targets?.projections?.next_60_90_days || 0}
                        onChange={(e) => updateTarget('projections', 'next_60_90_days', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Upsell & Renew Targets */}
              <Card>
                <CardHeader>
                  <CardTitle>Upsell & Renew Targets (Monthly)</CardTitle>
                  <CardDescription>
                    Monthly targets for partner meetings and upsell revenue
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="partner_meetings_mensuel">Partner Meetings Mensuel</Label>
                      <Input
                        id="partner_meetings_mensuel"
                        type="number"
                        value={targets?.upsell_renew?.partner_meetings_mensuel || 0}
                        onChange={(e) => updateTarget('upsell_renew', 'partner_meetings_mensuel', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="upsell_target_mensuel">Upsell Target Mensuel ($)</Label>
                      <Input
                        id="upsell_target_mensuel"
                        type="number"
                        value={targets?.upsell_renew?.upsell_target_mensuel || 0}
                        onChange={(e) => updateTarget('upsell_renew', 'upsell_target_mensuel', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Save Button */}
              <div className="flex justify-end">
                <Button 
                  onClick={handleSave} 
                  disabled={saving}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Targets'}
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
