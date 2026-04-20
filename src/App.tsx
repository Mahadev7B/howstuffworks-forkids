import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Calendar, Users, BarChart3, Settings as SettingsIcon, Smartphone } from 'lucide-react';
import Dashboard from './components/Dashboard';
import WaitlistManager from './components/WaitlistManager';
import Reports from './components/Reports';
import Settings from './components/Settings';
import PatientSMSFlow from './components/PatientSMSFlow';
import PatientConfirm from './components/PatientConfirm';

export default function App() {
  const [businessConfig, setBusinessConfig] = useState({
    primaryLabel: 'Patient',
    providerLabel: 'Dentist',
    requireDeposit: true,
    enablePriorityFee: false,
  });

  const [activeTab, setActiveTab] = useState('schedule');

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-teal-500 rounded-lg"></div>
              <span className="text-slate-900">SoonerSwitch</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-white border border-slate-200">
            <TabsTrigger value="schedule" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Schedule
            </TabsTrigger>
            <TabsTrigger value="waitlist" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Waitlist
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Reports
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <SettingsIcon className="w-4 h-4" />
              Settings
            </TabsTrigger>
            <TabsTrigger value="patient-sms" className="flex items-center gap-2">
              <Smartphone className="w-4 h-4" />
              Patient SMS
            </TabsTrigger>
            <TabsTrigger value="patient-confirm" className="flex items-center gap-2">
              <Smartphone className="w-4 h-4" />
              Patient PWA
            </TabsTrigger>
          </TabsList>

          <TabsContent value="schedule">
            <Dashboard config={businessConfig} />
          </TabsContent>

          <TabsContent value="waitlist">
            <WaitlistManager config={businessConfig} />
          </TabsContent>

          <TabsContent value="reports">
            <Reports config={businessConfig} />
          </TabsContent>

          <TabsContent value="settings">
            <Settings config={businessConfig} setConfig={setBusinessConfig} />
          </TabsContent>

          <TabsContent value="patient-sms">
            <PatientSMSFlow config={businessConfig} />
          </TabsContent>

          <TabsContent value="patient-confirm">
            <PatientConfirm config={businessConfig} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
