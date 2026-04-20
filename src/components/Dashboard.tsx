import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Clock, DollarSign, TrendingUp, AlertCircle } from 'lucide-react';

interface DashboardProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
  };
}

const mockAppointments = [
  { id: 1, time: '9:00 AM', patient: 'Sarah Johnson', provider: 'Dr. Smith', status: 'scheduled' },
  { id: 2, time: '9:30 AM', patient: 'Michael Chen', provider: 'Dr. Smith', status: 'scheduled' },
  { id: 3, time: '10:00 AM', patient: 'Emily Davis', provider: 'Dr. Williams', status: 'cancelled' },
  { id: 4, time: '10:30 AM', patient: 'James Wilson', provider: 'Dr. Smith', status: 'scheduled' },
  { id: 5, time: '11:00 AM', patient: 'Lisa Anderson', provider: 'Dr. Williams', status: 'scheduled' },
  { id: 6, time: '11:30 AM', patient: 'David Brown', provider: 'Dr. Smith', status: 'cancelled' },
  { id: 7, time: '1:00 PM', patient: 'Jennifer Lee', provider: 'Dr. Williams', status: 'scheduled' },
  { id: 8, time: '1:30 PM', patient: 'Robert Taylor', provider: 'Dr. Smith', status: 'scheduled' },
  { id: 9, time: '2:00 PM', patient: 'Amanda White', provider: 'Dr. Williams', status: 'scheduled' },
  { id: 10, time: '2:30 PM', patient: 'Christopher Martin', provider: 'Dr. Smith', status: 'cancelled' },
];

export default function Dashboard({ config }: DashboardProps) {
  const cancellationsToday = mockAppointments.filter(apt => apt.status === 'cancelled').length;
  const slotsFilled = 2;
  const recoveredRevenue = 340;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main Schedule Section */}
      <div className="lg:col-span-3">
        <Card>
          <CardHeader>
            <CardTitle>Today's Schedule - Sunday, October 12, 2025</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mockAppointments.map((apt) => (
                <div
                  key={apt.id}
                  className={`p-4 rounded-lg border ${
                    apt.status === 'cancelled'
                      ? 'bg-red-50 border-red-200'
                      : 'bg-white border-slate-200'
                  } transition-all hover:shadow-sm`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2 min-w-[80px]">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-700">{apt.time}</span>
                      </div>
                      <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                        <span className="text-slate-900">{apt.patient}</span>
                        <span className="text-slate-500 text-sm">
                          with {apt.provider.replace('Dr. ', `${config.providerLabel.includes('Dr') ? 'Dr. ' : ''}`)}
                          {!config.providerLabel.includes('Dr') && apt.provider.replace('Dr. ', '')}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {apt.status === 'cancelled' ? (
                        <>
                          <Badge variant="destructive" className="flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />
                            Cancelled
                          </Badge>
                          <Button size="sm" className="bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600">
                            Fill with Waitlist
                          </Button>
                        </>
                      ) : (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                          Scheduled
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* KPI Sidebar */}
      <div className="lg:col-span-1 space-y-4">
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-red-900">Cancellations Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl text-red-700">{cancellationsToday}</div>
            <p className="text-xs text-red-600 mt-1">3 slots available</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-green-900 flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              Slots Filled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl text-green-700">{slotsFilled}</div>
            <p className="text-xs text-green-600 mt-1">from waitlist today</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-teal-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-blue-900 flex items-center gap-1">
              <DollarSign className="w-4 h-4" />
              Recovered Revenue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl text-blue-700">${recoveredRevenue}</div>
            <p className="text-xs text-blue-600 mt-1">today</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
