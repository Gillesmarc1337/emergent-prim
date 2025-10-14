import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings, Save, AlertCircle, CheckCircle2, Info, Calculator, TrendingUp, Calendar } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Composant d'explication des formules
function FormulaExplanation() {
  const [showHelp, setShowHelp] = useState(false);

  return (
    <Card className="mb-6 border-blue-200 bg-blue-50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-blue-900">Guide des Formules et Calculs</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowHelp(!showHelp)}
          >
            {showHelp ? 'Masquer' : 'Afficher'} les détails
          </Button>
        </div>
      </CardHeader>
      
      {showHelp && (
        <CardContent className="space-y-6">
          
          {/* Principe général */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
              <Calculator className="h-5 w-5 text-blue-600" />
              🎯 Principe Général - Template Universel
            </h3>
            <div className="space-y-2 text-sm">
              <Alert className="bg-amber-50 border-amber-300">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-900">
                  <strong>Important:</strong> Toutes les vues (Organic, Full Funnel, Signal, Market, Master) utilisent 
                  exactement les <strong>mêmes formules de calcul</strong>. Seuls les <strong>targets</strong> que vous 
                  configurez ici sont différents par vue.
                </AlertDescription>
              </Alert>
              <p className="text-gray-700">
                ✅ Les formules sont identiques pour tous<br/>
                ✅ Les targets sont personnalisables par vue<br/>
                ✅ Les données sont isolées par vue (collections MongoDB séparées)
              </p>
            </div>
          </div>

          {/* Formules Dashboard */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              📊 Section 1: Dashboard - Targets Mensuels × Période
            </h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded font-mono text-xs">
                <strong>Formule:</strong><br/>
                Target Affiché = Target Mensuel × Nombre de Mois
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="border p-3 rounded">
                  <div className="font-semibold text-blue-600 mb-1">Exemple - Vue Mensuelle (1 mois)</div>
                  <div className="text-xs space-y-1">
                    Target mensuel: <span className="font-bold">$750,000</span><br/>
                    Période: <span className="font-bold">1 mois</span><br/>
                    <div className="mt-2 pt-2 border-t">
                      → Target affiché: <span className="font-bold text-green-600">$750,000</span>
                    </div>
                  </div>
                </div>
                
                <div className="border p-3 rounded">
                  <div className="font-semibold text-blue-600 mb-1">Exemple - Vue July-Dec (6 mois)</div>
                  <div className="text-xs space-y-1">
                    Target mensuel: <span className="font-bold">$750,000</span><br/>
                    Période: <span className="font-bold">6 mois</span><br/>
                    <div className="mt-2 pt-2 border-t">
                      → Target affiché: <span className="font-bold text-green-600">$4,500,000</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-3 rounded text-xs">
                <strong>💡 Métriques concernées:</strong>
                <ul className="list-disc ml-5 mt-1 space-y-1">
                  <li><strong>Objectif (Revenue):</strong> Target de chiffre d'affaires</li>
                  <li><strong>Deals:</strong> Nombre de deals à closer</li>
                  <li><strong>New Pipe Created:</strong> Nouveau pipeline à générer</li>
                  <li><strong>Weighted Pipe:</strong> Pipeline pondéré à créer</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Formules Meeting Generation */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              🤝 Section 2: Meeting Generation - Targets par Source
            </h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded font-mono text-xs">
                <strong>Formule:</strong><br/>
                Meeting Goal = Target Mensuel × Nombre de Mois × Nombre de BDR/AE
              </div>
              
              <div className="bg-green-50 p-3 rounded text-xs">
                <strong>📋 Sources de meetings:</strong>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div>• <strong>Intro:</strong> Introductions partenaires</div>
                  <div>• <strong>Inbound:</strong> Leads entrants</div>
                  <div>• <strong>Outbound:</strong> Prospection sortante</div>
                  <div>• <strong>Referrals:</strong> Recommandations clients</div>
                  <div>• <strong>Upsells/Cross-sell:</strong> Clients existants</div>
                </div>
              </div>

              <div className="border p-3 rounded">
                <div className="font-semibold text-blue-600 mb-1">Exemple - BDR Performance (6 mois)</div>
                <div className="text-xs space-y-1">
                  Target intro mensuel: <span className="font-bold">7</span><br/>
                  Période: <span className="font-bold">6 mois</span><br/>
                  Nombre de BDR: <span className="font-bold">1</span> (ex: Marie)<br/>
                  <div className="mt-2 pt-2 border-t">
                    → Meeting Goal: <span className="font-bold text-green-600">7 × 6 × 1 = 42 intros</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Formules Weighted Pipe */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">⚖️ Weighted Pipe - Calcul de Pondération</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded font-mono text-xs">
                <strong>Formule Complète:</strong><br/>
                Weighted Value = Pipeline × Stage Weight × Time Weight × Source Weight
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="border p-3 rounded">
                  <div className="font-semibold text-purple-600 mb-2">Stage Weight</div>
                  <div className="text-xs space-y-1">
                    • Legals: <strong>100%</strong><br/>
                    • Proposal: <strong>50%</strong><br/>
                    • POA Booked: <strong>25%</strong><br/>
                    • Intro: <strong>10%</strong><br/>
                    • Inbox: <strong>5%</strong>
                  </div>
                </div>

                <div className="border p-3 rounded">
                  <div className="font-semibold text-purple-600 mb-2">Time Weight</div>
                  <div className="text-xs space-y-1">
                    Bonus si deal ancien:<br/>
                    • &lt; 30 jours: <strong>100%</strong><br/>
                    • 30-60 jours: <strong>110%</strong><br/>
                    • &gt; 60 jours: <strong>120%</strong>
                  </div>
                </div>

                <div className="border p-3 rounded">
                  <div className="font-semibold text-purple-600 mb-2">Source Weight</div>
                  <div className="text-xs space-y-1">
                    • Referral: <strong>120%</strong><br/>
                    • Upsell: <strong>115%</strong><br/>
                    • Inbound: <strong>110%</strong><br/>
                    • Outbound: <strong>100%</strong>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 p-3 rounded text-xs">
                <strong>Exemple de calcul:</strong><br/>
                Deal: $120,000 | Stage: Proposal (50%) | Temps: 45 jours (110%) | Source: Referral (120%)<br/>
                <div className="mt-1 font-mono">
                  Weighted = $120,000 × 0.5 × 1.1 × 1.2 = <strong className="text-purple-700">$79,200</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Formules YTD */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">📅 YTD (Year-to-Date) - Calculs Cumulatifs</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded font-mono text-xs">
                <strong>Formule:</strong><br/>
                YTD = Somme de tous les deals avec discovery_date entre 1er janvier et 31 décembre
              </div>

              <div className="space-y-2 text-xs">
                <div className="border-l-4 border-blue-500 pl-3">
                  <strong>YTD Revenue:</strong> Somme des ARR des deals "Closed" (stage A) en 2025
                </div>
                <div className="border-l-4 border-green-500 pl-3">
                  <strong>New Pipe Created:</strong> Somme des pipelines des deals découverts en 2025
                </div>
                <div className="border-l-4 border-purple-500 pl-3">
                  <strong>Cumulative Weighted YTD:</strong> Somme des weighted values cumulées
                </div>
                <div className="border-l-4 border-orange-500 pl-3">
                  <strong>Active Deals:</strong> Deals non "Closed", "Lost" ou "Not relevant"
                </div>
              </div>

              <div className="bg-amber-50 p-3 rounded text-xs">
                <strong>⚠️ Note importante:</strong> Les calculs YTD incluent tous les deals de l'année, 
                même ceux avec des dates dans le futur (bug corrigé le 13 octobre 2025).
              </div>
            </div>
          </div>

          {/* Pipeline Metrics */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">📈 Pipeline Metrics - Métriques Cumulatives</h3>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div className="border p-3 rounded">
                  <div className="font-semibold text-green-600 mb-1">Cumulative Pipeline YTD</div>
                  <div className="text-xs">
                    Pipeline total actif (excluant Closed/Lost/Not relevant)<br/>
                    <strong>Target fixe YTD:</strong> Objectif cumulatif pour l'année
                  </div>
                </div>
                
                <div className="border p-3 rounded">
                  <div className="font-semibold text-green-600 mb-1">Cumulative Weighted YTD</div>
                  <div className="text-xs">
                    Pipeline pondéré actif (avec weights)<br/>
                    <strong>Target fixe YTD:</strong> Plus réaliste que pipeline brut
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Projections */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">🎯 Projections - Closing par Période</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded text-xs">
                <strong>Deals catégorisés par période de closing estimée:</strong>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <div className="border p-3 rounded">
                  <div className="font-semibold text-red-600 mb-1">Next 14 Days</div>
                  <div className="text-xs">
                    Deals en stage <strong>Legals</strong><br/>
                    Closing imminent<br/>
                    <em>Target: $375K (ex)</em>
                  </div>
                </div>
                
                <div className="border p-3 rounded">
                  <div className="font-semibold text-orange-600 mb-1">30-60 Days</div>
                  <div className="text-xs">
                    Deals <strong>Proposal sent</strong><br/>
                    + POA récentes<br/>
                    <em>Target: $1.125M (ex)</em>
                  </div>
                </div>
                
                <div className="border p-3 rounded">
                  <div className="font-semibold text-yellow-600 mb-1">60-90 Days</div>
                  <div className="text-xs">
                    Leads chauds<br/>
                    Pipeline actif<br/>
                    <em>Target: $750K (ex)</em>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Upsell & Renew */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">🔄 Upsell & Renew - Performance Partners</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 p-3 rounded text-xs">
                <strong>Formule Partner Meetings:</strong><br/>
                Target mensuel × Période = Nombre de meetings attendus
              </div>
              
              <div className="border p-3 rounded text-xs">
                <strong>Métriques trackées:</strong>
                <ul className="list-disc ml-5 mt-2 space-y-1">
                  <li><strong>Intros:</strong> Introductions de nouveaux clients par partners</li>
                  <li><strong>POA:</strong> Meetings de présentation (Proof of Action)</li>
                  <li><strong>Upsells ARR:</strong> Chiffre d'affaires généré via partners</li>
                  <li><strong>Source:</strong> Client referral, Internal referral, External referral</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Schéma de flux */}
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-bold text-lg mb-3">🔄 Flux de Données - Vue d'Ensemble</h3>
            <div className="bg-gray-50 p-4 rounded font-mono text-xs">
              <div className="space-y-2">
                <div>1️⃣ <strong>Upload Google Sheet</strong> → Collection MongoDB (sales_records_[vue])</div>
                <div className="ml-4">↓</div>
                <div>2️⃣ <strong>Sélection Vue</strong> → Frontend envoie view_id</div>
                <div className="ml-4">↓</div>
                <div>3️⃣ <strong>Backend API</strong> → Lit collection + targets de la vue</div>
                <div className="ml-4">↓</div>
                <div>4️⃣ <strong>Calculs Analytics</strong> → Applique formules universelles</div>
                <div className="ml-4">↓</div>
                <div>5️⃣ <strong>Dashboard</strong> → Affiche résultats avec targets personnalisés</div>
              </div>
            </div>
          </div>

          {/* Résumé */}
          <Alert className="bg-green-50 border-green-300">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-900">
              <strong>✅ À retenir:</strong> En modifiant les targets ici, vous changez uniquement 
              les objectifs affichés. Les formules de calcul restent identiques pour toutes les vues. 
              C'est le principe du <strong>template universel</strong>!
            </AlertDescription>
          </Alert>

        </CardContent>
      )}
    </Card>
  );
}

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
