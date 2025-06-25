import React from 'react';
import { NavLink } from 'react-router-dom';

const navLinks = [
  { to: '/', label: 'Dashboard' },
  { to: '/client-overview', label: 'Client Overview' },
  { to: '/parsers', label: 'Parsers' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/comparison', label: 'Comparison' },
  { to: '/doc-teacher', label: 'Doc Teacher' },
  { to: '/case-review', label: 'Case Review' },
  { to: '/client-profile', label: 'Client Profile' },
  { to: '/settings', label: 'Settings' },
];

const Navigation: React.FC = () => (
  <aside className="w-64 bg-white border-r border-gray-200 p-6 flex flex-col min-h-screen">
    <h1 className="text-2xl font-bold mb-8 text-gray-900">TI Parser</h1>
    <nav className="flex-1 space-y-2">
      {navLinks.map(link => (
        <NavLink
          key={link.to}
          to={link.to}
          className={({ isActive }) =>
            `block px-3 py-2 rounded transition-colors duration-150 font-medium text-base ${
              isActive 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'
            }`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  </aside>
);

export default Navigation; 