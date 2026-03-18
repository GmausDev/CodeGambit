import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ChallengeList from './pages/ChallengeList';
import ChallengeIDE from './pages/ChallengeIDE';
import Calibration from './pages/Calibration';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/challenges" element={<ChallengeList />} />
          <Route path="/challenge/:id" element={<ChallengeIDE />} />
          <Route path="/calibration" element={<Calibration />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
