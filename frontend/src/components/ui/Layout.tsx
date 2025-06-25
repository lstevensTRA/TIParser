import React from 'react';
import Navigation from './Navigation';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen flex bg-gray-50">
    <Navigation />
    <main className="flex-1 p-8 overflow-y-auto">{children}</main>
  </div>
);

export default Layout; 