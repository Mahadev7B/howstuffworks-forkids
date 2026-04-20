import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { DollarSign, TrendingDown, Clock, Calendar } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ReportsProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
  };
}

const chartData = [
  { name: 'Mon', cancellations: 4, filled: 3 },
  { name: 'Tue', cancellations: 3, filled: 2 },
  { name: 'Wed', cancellations: 5, filled: 4 },
  { name: 'Thu', cancellations: 2, filled: 2 },
  { name: 'Fri', cancellations: 6, filled: 5 },
  { name: 'Sat', cancellations: 1, filled: 1 },
  { name: 'Sun', cancellations: 3, filled: 2 },
];

export default function Reports({ config }: ReportsProps) {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-slate-600 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Recovered Revenue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-slate-900">$2,480</div>
            <p className="text-xs text-slate-500 mt-1">This month</p>
            <div className="mt-2 text-xs text-green-600">+18% vs last month</div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-teal-500">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-slate-600 flex items-center gap-2">
              <TrendingDown className="w-4 h-4" />
              No-Show Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-slate-900">3.2%</div>
            <p className="text-xs text-slate-500 mt-1">Down from 8.5%</p>
            <div className="mt-2 text-xs text-green-600">-62% improvement</div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-slate-600 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Avg Fill Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-slate-900">23 min</div>
            <p className="text-xs text-slate-500 mt-1">From cancellation</p>
            <div className="mt-2 text-xs text-green-600">Excellent</div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-slate-600 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Slots Filled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-slate-900">19</div>
            <p className="text-xs text-slate-500 mt-1">This month</p>
            <div className="mt-2 text-xs text-blue-600">76% fill rate</div>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cancellations vs Filled Slots - Last 7 Days</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="cancellations" fill="#ef4444" name="Cancellations" radius={[4, 4, 0, 0]} />
              <Bar dataKey="filled" fill="#10b981" name="Filled from Waitlist" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Performing {config.providerLabel}s</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-700">Dr. Williams</span>
                <span className="text-slate-900">12 slots filled</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-700">Dr. Smith</span>
                <span className="text-slate-900">7 slots filled</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Peak Cancellation Times</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-700">10:00 AM - 12:00 PM</span>
                <span className="text-red-600">8 cancellations</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-700">2:00 PM - 4:00 PM</span>
                <span className="text-red-600">6 cancellations</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
