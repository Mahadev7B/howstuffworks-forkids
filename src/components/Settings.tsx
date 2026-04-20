import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { Save } from 'lucide-react';

interface SettingsProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
    requireDeposit: boolean;
    enablePriorityFee: boolean;
  };
  setConfig: (config: any) => void;
}

export default function Settings({ config, setConfig }: SettingsProps) {
  const handleSave = () => {
    // In a real app, this would save to backend
    alert('Settings saved successfully!');
  };

  return (
    <div className="max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Business Configuration</CardTitle>
          <CardDescription>
            Customize labels and terminology to match your business type
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="primary-label">Primary Label (e.g., Patient/Client/Student)</Label>
            <Input
              id="primary-label"
              value={config.primaryLabel}
              onChange={(e) => setConfig({ ...config, primaryLabel: e.target.value })}
              placeholder="Patient"
            />
            <p className="text-xs text-slate-500">
              This label will be used throughout the app to refer to your customers
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="provider-label">Provider Label (e.g., Dentist/Stylist/Tutor)</Label>
            <Input
              id="provider-label"
              value={config.providerLabel}
              onChange={(e) => setConfig({ ...config, providerLabel: e.target.value })}
              placeholder="Dentist"
            />
            <p className="text-xs text-slate-500">
              This label will be used to refer to your service providers
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appointment Policies</CardTitle>
          <CardDescription>
            Configure how short-notice appointments and cancellations are handled
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
            <div className="space-y-1 flex-1">
              <Label htmlFor="require-deposit" className="cursor-pointer">
                Require deposit on short-notice reschedules
              </Label>
              <p className="text-xs text-slate-500">
                Charge a refundable deposit when {config.primaryLabel.toLowerCase()}s accept last-minute slots
              </p>
            </div>
            <Switch
              id="require-deposit"
              checked={config.requireDeposit}
              onCheckedChange={(checked) =>
                setConfig({ ...config, requireDeposit: checked })
              }
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
            <div className="space-y-1 flex-1">
              <Label htmlFor="priority-fee" className="cursor-pointer">
                Enable priority fee for earlier slots
              </Label>
              <p className="text-xs text-slate-500">
                Allow {config.primaryLabel.toLowerCase()}s to pay extra to get priority access to opened slots
              </p>
            </div>
            <Switch
              id="priority-fee"
              checked={config.enablePriorityFee}
              onCheckedChange={(checked) =>
                setConfig({ ...config, enablePriorityFee: checked })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notification Settings</CardTitle>
          <CardDescription>
            Configure how and when waitlist notifications are sent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sms-template">SMS Template</Label>
            <textarea
              id="sms-template"
              className="w-full min-h-[100px] p-3 rounded-md border border-slate-200 text-sm"
              defaultValue="Hi {name}, a slot just opened at {time}. Reply MOVE to claim it!"
            />
            <p className="text-xs text-slate-500">
              Available variables: {'{name}'}, {'{time}'}, {'{provider}'}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          className="bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600"
        >
          <Save className="w-4 h-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  );
}
