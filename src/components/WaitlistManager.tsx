import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { Send, CheckCircle2, Clock, Bell } from 'lucide-react';

interface WaitlistManagerProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
  };
}

const mockWaitlistData = [
  {
    id: 1,
    name: 'Maria Garcia',
    phone: '•••-•••-4521',
    preferences: 'Mornings, Dr. Smith',
    status: 'waiting',
  },
  {
    id: 2,
    name: 'Kevin Thompson',
    phone: '•••-•••-7832',
    preferences: 'Any time, Dr. Williams',
    status: 'notified',
  },
  {
    id: 3,
    name: 'Rachel Kim',
    phone: '•••-•••-9104',
    preferences: 'Afternoons',
    status: 'accepted',
  },
  {
    id: 4,
    name: 'Daniel Rodriguez',
    phone: '•••-•••-2367',
    preferences: 'Weekday mornings',
    status: 'waiting',
  },
  {
    id: 5,
    name: 'Ashley Turner',
    phone: '•••-•••-5689',
    preferences: 'Any availability',
    status: 'waiting',
  },
  {
    id: 6,
    name: 'Marcus Johnson',
    phone: '•••-•••-8901',
    preferences: 'Dr. Smith only',
    status: 'notified',
  },
];

export default function WaitlistManager({ config }: WaitlistManagerProps) {
  const [waitlistData, setWaitlistData] = useState(mockWaitlistData);

  const handleSendOffer = (id: number) => {
    setWaitlistData(prev =>
      prev.map(item =>
        item.id === id ? { ...item, status: 'notified' } : item
      )
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'waiting':
        return (
          <Badge variant="outline" className="flex items-center gap-1 w-fit">
            <Clock className="w-3 h-3" />
            Waiting
          </Badge>
        );
      case 'notified':
        return (
          <Badge className="flex items-center gap-1 w-fit bg-blue-500">
            <Bell className="w-3 h-3" />
            Notified
          </Badge>
        );
      case 'accepted':
        return (
          <Badge className="flex items-center gap-1 w-fit bg-green-500">
            <CheckCircle2 className="w-3 h-3" />
            Accepted
          </Badge>
        );
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Waitlist - {config.primaryLabel}s Ready for Appointments</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">
              {waitlistData.filter(p => p.status === 'waiting').length} waiting
            </span>
            <Button className="bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600">
              <Send className="w-4 h-4 mr-2" />
              Send Wave to All
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border border-slate-200 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead>Name</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Preferences</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {waitlistData.map((item) => (
                <TableRow
                  key={item.id}
                  className={item.status === 'accepted' ? 'bg-green-50' : ''}
                >
                  <TableCell>{item.name}</TableCell>
                  <TableCell className="text-slate-600">{item.phone}</TableCell>
                  <TableCell className="text-slate-600">{item.preferences}</TableCell>
                  <TableCell>{getStatusBadge(item.status)}</TableCell>
                  <TableCell className="text-right">
                    {item.status === 'waiting' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSendOffer(item.id)}
                        className="border-blue-200 text-blue-600 hover:bg-blue-50"
                      >
                        Send Offer
                      </Button>
                    )}
                    {item.status === 'notified' && (
                      <span className="text-sm text-slate-500">Awaiting response...</span>
                    )}
                    {item.status === 'accepted' && (
                      <span className="text-sm text-green-600">Slot claimed!</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
