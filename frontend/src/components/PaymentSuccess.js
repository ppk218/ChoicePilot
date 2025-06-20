import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const PaymentSuccess = ({ onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleContinue();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleContinue = () => {
    if (onClose) {
      onClose();
    } else {
      navigate('/');
    }
  };

  const getPaymentDetails = () => {
    const params = new URLSearchParams(location.search);
    return {
      paymentId: params.get('payment_id'),
      amount: params.get('amount'),
      status: params.get('status'),
      productName: params.get('product_name')
    };
  };

  const details = getPaymentDetails();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-card rounded-xl p-8 max-w-md w-full mx-4 text-center">
        {/* Success Icon */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        {/* Success Message */}
        <h2 className="text-2xl font-bold text-foreground mb-2">Payment Successful!</h2>
        <p className="text-muted-foreground mb-6">
          Your payment has been processed successfully. Your account will be updated shortly.
        </p>

        {/* Payment Details */}
        {details.paymentId && (
          <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold text-foreground mb-3">Payment Details</h3>
            <div className="space-y-2 text-sm">
              {details.productName && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Product:</span>
                  <span className="font-medium">{details.productName}</span>
                </div>
              )}
              {details.amount && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount:</span>
                  <span className="font-medium">${details.amount}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Payment ID:</span>
                <span className="font-mono text-xs">{details.paymentId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status:</span>
                <span className="text-green-600 font-medium">✓ Completed</span>
              </div>
            </div>
          </div>
        )}

        {/* Next Steps */}
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-900 mb-2">What's Next?</h3>
          <ul className="text-sm text-blue-800 space-y-1 text-left">
            <li>• Your credits will be added to your account automatically</li>
            <li>• You'll receive an email confirmation shortly</li>
            <li>• Premium features will be activated if you upgraded</li>
            <li>• You can start using ChoicePilot immediately</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleContinue}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
          >
            Continue to ChoicePilot
          </button>
          
          <p className="text-sm text-muted-foreground">
            Redirecting automatically in {countdown} seconds...
          </p>
        </div>

        {/* Support Link */}
        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            Need help? Contact{' '}
            <a href="mailto:support@choicepilot.ai" className="text-blue-600 hover:text-blue-800">
              support@choicepilot.ai
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccess;