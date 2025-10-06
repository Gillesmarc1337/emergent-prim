import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Sheet, AlertCircle, CheckCircle2, Link as LinkIcon } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function GoogleSheetsUpload({ onUploadSuccess }) {
  const [sheetUrl, setSheetUrl] = useState('');
  const [sheetName, setSheetName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!sheetUrl.trim()) {
      setUploadStatus({ 
        type: 'error', 
        message: 'URL requise', 
        details: 'Veuillez saisir l\'URL de votre Google Sheet' 
      });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    try {
      const response = await axios.post(`${API}/upload-google-sheets`, {
        sheet_url: sheetUrl,
        sheet_name: sheetName || null
      });

      setUploadStatus({ 
        type: 'success', 
        message: response.data.message,
        details: `${response.data.records_valid} enregistrements valides traités sur ${response.data.records_processed}` 
      });

      if (onUploadSuccess) {
        onUploadSuccess();
      }
      
      // Clear form on success
      setSheetUrl('');
      setSheetName('');
    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: 'Erreur lors de l\'import', 
        details: error.response?.data?.detail || error.message 
      });
    } finally {
      setIsUploading(false);
    }
  };

  const isValidGoogleSheetsUrl = (url) => {
    return url.includes('docs.google.com/spreadsheets') || url.includes('sheets.google.com');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sheet className="h-5 w-5 text-green-500" />
          Import Google Sheets
        </CardTitle>
        <CardDescription>
          Connectez directement votre Google Sheet pour importer les données.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="sheet-url" className="text-sm font-medium">
              URL du Google Sheet *
            </label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                id="sheet-url"
                type="url"
                placeholder="https://docs.google.com/spreadsheets/d/..."
                value={sheetUrl}
                onChange={(e) => setSheetUrl(e.target.value)}
                className="pl-10"
                disabled={isUploading}
              />
            </div>
            {sheetUrl && !isValidGoogleSheetsUrl(sheetUrl) && (
              <p className="text-sm text-orange-600">
                ⚠️ Assurez-vous que l'URL est bien celle d'un Google Sheet
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="sheet-name" className="text-sm font-medium">
              Nom de l'onglet (optionnel)
            </label>
            <Input
              id="sheet-name"
              type="text"
              placeholder="Feuille1, Data, etc..."
              value={sheetName}
              onChange={(e) => setSheetName(e.target.value)}
              disabled={isUploading}
            />
            <p className="text-xs text-gray-500">
              Laissez vide pour utiliser le premier onglet
            </p>
          </div>

          <div className="bg-blue-50 p-3 rounded-md">
            <h4 className="text-sm font-medium mb-2 text-blue-900">📋 Instructions :</h4>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>• Assurez-vous que votre Google Sheet est <strong>public</strong> ou partagé en lecture</li>
              <li>• Copiez l'URL complète depuis votre navigateur</li>
              <li>• Le sheet doit contenir les colonnes : Client, Discovery date, Stage, etc.</li>
            </ul>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              type="submit" 
              disabled={isUploading || !sheetUrl.trim()}
              className="flex-1"
            >
              {isUploading ? 'Import en cours...' : 'Importer les données'}
            </Button>
            {sheetUrl && isValidGoogleSheetsUrl(sheetUrl) && (
              <Badge variant="outline" className="text-green-600 border-green-600">
                ✓ URL valide
              </Badge>
            )}
          </div>
        </form>

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

export { GoogleSheetsUpload };