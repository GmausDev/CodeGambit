import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ChallengeList from './pages/ChallengeList';
import ChallengeIDE from './pages/ChallengeIDE';
import Calibration from './pages/Calibration';

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <h2 className="text-2xl font-bold text-gray-200 mb-2">404 — Page Not Found</h2>
      <p className="text-gray-400 mb-4">The page you are looking for does not exist.</p>
      <Link
        to="/"
        className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/challenges" element={<ChallengeList />} />
          <Route path="/challenge/:id" element={<ChallengeIDE />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
