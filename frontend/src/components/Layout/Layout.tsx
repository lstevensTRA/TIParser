import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { to: '/', label: 'Dashboard' },
  { to: '/wi-parser', label: 'WI Parser' },
  { to: '/at-parser', label: 'AT Parser' },
  { to: '/roa-parser', label: 'ROA Parser' },
  { to: '/trt-parser', label: 'TRT Parser' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/comparison', label: 'Comparison' },
  { to: '/client-profile', label: 'Client Profile' },
  { to: '/settings', label: 'Settings' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r p-6 flex flex-col">
        <h1 className="text-2xl font-bold mb-8">TI Parser</h1>
        <nav className="flex-1 space-y-2">
          {navLinks.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`block px-3 py-2 rounded transition-colors duration-150 font-medium text-base hover:bg-primary-100 hover:text-primary-700 ${
                location.pathname === link.to ? 'bg-blue-600 text-white' : 'text-gray-700'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </aside>
      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">{children}</main>
    </div>
  );
} 