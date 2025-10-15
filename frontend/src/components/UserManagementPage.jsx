import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Users, UserPlus, Trash2, Shield, Eye, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function UserManagementPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [views, setViews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [newUser, setNewUser] = useState({
    email: '',
    role: 'viewer',
    view_access: []
  });

  useEffect(() => {
    loadUsers();
    loadViews();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        withCredentials: true
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
      setMessage({ type: 'error', text: 'Failed to load users' });
    } finally {
      setLoading(false);
    }
  };

  const loadViews = async () => {
    try {
      const response = await axios.get(`${API}/views`, {
        withCredentials: true
      });
      setViews(response.data);
    } catch (error) {
      console.error('Error loading views:', error);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    
    if (!newUser.email) {
      setMessage({ type: 'error', text: 'Email is required' });
      return;
    }

    try {
      await axios.post(`${API}/admin/users`, newUser, {
        withCredentials: true
      });
      
      setMessage({ type: 'success', text: `User ${newUser.email} added successfully!` });
      setNewUser({ email: '', role: 'viewer', view_access: [] });
      loadUsers();
    } catch (error) {
      console.error('Error adding user:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to add user' });
    }
  };

  const handleDeleteUser = async (email) => {
    if (!window.confirm(`Are you sure you want to delete user ${email}?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/users/${encodeURIComponent(email)}`, {
        withCredentials: true
      });
      
      setMessage({ type: 'success', text: `User ${email} deleted successfully!` });
      loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to delete user' });
    }
  };

  const handleUpdateUserViews = async (email, viewName, action) => {
    try {
      const targetUser = users.find(u => u.email === email);
      let newViewAccess = [...(targetUser.view_access || [])];
      
      if (action === 'add') {
        if (!newViewAccess.includes(viewName)) {
          newViewAccess.push(viewName);
        }
      } else if (action === 'remove') {
        newViewAccess = newViewAccess.filter(v => v !== viewName);
      }

      await axios.put(`${API}/admin/users/${encodeURIComponent(email)}`, {
        view_access: newViewAccess
      }, {
        withCredentials: true
      });
      
      loadUsers();
    } catch (error) {
      console.error('Error updating user views:', error);
      setMessage({ type: 'error', text: 'Failed to update user views' });
    }
  };

  const handleToggleRole = async (email, currentRole) => {
    const newRole = currentRole === 'super_admin' ? 'viewer' : 'super_admin';
    
    try {
      await axios.put(`${API}/admin/users/${encodeURIComponent(email)}`, {
        role: newRole
      }, {
        withCredentials: true
      });
      
      setMessage({ type: 'success', text: `User ${email} role updated to ${newRole}` });
      loadUsers();
    } catch (error) {
      console.error('Error updating role:', error);
      setMessage({ type: 'error', text: 'Failed to update user role' });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-gray-600">Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="h-8 w-8 text-blue-600" />
            User Management
          </h1>
          <p className="text-gray-600 mt-2">
            Manage users, permissions, and view access
          </p>
        </div>

        {/* Messages */}
        {message && (
          <Alert className={`mb-6 ${message.type === 'success' ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'}`}>
            {message.type === 'success' ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-red-600" />}
            <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {message.text}
            </AlertDescription>
          </Alert>
        )}

        {/* Add New User Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Add New User
            </CardTitle>
            <CardDescription>
              Create a new user and assign view permissions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddUser} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="user@primelis.com"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <select
                    id="role"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  >
                    <option value="viewer">Viewer</option>
                    <option value="super_admin">Super Admin</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <Button type="submit" className="w-full">
                    <UserPlus className="mr-2 h-4 w-4" />
                    Add User
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Users List */}
        <Card>
          <CardHeader>
            <CardTitle>Current Users ({users.length})</CardTitle>
            <CardDescription>
              Manage existing users and their permissions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {users.map((u) => (
                <div key={u.email} className="border rounded-lg p-4 bg-white">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{u.email}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          u.role === 'super_admin' 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {u.role === 'super_admin' ? <><Shield className="inline h-3 w-3 mr-1" />Super Admin</> : 'Viewer'}
                        </span>
                      </div>
                      
                      {/* View Access */}
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                          <Eye className="h-4 w-4" />
                          View Access:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {views.map((view) => {
                            const hasAccess = u.view_access?.includes(view.name);
                            return (
                              <button
                                key={view.id}
                                onClick={() => handleUpdateUserViews(u.email, view.name, hasAccess ? 'remove' : 'add')}
                                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                  hasAccess
                                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                              >
                                {hasAccess && <CheckCircle2 className="inline h-3 w-3 mr-1" />}
                                {view.name}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleRole(u.email, u.role)}
                      >
                        {u.role === 'super_admin' ? 'Remove Admin' : 'Make Admin'}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteUser(u.email)}
                        disabled={u.email === user?.email}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default UserManagementPage;
