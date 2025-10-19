import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings, Save, AlertCircle, CheckCircle2, Download, Info, RefreshCw } from 'lucide-react';
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

  // Auto-refresh targets every 30 seconds to detect changes from other admins
  useEffect(() => {
    if (!selectedView) return;

    const intervalId = setInterval(() => {
      // Silent reload without showing loading state
      axios.get(`${API}/views/${selectedView.id}/config`, {
        withCredentials: true
      })
      .then(response => {
        const newTargets = response.data.targets;
        // Only update if targets actually changed
        if (JSON.stringify(newTargets) !== JSON.stringify(targets)) {
          setTargets(newTargets);
          setMessage({
            type: 'info',
            text: '🔄 Targets updated by another admin. Refreshed automatically.'
          });
          setTimeout(() => setMessage(null), 3000);
        }
      })
      .catch(err => {
        console.error('Auto-refresh failed:', err);
      });
    }, 30000); // Check every 30 seconds

    return () => clearInterval(intervalId);
  }, [selectedView, targets]);

  // Also reload when tab becomes visible again
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && selectedView) {
        loadViewTargets(selectedView.id);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
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
        dashboard_top_cards: {
          ytd_target: 12600000,
          new_pipe_created: 2000000,
          created_weighted_pipe: 800000
        },
        dashboard_banners: {
          meetings_generation_target: 50,
          intro_target: 45,
          poa_target: 45,
          new_pipe_target: 2000000,
          deals_closed_count: 10,
          deals_closed_arr: 500000
        },
        closing_projections: {
          next_30_days_target: 250000,
          next_60_days_target: 500000,
          next_90_days_target: 750000,
          potentially_delayed_target: 200000
        },
        dashboard_bottom_cards: {
          new_pipe_created: 2000000,
          created_weighted_pipe: 800000,
          ytd_revenue: 4500000,
          ytd_aggregate_pipeline: 7500000,
          ytd_cumulative_weighted: 2500000
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
        },
        meetings_attended: {
          meetings_scheduled: 50,
          poa_generated: 18,
          deals_closed: 6
        },
        // NEW: Direct targets for Meetings Attended TAB (no multiplication, direct display)
        meetings_attended_tab: {
          meetings_scheduled_target: 50,
          poa_generated_target: 18,
          deals_closed_target: 6
        },
        deals_closed_current_period: {
          deals_target: 10,
          arr_target: 500000
        },
        // NEW: Direct targets for Deals Closed TAB (no multiplication, direct display)
        deals_closed_tab: {
          deals_closed_target: 10,
          arr_closed_target: 500000
        },
        upsell_renew: {
          upsells_target: 5,
          renewals_target: 10,
          mrr_target: 50000
        },
        deals_closed_yearly: {
          deals_target: 36,
          arr_target: 4500000
        }
      };

      // Check if this is the Master view
      const currentView = views.find(v => v.id === viewId);
      const isMasterView = currentView?.name === 'Master';

      if (isMasterView) {
        // Check if Master has manual overrides saved
        const savedTargets = response.data.targets;
        const hasManualOverrides = savedTargets && Object.keys(savedTargets).length > 0;
        
        if (hasManualOverrides) {
          // Use saved manual targets
          console.log('📝 Master view: Using manual overrides');
          setTargets(savedTargets);
        } else {
          // Calculate targets as sum of all other views (auto-aggregate)
          console.log('🔢 Master view: Auto-calculating from other views');
          const calculatedTargets = await calculateMasterTargets();
          setTargets(calculatedTargets);
        }
      } else {
        setTargets(response.data.targets || defaultTargets);
      }
    } catch (error) {
      console.error('Error loading targets:', error);
      setMessage({ type: 'error', text: 'Failed to load targets' });
    } finally {
      setLoading(false);
    }
  };

  const calculateMasterTargets = async () => {
    try {
      // Get all views except Master
      const otherViews = views.filter(v => v.name !== 'Master');
      
      // Fetch targets for all other views
      const targetsPromises = otherViews.map(view => 
        axios.get(`${API}/views/${view.id}/config`, { withCredentials: true })
      );
      
      const responses = await Promise.all(targetsPromises);
      const allTargets = responses.map(r => r.data.targets).filter(t => t);

      // Initialize sum structure
      const sumTargets = {
        revenue_2025: {
          jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0,
          jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0
        },
        dashboard_bottom_cards: {
          new_pipe_created: 0,
          created_weighted_pipe: 0,
          ytd_revenue: 0,
          ytd_aggregate_pipeline: 0,
          ytd_cumulative_weighted: 0
        },
        meeting_generation: {
          total_target: 0,
          inbound: 0,
          outbound: 0,
          referral: 0,
          upsells_cross: 0
        },
        intro_poa: {
          intro: 0,
          poa: 0
        },
        meetings_attended: {
          meetings_scheduled: 0,
          poa_generated: 0,
          deals_closed: 0
        },
        // NEW: Direct tab targets
        meetings_attended_tab: {
          meetings_scheduled_target: 0,
          poa_generated_target: 0,
          deals_closed_target: 0
        },
        deals_closed_current_period: {
          deals_target: 0,
          arr_target: 0
        },
        deals_closed_tab: {
          deals_closed_target: 0,
          arr_closed_target: 0
        },
        upsell_renew: {
          upsells_target: 0,
          renewals_target: 0,
          mrr_target: 0
        },
        deals_closed_yearly: {
          deals_target: 0,
          arr_target: 0
        }
      };

      // Sum all targets
      allTargets.forEach(viewTargets => {
        // Revenue 2025
        if (viewTargets.revenue_2025) {
          Object.keys(sumTargets.revenue_2025).forEach(month => {
            sumTargets.revenue_2025[month] += (viewTargets.revenue_2025[month] || 0);
          });
        }

        // Dashboard bottom cards
        if (viewTargets.dashboard_bottom_cards) {
          sumTargets.dashboard_bottom_cards.new_pipe_created += (viewTargets.dashboard_bottom_cards.new_pipe_created || 0);
          sumTargets.dashboard_bottom_cards.created_weighted_pipe += (viewTargets.dashboard_bottom_cards.created_weighted_pipe || 0);
          sumTargets.dashboard_bottom_cards.ytd_revenue += (viewTargets.dashboard_bottom_cards.ytd_revenue || 0);
          sumTargets.dashboard_bottom_cards.ytd_aggregate_pipeline += (viewTargets.dashboard_bottom_cards.ytd_aggregate_pipeline || 0);
          sumTargets.dashboard_bottom_cards.ytd_cumulative_weighted += (viewTargets.dashboard_bottom_cards.ytd_cumulative_weighted || 0);
        }

        // Meeting generation
        if (viewTargets.meeting_generation) {
          sumTargets.meeting_generation.total_target += (viewTargets.meeting_generation.total_target || 0);
          sumTargets.meeting_generation.inbound += (viewTargets.meeting_generation.inbound || 0);
          sumTargets.meeting_generation.outbound += (viewTargets.meeting_generation.outbound || 0);
          sumTargets.meeting_generation.referral += (viewTargets.meeting_generation.referral || 0);
          sumTargets.meeting_generation.upsells_cross += (viewTargets.meeting_generation.upsells_cross || 0);
        }

        // Intro POA
        if (viewTargets.intro_poa) {
          sumTargets.intro_poa.intro += (viewTargets.intro_poa.intro || 0);
          sumTargets.intro_poa.poa += (viewTargets.intro_poa.poa || 0);
        }

        // Meetings attended
        if (viewTargets.meetings_attended) {
          sumTargets.meetings_attended.meetings_scheduled += (viewTargets.meetings_attended.meetings_scheduled || 0);
          sumTargets.meetings_attended.poa_generated += (viewTargets.meetings_attended.poa_generated || 0);
          sumTargets.meetings_attended.deals_closed += (viewTargets.meetings_attended.deals_closed || 0);
        }

        // Deals closed current period
        if (viewTargets.deals_closed_current_period) {
          sumTargets.deals_closed_current_period.deals_target += (viewTargets.deals_closed_current_period.deals_target || 0);
          sumTargets.deals_closed_current_period.arr_target += (viewTargets.deals_closed_current_period.arr_target || 0);
        }

        // Upsell & Renew
        if (viewTargets.upsell_renew) {
          sumTargets.upsell_renew.upsells_target += (viewTargets.upsell_renew.upsells_target || 0);
          sumTargets.upsell_renew.renewals_target += (viewTargets.upsell_renew.renewals_target || 0);
          sumTargets.upsell_renew.mrr_target += (viewTargets.upsell_renew.mrr_target || 0);
        }

        // Deals closed yearly
        if (viewTargets.deals_closed_yearly) {
          sumTargets.deals_closed_yearly.deals_target += (viewTargets.deals_closed_yearly.deals_target || 0);
          sumTargets.deals_closed_yearly.arr_target += (viewTargets.deals_closed_yearly.arr_target || 0);
        }

        // NEW: Meetings Attended TAB direct targets
        if (viewTargets.meetings_attended_tab) {
          sumTargets.meetings_attended_tab.meetings_scheduled_target += (viewTargets.meetings_attended_tab.meetings_scheduled_target || 0);
          sumTargets.meetings_attended_tab.poa_generated_target += (viewTargets.meetings_attended_tab.poa_generated_target || 0);
          sumTargets.meetings_attended_tab.deals_closed_target += (viewTargets.meetings_attended_tab.deals_closed_target || 0);
        }

        // NEW: Deals Closed TAB direct targets
        if (viewTargets.deals_closed_tab) {
          sumTargets.deals_closed_tab.deals_closed_target += (viewTargets.deals_closed_tab.deals_closed_target || 0);
          sumTargets.deals_closed_tab.arr_closed_target += (viewTargets.deals_closed_tab.arr_closed_target || 0);
        }
      });

      return sumTargets;
    } catch (error) {
      console.error('Error calculating master targets:', error);
      return null;
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

    const isMasterView = selectedView.name === 'Master';
    
    setSaving(true);
    setMessage(null);

    try {
      const response = await axios.put(
        `${API}/admin/views/${selectedView.id}/targets`,
        targets,
        { withCredentials: true }
      );
      
      // Console log for verification
      console.log('✅ Targets saved successfully!');
      console.log('View:', selectedView.name);
      console.log('Saved targets:', targets);
      console.log('Backend response:', response.data);
      
      if (isMasterView) {
        setMessage({ 
          type: 'success', 
          text: '✅ Master targets saved! Frontend updated. These manual values will override auto-calculated aggregates.' 
        });
      } else {
        setMessage({ 
          type: 'success', 
          text: '✅ Targets saved successfully! Frontend has been updated with the new values.' 
        });
      }
      
      // Clear message after 5 seconds (extended to ensure user sees it)
      setTimeout(() => setMessage(null), 5000);
    } catch (error) {
      console.error('❌ Failed to save targets:', error);
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

        {views.map(view => {
          const isMasterView = view.name === 'Master';
          
          return (
          <TabsContent key={view.id} value={view.id}>
            <div className="space-y-6">
              
              {/* Master View Info */}
              {isMasterView && (
                <Alert className="bg-blue-50 border-blue-300">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-900">
                    <strong>Master View:</strong> By default, targets are auto-calculated as the sum of all other views. 
                    However, you can <strong>manually override</strong> any target value. Manual values will be used instead of auto-calculated ones.
                    Monthly targets will be multiplied by the number of months in the selected period in the dashboard.
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Sync Button */}
              <div className="flex justify-end">
                <Button
                  onClick={handleSyncFromSheet}
                  disabled={syncing || isMasterView}
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
                    {isMasterView 
                      ? 'Monthly revenue targets. Auto-aggregated by default, but you can manually override any value.' 
                      : 'Configure monthly revenue targets. These are read from Google Sheet column Y (row 19) but can be edited manually.'}
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

              {/* DASHBOARD TAB - Main Dashboard Cards (Top 4) */}
              <Card className="border-pink-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-pink-100 text-pink-700 text-xs font-semibold rounded">DASHBOARD TAB</span>
                    Main Dashboard Cards Targets (Row 1)
                  </CardTitle>
                  <CardDescription>
                    Configure targets for the 4 main dashboard cards at the top: YTD Revenue, New Pipe Created, Created Weighted Pipe
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="ytd_target_2025">YTD Revenue Target 2025 ($)</Label>
                      <Input
                        id="ytd_target_2025"
                        type="number"
                        value={targets?.dashboard_top_cards?.ytd_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            dashboard_top_cards: {
                              ...(prev.dashboard_top_cards || {}),
                              ytd_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="100000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Year-to-date revenue target for 2025</p>
                    </div>
                    <div>
                      <Label htmlFor="new_pipe_target">New Pipe Created Monthly Target ($)</Label>
                      <Input
                        id="new_pipe_target"
                        type="number"
                        value={targets?.dashboard_top_cards?.new_pipe_created || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            dashboard_top_cards: {
                              ...(prev.dashboard_top_cards || {}),
                              new_pipe_created: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="100000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target for new pipeline created (multiplied by period)</p>
                    </div>
                    <div>
                      <Label htmlFor="weighted_pipe_target">Created Weighted Pipe Monthly Target ($)</Label>
                      <Input
                        id="weighted_pipe_target"
                        type="number"
                        value={targets?.dashboard_top_cards?.created_weighted_pipe || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            dashboard_top_cards: {
                              ...(prev.dashboard_top_cards || {}),
                              created_weighted_pipe: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="100000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target for weighted pipeline (multiplied by period)</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      {/* Card 1: YTD Revenue 2025 */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-2 flex items-center gap-1">
                          💵 YTD Revenue 2025
                        </div>
                        <div className="text-2xl font-bold text-gray-800 mb-1">$X.XX M</div>
                        <div className="text-xs text-gray-500 mb-2">Target: ${((targets?.dashboard_top_cards?.ytd_target || 0) / 1000000).toFixed(1)}M</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center">X% of target</div>
                        <div className="mt-2 text-xs text-center px-2 py-1 bg-gray-200 text-gray-600 rounded">Status</div>
                      </div>

                      {/* Card 2: YTD Remaining 2025 */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-2">⚠️ YTD Remaining 2025</div>
                        <div className="text-2xl font-bold text-gray-800 mb-1">$X.XX M</div>
                        <div className="text-xs text-gray-500 mb-2">Calculated from YTD Target - YTD Revenue</div>
                        <div className="mt-8 text-xs text-center px-2 py-1 bg-gray-200 text-gray-600 rounded">Remaining</div>
                      </div>

                      {/* Card 3: New Pipe Created */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-2">📈 New Pipe Created</div>
                        <div className="text-2xl font-bold text-gray-800 mb-1">$X.XX M</div>
                        <div className="text-xs text-gray-500 mb-2">Target: ${((targets?.dashboard_top_cards?.new_pipe_created || 0) / 1000000).toFixed(1)}M × period</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center">X% of target</div>
                        <div className="mt-2 text-xs text-center px-2 py-1 bg-gray-200 text-gray-600 rounded">Status</div>
                      </div>

                      {/* Card 4: Created Weighted Pipe */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-2">🎯 Created Weighted Pipe</div>
                        <div className="text-2xl font-bold text-gray-800 mb-1">$X.XX M</div>
                        <div className="text-xs text-gray-500 mb-2">Target: ${((targets?.dashboard_top_cards?.created_weighted_pipe || 0) / 1000000).toFixed(1)}M × period</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center">X% of target</div>
                        <div className="mt-2 text-xs text-center px-2 py-1 bg-gray-200 text-gray-600 rounded">Status</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values calculated from sheet data. Period targets multiply monthly base × selected months.
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* DASHBOARD TAB - Dashboard Banner Cards (Row 2) */}
              <Card className="border-pink-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-pink-100 text-pink-700 text-xs font-semibold rounded">DASHBOARD TAB</span>
                    Dashboard Banner Cards Targets (Row 2)
                  </CardTitle>
                  <CardDescription>
                    Configure monthly targets for the 4 dashboard banner cards below the main cards
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="dashboard_meetings_gen">Meetings Generation Monthly Target</Label>
                      <Input
                        id="dashboard_meetings_gen"
                        type="number"
                        value={targets?.dashboard_banners?.meetings_generation_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            dashboard_banners: {
                              ...(prev.dashboard_banners || {}),
                              meetings_generation_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Total meetings to generate per month</p>
                    </div>
                    <div>
                      <Label htmlFor="dashboard_intro_poa">Intro & POA Monthly Targets</Label>
                      <div className="grid grid-cols-2 gap-2 mt-1">
                        <Input
                          placeholder="Intro"
                          type="number"
                          value={targets?.dashboard_banners?.intro_target || 0}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 0;
                            setTargets(prev => ({
                              ...prev,
                              dashboard_banners: {
                                ...(prev.dashboard_banners || {}),
                                intro_target: value
                              }
                            }));
                          }}
                        />
                        <Input
                          placeholder="POA"
                          type="number"
                          value={targets?.dashboard_banners?.poa_target || 0}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 0;
                            setTargets(prev => ({
                              ...prev,
                              dashboard_banners: {
                                ...(prev.dashboard_banners || {}),
                                poa_target: value
                              }
                            }));
                          }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Intro meetings and POA generated per month</p>
                    </div>
                    <div>
                      <Label htmlFor="dashboard_new_pipe">New Pipe Created Monthly ($)</Label>
                      <Input
                        id="dashboard_new_pipe"
                        type="number"
                        value={targets?.dashboard_banners?.new_pipe_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            dashboard_banners: {
                              ...(prev.dashboard_banners || {}),
                              new_pipe_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="100000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Pipeline creation target per month</p>
                    </div>
                    <div>
                      <Label htmlFor="dashboard_deals_closed">Deals Closed Monthly Targets</Label>
                      <div className="grid grid-cols-2 gap-2 mt-1">
                        <Input
                          placeholder="Deals #"
                          type="number"
                          value={targets?.dashboard_banners?.deals_closed_count || 0}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 0;
                            setTargets(prev => ({
                              ...prev,
                              dashboard_banners: {
                                ...(prev.dashboard_banners || {}),
                                deals_closed_count: value
                              }
                            }));
                          }}
                        />
                        <Input
                          placeholder="ARR $"
                          type="number"
                          value={targets?.dashboard_banners?.deals_closed_arr || 0}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 0;
                            setTargets(prev => ({
                              ...prev,
                              dashboard_banners: {
                                ...(prev.dashboard_banners || {}),
                                deals_closed_arr: value
                              }
                            }));
                          }}
                          step="50000"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Number of deals and ARR closed per month</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      {/* Card 1: Meetings Generation */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs font-semibold text-gray-600 mb-3">Meetings Generation</div>
                        <div className="text-center mb-2">
                          <div className="text-3xl font-bold text-gray-800">X/X</div>
                          <div className="text-xs text-gray-500 mt-1">Total Target: {targets?.dashboard_banners?.meetings_generation_target || 0}</div>
                        </div>
                        <div className="text-xs text-gray-600 space-y-1">
                          <div>Inbound: X/X</div>
                          <div>Outbound: X/X</div>
                          <div>Referral: X/X</div>
                        </div>
                      </div>

                      {/* Card 2: Intro & POA */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs font-semibold text-gray-600 mb-3">Intro & POA</div>
                        <div className="text-center space-y-3">
                          <div>
                            <div className="text-3xl font-bold text-gray-800">X/{targets?.dashboard_banners?.intro_target || 0}</div>
                            <div className="text-xs text-gray-500">Intro</div>
                          </div>
                          <div>
                            <div className="text-3xl font-bold text-gray-800">X/{targets?.dashboard_banners?.poa_target || 0}</div>
                            <div className="text-xs text-gray-500">POA</div>
                          </div>
                        </div>
                      </div>

                      {/* Card 3: New Pipe Created */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs font-semibold text-gray-600 mb-3">New Pipe Created</div>
                        <div className="text-center mb-2">
                          <div className="text-3xl font-bold text-purple-600">$X.XM</div>
                          <div className="text-xs text-gray-500 mt-1">Total Pipe Generation</div>
                        </div>
                        <div className="text-center mb-2">
                          <div className="text-2xl font-bold text-gray-800">$X.XM</div>
                          <div className="text-xs text-gray-500 mt-1">Aggregate Weighted Pipe</div>
                        </div>
                        <div className="text-xs text-gray-500 text-center">Target: ${((targets?.dashboard_banners?.new_pipe_target || 0) / 1000000).toFixed(1)}M × period</div>
                      </div>

                      {/* Card 4: Deals Closed (Current Period) */}
                      <div className="bg-gray-50 border-2 border-blue-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs font-semibold text-blue-600 mb-3">Deals Closed (Current Period)</div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="text-center bg-white p-2 rounded">
                            <div className="text-2xl font-bold text-gray-800">X</div>
                            <div className="text-xs text-gray-600">Deals Closed</div>
                            <div className="text-xs text-gray-500">Target: {targets?.dashboard_banners?.deals_closed_count || 0}</div>
                          </div>
                          <div className="text-center bg-white p-2 rounded">
                            <div className="text-2xl font-bold text-green-600">$X.XM</div>
                            <div className="text-xs text-gray-600">ARR Closed</div>
                            <div className="text-xs text-gray-500">Target: ${((targets?.dashboard_banners?.deals_closed_arr || 0) / 1000000).toFixed(1)}M</div>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-gray-600 text-center">X% of target</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values calculated from sheet data. Targets multiply by selected period (Monthly/July-Dec/Custom).
                    </div>
                  </div>
                </CardContent>
              </Card>


              {/* PROJECTIONS TAB - Closing Projections Board Targets */}
              <Card className="border-indigo-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded">PROJECTIONS TAB</span>
                    Closing Projections Board - Period Targets
                  </CardTitle>
                  <CardDescription>
                    Configure revenue targets for each time period column in the interactive closing projections board
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="next_30_days_target">Next 30 Days Target ($)</Label>
                      <Input
                        id="next_30_days_target"
                        type="number"
                        value={targets?.closing_projections?.next_30_days_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            closing_projections: {
                              ...(prev.closing_projections || {}),
                              next_30_days_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="50000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Expected ARR to close in next 30 days</p>
                    </div>
                    <div>
                      <Label htmlFor="next_60_days_target">Next 60 Days Target ($)</Label>
                      <Input
                        id="next_60_days_target"
                        type="number"
                        value={targets?.closing_projections?.next_60_days_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            closing_projections: {
                              ...(prev.closing_projections || {}),
                              next_60_days_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="50000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Expected ARR to close in next 60 days</p>
                    </div>
                    <div>
                      <Label htmlFor="next_90_days_target">Next 90 Days Target ($)</Label>
                      <Input
                        id="next_90_days_target"
                        type="number"
                        value={targets?.closing_projections?.next_90_days_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            closing_projections: {
                              ...(prev.closing_projections || {}),
                              next_90_days_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="50000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Expected ARR to close in next 90 days</p>
                    </div>
                    <div>
                      <Label htmlFor="potentially_delayed_target">Potentially Delayed Target ($)</Label>
                      <Input
                        id="potentially_delayed_target"
                        type="number"
                        value={targets?.closing_projections?.potentially_delayed_target || 0}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 0;
                          setTargets(prev => ({
                            ...prev,
                            closing_projections: {
                              ...(prev.closing_projections || {}),
                              potentially_delayed_target: value
                            }
                          }));
                        }}
                        className="mt-1"
                        step="50000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Expected ARR for deals at risk of delay</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Closing Projections Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      {/* Column 1: Next 30 Days */}
                      <div className="bg-gray-50 border-2 border-green-300 rounded-lg p-3 shadow-sm">
                        <div className="text-center mb-2">
                          <div className="text-xs font-semibold text-green-600 mb-1">Next 30 Days</div>
                          <div className="text-lg font-bold text-gray-800">${((targets?.closing_projections?.next_30_days_target || 0) / 1000).toFixed(0)}K</div>
                          <div className="text-xs text-gray-500">Target: ${((targets?.closing_projections?.next_30_days_target || 0) / 1000).toFixed(0)}K</div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div className="bg-green-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-center text-gray-500 mb-2">X deals • $XK</div>
                        <div className="space-y-1">
                          <div className="bg-white border border-gray-300 rounded p-1 text-xs text-gray-600">Deal cards appear here</div>
                        </div>
                      </div>

                      {/* Column 2: Next 60 Days */}
                      <div className="bg-gray-50 border-2 border-blue-300 rounded-lg p-3 shadow-sm">
                        <div className="text-center mb-2">
                          <div className="text-xs font-semibold text-blue-600 mb-1">Next 60 Days</div>
                          <div className="text-lg font-bold text-gray-800">${((targets?.closing_projections?.next_60_days_target || 0) / 1000).toFixed(0)}K</div>
                          <div className="text-xs text-gray-500">Target: ${((targets?.closing_projections?.next_60_days_target || 0) / 1000).toFixed(0)}K</div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div className="bg-blue-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-center text-gray-500 mb-2">X deals • $XK</div>
                        <div className="space-y-1">
                          <div className="bg-white border border-gray-300 rounded p-1 text-xs text-gray-600">Deal cards appear here</div>
                        </div>
                      </div>

                      {/* Column 3: Next 90 Days */}
                      <div className="bg-gray-50 border-2 border-purple-300 rounded-lg p-3 shadow-sm">
                        <div className="text-center mb-2">
                          <div className="text-xs font-semibold text-purple-600 mb-1">Next 90 Days</div>
                          <div className="text-lg font-bold text-gray-800">${((targets?.closing_projections?.next_90_days_target || 0) / 1000).toFixed(0)}K</div>
                          <div className="text-xs text-gray-500">Target: ${((targets?.closing_projections?.next_90_days_target || 0) / 1000).toFixed(0)}K</div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div className="bg-purple-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-center text-gray-500 mb-2">X deals • $XK</div>
                        <div className="space-y-1">
                          <div className="bg-white border border-gray-300 rounded p-1 text-xs text-gray-600">Deal cards appear here</div>
                        </div>
                      </div>

                      {/* Column 4: Potentially Delayed */}
                      <div className="bg-gray-50 border-2 border-orange-300 rounded-lg p-3 shadow-sm">
                        <div className="text-center mb-2">
                          <div className="text-xs font-semibold text-orange-600 mb-1">Potentially Delayed</div>
                          <div className="text-lg font-bold text-gray-800">${((targets?.closing_projections?.potentially_delayed_target || 0) / 1000).toFixed(0)}K</div>
                          <div className="text-xs text-gray-500">Target: ${((targets?.closing_projections?.potentially_delayed_target || 0) / 1000).toFixed(0)}K</div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div className="bg-orange-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-center text-gray-500 mb-2">X deals • $XK</div>
                        <div className="space-y-1">
                          <div className="bg-white border border-gray-300 rounded p-1 text-xs text-gray-600">Deal cards appear here</div>
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows board layout. Actual deals are draggable in the Projections tab. Progress bars update based on deals assigned to each column.
                    </div>
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
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                      {/* Total Meetings */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">📊 Total Meetings</div>
                        <div className="text-xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meeting_generation?.total_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-gray-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                      </div>

                      {/* Inbound */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">🟢 Inbound</div>
                        <div className="text-xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meeting_generation?.inbound || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-gray-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                      </div>

                      {/* Outbound */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">🟠 Outbound</div>
                        <div className="text-xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meeting_generation?.outbound || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-gray-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                      </div>

                      {/* Referral */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">🟣 Referral</div>
                        <div className="text-xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meeting_generation?.referral || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-gray-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                      </div>

                      {/* Upsells */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">🔵 Upsells</div>
                        <div className="text-xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meeting_generation?.upsells_cross || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-gray-400 h-1.5 rounded-full" style={{width: '0%'}}></div>
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values calculated from sheet data.
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
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Intro Card */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">👥 Intro</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.intro_poa?.intro || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* POA Card */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">📋 POA</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.intro_poa?.poa || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values calculated from sheet data.
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* MEETINGS ATTENDED TAB - NEW Monthly Tab Targets */}
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">MEETINGS ATTENDED TAB</span>
                    Meetings Attended Monthly Targets
                  </CardTitle>
                  <CardDescription>
                    Configure MONTHLY targets for Meetings Attended tab (will be multiplied by period duration in dashboard)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="meetings_scheduled_tab">Meetings Scheduled Target (Monthly)</Label>
                      <Input
                        id="meetings_scheduled_tab"
                        type="number"
                        value={targets?.meetings_attended_tab?.meetings_scheduled_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            meetings_attended_tab: {
                              ...prev.meetings_attended_tab,
                              meetings_scheduled_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target × period duration</p>
                    </div>
                    <div>
                      <Label htmlFor="poa_generated_tab">POA Generated Target (Monthly)</Label>
                      <Input
                        id="poa_generated_tab"
                        type="number"
                        value={targets?.meetings_attended_tab?.poa_generated_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            meetings_attended_tab: {
                              ...prev.meetings_attended_tab,
                              poa_generated_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target × period duration</p>
                    </div>
                    <div>
                      <Label htmlFor="deals_closed_tab">Deals Closed Target (Monthly)</Label>
                      <Input
                        id="deals_closed_tab"
                        type="number"
                        value={targets?.meetings_attended_tab?.deals_closed_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            meetings_attended_tab: {
                              ...prev.meetings_attended_tab,
                              deals_closed_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target × period duration</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Meetings Scheduled */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">📅 Meetings Scheduled</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meetings_attended_tab?.meetings_scheduled_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* POA Generated */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">📋 POA Generated</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meetings_attended_tab?.poa_generated_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* Deals Closed */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">✅ Deals Closed</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.meetings_attended_tab?.deals_closed_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values × period (Monthly = ×1, Yearly = ×6).
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

              {/* DEALS & PIPELINE TAB - NEW Monthly Tab Targets for Deals Closed */}
              <Card className="border-orange-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-semibold rounded">DEALS & PIPELINE TAB</span>
                    Deals Closed Monthly Targets
                  </CardTitle>
                  <CardDescription>
                    Configure MONTHLY targets for Deals Closed banner (will be multiplied by period duration in dashboard)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="deals_closed_tab_target">Deals Closed Target (Monthly)</Label>
                      <Input
                        id="deals_closed_tab_target"
                        type="number"
                        value={targets?.deals_closed_tab?.deals_closed_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            deals_closed_tab: {
                              ...prev.deals_closed_tab,
                              deals_closed_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target × period duration</p>
                    </div>
                    <div>
                      <Label htmlFor="arr_closed_tab_target">ARR Closed Target (Monthly)</Label>
                      <Input
                        id="arr_closed_tab_target"
                        type="number"
                        value={targets?.deals_closed_tab?.arr_closed_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            deals_closed_tab: {
                              ...prev.deals_closed_tab,
                              arr_closed_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                        step="10000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly target × period duration</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Deals Closed */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">✅ Deals Closed</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.deals_closed_tab?.deals_closed_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* ARR Closed */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">💰 ARR Closed</div>
                        <div className="text-2xl font-bold text-gray-800">$X.XM</div>
                        <div className="text-xs text-gray-500 mb-2">Target: ${((targets?.deals_closed_tab?.arr_closed_target || 0) / 1000000).toFixed(1)}M</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values × period (Monthly = ×1, Yearly = ×6).
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* UPSELL & RENEW TAB - Upsells & Renewals Targets */}
              <Card className="border-teal-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-teal-100 text-teal-700 text-xs font-semibold rounded">UPSELL & RENEW TAB</span>
                    Upsells & Renewals Target Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure targets for Upsells and Renewals shown in the Upsells & Renewals tab
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="upsells_target">Upsells Target</Label>
                      <Input
                        id="upsells_target"
                        type="number"
                        value={targets?.upsell_renew?.upsells_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            upsell_renew: {
                              ...prev.upsell_renew,
                              upsells_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Number of upsells expected</p>
                    </div>
                    <div>
                      <Label htmlFor="renewals_target">Renewals Target</Label>
                      <Input
                        id="renewals_target"
                        type="number"
                        value={targets?.upsell_renew?.renewals_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            upsell_renew: {
                              ...prev.upsell_renew,
                              renewals_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Number of renewals expected</p>
                    </div>
                    <div>
                      <Label htmlFor="mrr_target">MRR Target</Label>
                      <Input
                        id="mrr_target"
                        type="number"
                        value={targets?.upsell_renew?.mrr_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            upsell_renew: {
                              ...prev.upsell_renew,
                              mrr_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        className="mt-1"
                        step="1000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Monthly Recurring Revenue target in $ (e.g., 50000 for $50K)</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-gray-100 rounded-lg border-2 border-gray-300">
                    <div className="text-sm font-semibold mb-3 text-gray-700">📊 Dashboard Preview (Grey Replica):</div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Upsells */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">📈 Upsells</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.upsell_renew?.upsells_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* Renewals */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">🔄 Renewals</div>
                        <div className="text-2xl font-bold text-gray-800">X</div>
                        <div className="text-xs text-gray-500 mb-2">Target: {targets?.upsell_renew?.renewals_target || 0}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">X% of target</div>
                      </div>

                      {/* MRR */}
                      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4 shadow-sm">
                        <div className="text-xs text-gray-600 mb-1">💰 MRR</div>
                        <div className="text-2xl font-bold text-gray-800">${((targets?.upsell_renew?.mrr_target || 0) / 1000).toFixed(0)}K</div>
                        <div className="text-xs text-gray-500 mb-2">Target: ${(targets?.upsell_renew?.mrr_target || 0).toLocaleString()}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-gray-400 h-2 rounded-full" style={{width: '0%'}}></div>
                        </div>
                        <div className="text-xs text-gray-600 text-center mt-2">Monthly Recurring</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-3 text-center italic">
                      ℹ️ Preview shows layout only. Actual values calculated from sheet data.
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* DEALS & PIPELINE TAB - Deals Closed Yearly (Jul-Dec 2025) */}
              <Card className="border-indigo-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded">DEALS & PIPELINE TAB</span>
                    Deals Closed Yearly Configuration (Jul-Dec 2025)
                  </CardTitle>
                  <CardDescription>
                    Configure targets for Deals Closed and ARR Closed shown in July to Dec view
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="deals_closed_yearly">Deals Closed Target (Jul-Dec)</Label>
                      <Input
                        id="deals_closed_yearly"
                        type="number"
                        value={targets?.deals_closed_yearly?.deals_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            deals_closed_yearly: {
                              ...prev.deals_closed_yearly,
                              deals_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        
                          className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Number of deals to close from July to December</p>
                    </div>
                    <div>
                      <Label htmlFor="arr_closed_yearly">ARR Closed Target (Jul-Dec)</Label>
                      <Input
                        id="arr_closed_yearly"
                        type="number"
                        value={targets?.deals_closed_yearly?.arr_target || 0}
                        onChange={(e) => {
                          setTargets(prev => ({
                            ...prev,
                            deals_closed_yearly: {
                              ...prev.deals_closed_yearly,
                              arr_target: parseInt(e.target.value) || 0
                            }
                          }));
                        }}
                        
                          className="mt-1"
                        step="100000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Total ARR target in $ (e.g., 4500000 for $4.5M)</p>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-purple-50 rounded">
                    <div className="text-sm font-semibold mb-2">Preview Banner:</div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="border p-3 rounded bg-white">
                        <div className="font-semibold text-lg">_/{targets?.deals_closed_yearly?.deals_target || 0}</div>
                        <div className="text-gray-600">Deals Closed</div>
                        <div className="text-xs text-gray-500">Target: {targets?.deals_closed_yearly?.deals_target || 0}</div>
                      </div>
                      <div className="border p-3 rounded bg-white">
                        <div className="font-semibold text-lg">$_M</div>
                        <div className="text-gray-600">ARR Closed</div>
                        <div className="text-xs text-gray-500">Target: ${((targets?.deals_closed_yearly?.arr_target || 0) / 1000000).toFixed(1)}M</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Save Button & Reset to Auto-Aggregate for Master */}
              <div className="flex justify-end gap-3">
                {isMasterView && (
                  <Button 
                    onClick={async () => {
                      if (window.confirm('Reset Master targets to auto-calculated values from other views?')) {
                        const calculatedTargets = await calculateMasterTargets();
                        setTargets(calculatedTargets);
                        setMessage({ type: 'info', text: 'Master targets reset to auto-aggregated values. Click Save to confirm.' });
                      }
                    }}
                    variant="outline"
                    size="lg"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Reset to Auto-Aggregate
                  </Button>
                )}
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
          );
        })}
      </Tabs>
    </div>
  );
}

export default AdminTargetsPage;
