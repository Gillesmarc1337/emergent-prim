import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { LogOut, User, Eye, Settings, Users, ChevronDown } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const Header = () => {
  const { user, logout, currentView, setCurrentView, views, isAdmin, isDemo } = useAuth();

  const handleViewChange = (viewId) => {
    const selectedView = views.find(v => v.id === viewId);
    if (selectedView) {
      setCurrentView(selectedView);
    }
  };

  // Sort views in specific order for admins: Master / Full Funnel / Organic / Signal / Market
  const getSortedViews = () => {
    if (!views || views.length === 0) return [];
    
    const viewOrder = ['Master', 'Full Funnel', 'Organic', 'Signal', 'Market'];
    
    return [...views].sort((a, b) => {
      const indexA = viewOrder.indexOf(a.name);
      const indexB = viewOrder.indexOf(b.name);
      
      // If view is not in the order list, put it at the end
      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      
      return indexA - indexB;
    });
  };

  // Debug: Log views state
  console.log('Header - Views:', views, 'CurrentView:', currentView);

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Title */}
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">Sales Analytics Dashboard</h1>
          </div>

          {/* Right side - User info, View selector, Logout */}
          <div className="flex items-center gap-4">
            {/* View Selector - Always show if user is authenticated */}
            {user && (
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-gray-500" />
                {views.length > 0 ? (
                  <Select
                    value={currentView?.id || ''}
                    onValueChange={handleViewChange}
                  >
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select view" />
                    </SelectTrigger>
                    <SelectContent>
                      {getSortedViews().map((view) => (
                        <SelectItem key={view.id} value={view.id}>
                          {view.name}
                          {view.is_master && ' (Master)'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <span className="text-sm text-gray-500">Loading views...</span>
                )}
              </div>
            )}

            {/* Admin Dropdown (super_admin only) */}
            {isAdmin && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Settings className="h-4 w-4" />
                    Admin
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem asChild>
                    <a href="/admin/targets" className="flex items-center gap-2 cursor-pointer">
                      <Settings className="h-4 w-4" />
                      Targets Config
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <a href="/admin/users" className="flex items-center gap-2 cursor-pointer">
                      <Users className="h-4 w-4" />
                      User Management
                    </a>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* User Info */}
            {user && (
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                <User className="h-4 w-4 text-gray-500" />
                <div className="text-sm">
                  <div className="font-medium text-gray-900">
                    {user.name || user.email}
                    {isDemo && <span className="ml-2 text-amber-600">(Demo)</span>}
                  </div>
                  <div className="text-xs text-gray-500 capitalize">
                    {user.role?.replace('_', ' ') || 'User'}
                  </div>
                </div>
              </div>
            )}

            {/* Logout Button */}
            <Button
              onClick={logout}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
