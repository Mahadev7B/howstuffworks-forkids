import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Smartphone } from 'lucide-react';

interface PatientSMSFlowProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
  };
}

export default function PatientSMSFlow({ config }: PatientSMSFlowProps) {
  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="text-center space-y-2">
        <Smartphone className="w-12 h-12 mx-auto text-slate-400" />
        <h2 className="text-slate-900">Patient SMS Flow Preview</h2>
        <p className="text-sm text-slate-600">
          See how {config.primaryLabel.toLowerCase()}s experience the waitlist notifications
        </p>
      </div>

      {/* Phone Mockup */}
      <div className="bg-slate-900 rounded-[40px] p-4 shadow-2xl">
        <div className="bg-white rounded-[32px] overflow-hidden h-[600px] flex flex-col">
          {/* Status Bar */}
          <div className="bg-slate-50 px-6 py-2 flex justify-between items-center border-b">
            <span className="text-xs">9:41 AM</span>
            <div className="flex items-center gap-1">
              <div className="w-4 h-3 bg-slate-300 rounded-sm"></div>
              <div className="w-2 h-3 bg-slate-300 rounded-sm"></div>
              <div className="w-4 h-3 bg-slate-300 rounded-sm"></div>
            </div>
          </div>

          {/* Messages Header */}
          <div className="bg-slate-100 px-4 py-3 border-b flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-teal-500 rounded-full"></div>
            <div>
              <div className="text-sm">SoonerSwitch</div>
              <div className="text-xs text-slate-500">SMS</div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {/* Reminder Message */}
            <div className="flex flex-col items-start">
              <Badge variant="outline" className="mb-2 text-xs">
                Yesterday, 2:15 PM
              </Badge>
              <div className="bg-white rounded-2xl rounded-tl-sm p-3 shadow-sm max-w-[85%] border border-slate-200">
                <p className="text-sm text-slate-900">
                  Hi Sarah, your appointment with {config.providerLabel} Dr. Smith is at 3:30 PM tomorrow.
                </p>
                <p className="text-sm text-slate-900 mt-2">
                  Reply 1 to CONFIRM or 2 to CANCEL.
                </p>
              </div>
            </div>

            {/* User Reply */}
            <div className="flex flex-col items-end">
              <Badge variant="outline" className="mb-2 text-xs">
                Yesterday, 2:47 PM
              </Badge>
              <div className="bg-blue-500 rounded-2xl rounded-tr-sm p-3 shadow-sm max-w-[85%]">
                <p className="text-sm text-white">2</p>
              </div>
            </div>

            {/* Cancellation Confirmation */}
            <div className="flex flex-col items-start">
              <Badge variant="outline" className="mb-2 text-xs">
                Yesterday, 2:47 PM
              </Badge>
              <div className="bg-white rounded-2xl rounded-tl-sm p-3 shadow-sm max-w-[85%] border border-slate-200">
                <p className="text-sm text-slate-900">
                  Your appointment has been cancelled. No worries! You've been added to our priority waitlist.
                </p>
              </div>
            </div>

            {/* Slot Opening Offer */}
            <div className="flex flex-col items-start">
              <Badge variant="outline" className="mb-2 text-xs">
                Today, 9:38 AM
              </Badge>
              <div className="bg-gradient-to-r from-blue-500 to-teal-500 rounded-2xl rounded-tl-sm p-3 shadow-sm max-w-[85%]">
                <p className="text-sm text-white">
                  ⚡ Slot just opened at 3:10 PM today with {config.providerLabel} Dr. Smith!
                </p>
                <p className="text-sm text-white mt-2">
                  Reply MOVE to claim it (first to respond gets it!)
                </p>
              </div>
            </div>

            {/* User Response */}
            <div className="flex flex-col items-end">
              <Badge variant="outline" className="mb-2 text-xs">
                Today, 9:39 AM
              </Badge>
              <div className="bg-blue-500 rounded-2xl rounded-tr-sm p-3 shadow-sm max-w-[85%]">
                <p className="text-sm text-white">MOVE</p>
              </div>
            </div>

            {/* Confirmation with Deposit */}
            <div className="flex flex-col items-start">
              <Badge variant="outline" className="mb-2 text-xs">
                Today, 9:39 AM
              </Badge>
              <div className="bg-white rounded-2xl rounded-tl-sm p-3 shadow-sm max-w-[85%] border border-slate-200">
                <p className="text-sm text-slate-900">
                  🎉 You got the 3:10 PM slot!
                </p>
                <p className="text-sm text-slate-900 mt-2">
                  Please confirm with a $10 refundable deposit (returned at appointment):
                </p>
                <div className="mt-3 p-2 bg-blue-50 rounded-lg border border-blue-200">
                  <a
                    href="#"
                    className="text-sm text-blue-600 underline"
                    onClick={(e) => e.preventDefault()}
                  >
                    🔒 Secure payment link
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Message Input */}
          <div className="bg-white border-t px-4 py-3 flex items-center gap-2">
            <div className="flex-1 bg-slate-100 rounded-full px-4 py-2">
              <span className="text-sm text-slate-400">iMessage</span>
            </div>
            <div className="w-8 h-8 bg-slate-200 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
