import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/ui/Layout';
import Home from './pages/Home';
import WIParser from './pages/WIParser';
import ATParser from './pages/ATParser';
import ROAParser from './pages/ROAParser';
import TRTParser from './pages/TRTParser';
import Analysis from './pages/Analysis';
import Comparison from './pages/Comparison';
import ClientProfile from './pages/ClientProfile';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Data from './pages/Data';
import DocTeacherTab from './pages/DocTeacherTab';
import Parsers from './pages/Parsers';
import ClientOverview from './pages/ClientOverview';
import CaseReview from './pages/CaseReview';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/parsers" element={<Parsers />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/comparison" element={<Comparison />} />
            <Route path="/client-profile" element={<ClientProfile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/data" element={<Data />} />
            <Route path="/doc-teacher" element={<DocTeacherTab />} />
            <Route path="/client-overview" element={<ClientOverview />} />
            <Route path="/case-review" element={<CaseReview />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}
