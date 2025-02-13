import { Routes, Route, Link } from 'react-router-dom';

import Home from './pages/Home';
import Hub from './pages/authenticated/Hub';

import CostManagementHub from './pages/authenticated/cost_management/CostManagementHub';
import CostManagementAgent from './pages/authenticated/cost_management/CostManagementAgent';

import AgentManagementHub from './pages/authenticated/agent_management/AgentManagementHub';
import AgentManagementAgent from './pages/authenticated/agent_management/AgentManagementAgent';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/hub" element={<Hub />} />

      <Route path="/hub/cost-management" element={<CostManagementHub />} />
      <Route path="/cost-management/agent/:id" element={<CostManagementAgent />} />

      <Route path="/hub/agent-management" element={<AgentManagementHub />} />
      <Route path="/agent-management/agent/:id" element={<AgentManagementAgent />} />
    </Routes>
  );
}

export default App
