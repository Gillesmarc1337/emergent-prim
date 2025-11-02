import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Button } from './ui/button';
import { LogOut, User, Eye, Settings, Users, ChevronDown, Moon, Sun, Menu, X } from 'lucide-react';
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
  const { isDarkMode, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    <div className="bg-white dark:bg-[#1a1d23] border-b border-gray-200 dark:border-[#2a2d35] shadow-sm sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Logo */}
          <div className="flex items-center">
            <img 
              src="/primelis-logo.jpg" 
              alt="Primelis Logo" 
              className="h-8 sm:h-10 w-auto object-contain"
            />
          </div>

          {/* Desktop view - Right side */}
          <div className="hidden lg:flex items-center gap-2 xl:gap-4">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="relative w-9 h-9 rounded-full hover:bg-slate-100 dark:hover:bg-[#24272e]"
              title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDarkMode ? (
                <Sun className="h-5 w-5 text-amber-500" />
              ) : (
                <Moon className="h-5 w-5 text-slate-700" />
              )}
            </Button>

            {/* View Selector */}
            {user && views.length > 0 && (
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <Select
                  value={currentView?.id || ''}
                  onValueChange={handleViewChange}
                >
                  <SelectTrigger className="w-[160px] xl:w-[200px]">
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
              </div>
            )}

            {/* Clear Cache Button */}
            {user && (
              <Button
                onClick={() => {
                  localStorage.clear();
                  sessionStorage.clear();
                  window.location.reload();
                }}
                variant="outline"
                size="sm"
                className="gap-2 text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-950"
              >
                🗑️ <span className="hidden xl:inline">Clear Cache</span>
              </Button>
            )}

            {/* Admin Dropdown */}
            {isAdmin && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Settings className="h-4 w-4" />
                    <span className="hidden xl:inline">Admin</span>
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
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-[#24272e] rounded-lg">
                <User className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <div className="text-sm">
                  <div className="font-medium text-gray-900 dark:text-white text-xs xl:text-sm">
                    {user.name || user.email}
                    {isDemo && <span className="ml-2 text-amber-600">(Demo)</span>}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
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
              <span className="hidden xl:inline">Logout</span>
            </Button>
          </div>

          {/* Mobile view - Hamburger menu */}
          <div className="flex lg:hidden items-center gap-2">
            {/* Theme Toggle Mobile */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="w-9 h-9"
            >
              {isDarkMode ? (
                <Sun className="h-5 w-5 text-amber-500" />
              ) : (
                <Moon className="h-5 w-5 text-slate-700" />
              )}
            </Button>

            {/* Hamburger Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="w-9 h-9"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 dark:border-[#2a2d35] py-4 space-y-3">
            {/* View Selector Mobile */}
            {user && views.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  View
                </label>
                <Select
                  value={currentView?.id || ''}
                  onValueChange={handleViewChange}
                >
                  <SelectTrigger className="w-full">
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
              </div>
            )}

            {/* User Info Mobile */}
            {user && (
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-[#24272e] rounded-lg">
                <User className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <div className="text-sm">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {user.name || user.email}
                    {isDemo && <span className="ml-2 text-amber-600">(Demo)</span>}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                    {user.role?.replace('_', ' ') || 'User'}
                  </div>
                </div>
              </div>
            )}

            {/* Clear Cache Mobile */}
            {user && (
              <Button
                onClick={() => {
                  localStorage.clear();
                  sessionStorage.clear();
                  window.location.reload();
                }}
                variant="outline"
                size="sm"
                className="w-full gap-2 text-blue-600 dark:text-blue-400"
              >
                🗑️ Clear Cache
              </Button>
            )}

            {/* Admin Links Mobile */}
            {isAdmin && (
              <div className="space-y-2">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Admin
                </label>
                <a 
                  href="/admin/targets" 
                  className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-[#24272e] rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-[#2a2d35]"
                >
                  <Settings className="h-4 w-4" />
                  Targets Config
                </a>
                <a 
                  href="/admin/users" 
                  className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-[#24272e] rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-[#2a2d35]"
                >
                  <Users className="h-4 w-4" />
                  User Management
                </a>
              </div>
            )}

            {/* Logout Mobile */}
            <Button
              onClick={logout}
              variant="outline"
              size="sm"
              className="w-full gap-2"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Header;
