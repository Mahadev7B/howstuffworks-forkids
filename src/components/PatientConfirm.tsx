import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { CheckCircle2, Calendar, Clock, User, CreditCard, Shield } from 'lucide-react';

interface PatientConfirmProps {
  config: {
    primaryLabel: string;
    providerLabel: string;
  };
}

export default function PatientConfirm({ config }: PatientConfirmProps) {
  const [paymentComplete, setPaymentComplete] = useState(false);

  const handlePayment = () => {
    // Simulate payment processing
    setTimeout(() => {
      setPaymentComplete(true);
    }, 1000);
  };

  return (
    <div className="max-w-md mx-auto">
      {/* Mobile Device Frame */}
      <div className="bg-slate-900 rounded-[40px] p-4 shadow-2xl">
        <div className="bg-white rounded-[32px] overflow-hidden">
          {/* Status Bar */}
          <div className="bg-slate-50 px-6 py-2 flex justify-between items-center border-b">
            <span className="text-xs">9:41 AM</span>
            <div className="flex items-center gap-1">
              <div className="w-4 h-3 bg-slate-300 rounded-sm"></div>
              <div className="w-2 h-3 bg-slate-300 rounded-sm"></div>
              <div className="w-4 h-3 bg-slate-300 rounded-sm"></div>
            </div>
          </div>

          {/* App Header */}
          <div className="bg-gradient-to-r from-blue-500 to-teal-500 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <Calendar className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <div className="text-white">SoonerSwitch</div>
                <div className="text-xs text-blue-100">Confirm Your Appointment</div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6 min-h-[500px]">
            {!paymentComplete ? (
              <>
                {/* Success Badge */}
                <div className="flex justify-center">
                  <Badge className="bg-green-500 text-white px-4 py-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Slot Reserved for You!
                  </Badge>
                </div>

                {/* Appointment Details */}
                <Card className="border-2 border-blue-100">
                  <CardHeader>
                    <CardTitle className="text-base">Appointment Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-start gap-3">
                      <Calendar className="w-5 h-5 text-blue-500 mt-0.5" />
                      <div>
                        <div className="text-sm text-slate-600">Date</div>
                        <div className="text-slate-900">Sunday, October 12, 2025</div>
                      </div>
                    </div>

                    <Separator />

                    <div className="flex items-start gap-3">
                      <Clock className="w-5 h-5 text-blue-500 mt-0.5" />
                      <div>
                        <div className="text-sm text-slate-600">Time</div>
                        <div className="text-slate-900">3:10 PM</div>
                      </div>
                    </div>

                    <Separator />

                    <div className="flex items-start gap-3">
                      <User className="w-5 h-5 text-blue-500 mt-0.5" />
                      <div>
                        <div className="text-sm text-slate-600">{config.providerLabel}</div>
                        <div className="text-slate-900">Dr. Smith</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Deposit Info */}
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-sm text-blue-900">Refundable Deposit</div>
                        <p className="text-xs text-blue-700 mt-1">
                          A $10 deposit is required to secure this last-minute slot. It will be fully refunded when you attend your appointment.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Stripe Checkout Mockup */}
                <Card className="border-2 border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <CreditCard className="w-5 h-5" />
                      Payment Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm text-slate-600">Card Number</label>
                      <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                        <span className="text-slate-400">•••• •••• •••• 4242</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <label className="text-sm text-slate-600">Expiry</label>
                        <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                          <span className="text-slate-400">12/26</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm text-slate-600">CVC</label>
                        <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                          <span className="text-slate-400">•••</span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2">
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-slate-600">Deposit Amount</span>
                        <span className="text-slate-900">$10.00</span>
                      </div>
                      <Button
                        onClick={handlePayment}
                        className="w-full bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600"
                      >
                        Confirm & Pay $10.00
                      </Button>
                    </div>

                    <div className="flex items-center justify-center gap-2 pt-2">
                      <Shield className="w-4 h-4 text-slate-400" />
                      <span className="text-xs text-slate-500">Secured by Stripe</span>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              /* Confirmation Success */
              <div className="text-center space-y-6 py-8">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-12 h-12 text-green-600" />
                </div>

                <div>
                  <h3 className="text-slate-900 mb-2">You're All Set!</h3>
                  <p className="text-sm text-slate-600">
                    Your appointment is confirmed for Sunday, October 12 at 3:10 PM
                  </p>
                </div>

                <Card className="bg-blue-50 border-blue-200 text-left">
                  <CardContent className="pt-6">
                    <p className="text-sm text-blue-900">
                      ✓ Confirmation sent to your phone
                    </p>
                    <p className="text-sm text-blue-900 mt-2">
                      ✓ Calendar invite attached
                    </p>
                    <p className="text-sm text-blue-900 mt-2">
                      ✓ $10 deposit will be refunded at your appointment
                    </p>
                  </CardContent>
                </Card>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setPaymentComplete(false)}
                >
                  View Details
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
