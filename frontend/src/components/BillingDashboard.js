import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BillingDashboard = ({ user, subscriptionInfo, onClose }) => {
  const [billingHistory, setBillingHistory] = useState(null);
  const [creditPacks, setCreditPacks] = useState({});
  const [subscriptionPlans, setSubscriptionPlans] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingPayment, setProcessingPayment] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      const [historyRes, packsRes, plansRes] = await Promise.all([
        axios.get(`${API}/payments/billing-history`),
        axios.get(`${API}/payments/credit-packs`),
        axios.get(`${API}/payments/subscription-plans`)
      ]);

      setBillingHistory(historyRes.data);
      setCreditPacks(packsRes.data.credit_packs);
      setSubscriptionPlans(plansRes.data.subscription_plans);
    } catch (error) {
      console.error('Error loading billing data:', error);
      setError('Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchaseCreditPack = async (packId) => {
    try {
      setProcessingPayment(true);
      setError('');

      const response = await axios.post(`${API}/payments/create-payment-link`, {
        product_id: packId,
        quantity: 1,
        user_email: user.email,
        customer_info: {
          fullName: user.name || user.email
        }
      });

      // Redirect to Dodo Payments checkout
      window.open(response.data.payment_link, '_blank');
      
    } catch (error) {
      console.error('Error creating payment:', error);
      setError(error.response?.data?.detail || 'Failed to create payment');
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleUpgradeToPro = async () => {
    try {
      setProcessingPayment(true);
      setError('');

      const response = await axios.post(`${API}/payments/create-subscription`, {
        plan_id: 'pro_monthly',
        user_email: user.email,
        customer_info: {
          fullName: user.name || user.email
        },
        billing_cycle: 'monthly'
      });

      // For subscriptions, we might get a checkout URL or handle differently
      if (response.data.checkout_url) {
        window.open(response.data.checkout_url, '_blank');
      } else {
        // Subscription created successfully
        alert('Subscription created successfully! Your account will be upgraded shortly.');
        loadBillingData();
      }
      
    } catch (error) {
      console.error('Error creating subscription:', error);
      setError(error.response?.data?.detail || 'Failed to create subscription');
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('Are you sure you want to cancel your Pro subscription? You will lose access to premium features.')) {
      return;
    }

    try {
      setProcessingPayment(true);
      await axios.post(`${API}/payments/cancel-subscription`);
      alert('Subscription cancelled successfully. You will retain Pro features until the end of your billing period.');
      loadBillingData();
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      setError(error.response?.data?.detail || 'Failed to cancel subscription');
    } finally {
      setProcessingPayment(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading billing information...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Billing & Subscription</h2>
            <p className="text-gray-600">Manage your getgingee subscription and billing</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        <div className="p-6 space-y-8">
          {/* Current Plan Section */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Current Plan */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Plan</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Plan:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    subscriptionInfo?.plan === 'pro' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {subscriptionInfo?.plan === 'pro' ? '💎 Full Plate' : '🆓 Lite Bite'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Credits:</span>
                  <span className="font-medium">{subscriptionInfo?.credits || 0}</span>
                </div>

                {subscriptionInfo?.plan === 'free' && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Decisions Used:</span>
                    <span className="font-medium">
                      {subscriptionInfo?.monthly_decisions_used || 0} / {subscriptionInfo?.monthly_limit || 3}
                    </span>
                  </div>
                )}

                {billingHistory?.active_subscription && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Next Billing:</span>
                    <span className="font-medium">
                      {formatDate(billingHistory.active_subscription.current_period_end)}
                    </span>
                  </div>
                )}
              </div>

              {subscriptionInfo?.plan === 'free' ? (
                <button
                  onClick={handleUpgradeToPro}
                  disabled={processingPayment}
                  className="w-full mt-4 gingee-gradient text-white py-3 px-6 rounded-lg hover:opacity-90 disabled:opacity-50 font-medium transition-all duration-200"
                >
                  {processingPayment ? 'Processing...' : 'Upgrade to Full Plate - $12/month'}
                </button>
              ) : (
                <button
                  onClick={handleCancelSubscription}
                  disabled={processingPayment}
                  className="w-full mt-4 bg-red-100 text-red-700 py-3 px-6 rounded-lg hover:bg-red-200 disabled:opacity-50 font-medium transition-all duration-200"
                >
                  {processingPayment ? 'Processing...' : 'Cancel Subscription'}
                </button>
              )}
            </div>

            {/* Billing Summary */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Summary</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Total Spent:</span>
                  <span className="font-medium text-lg">
                    {formatAmount(billingHistory?.total_spent || 0)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Payments:</span>
                  <span className="font-medium">{billingHistory?.payments?.length || 0}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Active Since:</span>
                  <span className="font-medium">
                    {billingHistory?.active_subscription 
                      ? formatDate(billingHistory.active_subscription.created_at)
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Credit Packs */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Buy Credit Packs</h3>
            <div className="grid md:grid-cols-3 gap-4">
              {Object.entries(creditPacks).map(([key, pack]) => (
                <div key={key} className={`bg-white border-2 rounded-xl p-6 relative ${
                  pack.popular ? 'border-purple-300 ring-2 ring-purple-100' : 'border-gray-200'
                }`}>
                  {pack.popular && (
                    <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                        BEST VALUE
                      </span>
                    </div>
                  )}
                  
                  <div className="text-center">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">{pack.name}</h4>
                    <div className="text-3xl font-bold text-gray-900 mb-1">
                      {formatAmount(pack.price)}
                    </div>
                    <p className="text-gray-600 mb-4">{pack.credits} credits</p>
                    <p className="text-sm text-gray-500 mb-6">{pack.description}</p>
                    
                    <button
                      onClick={() => handlePurchaseCreditPack(key)}
                      disabled={processingPayment}
                      className={`w-full py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                        pack.popular
                          ? 'bg-purple-600 text-white hover:bg-purple-700'
                          : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                      } disabled:opacity-50`}
                    >
                      {processingPayment ? 'Processing...' : 'Purchase'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Payment History */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment History</h3>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              {billingHistory?.payments?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Credits
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {billingHistory.payments.slice(0, 10).map((payment, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(payment.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {payment.product_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatAmount(payment.amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {payment.credits_amount || 0}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              payment.status === 'succeeded' ? 'bg-green-100 text-green-800' :
                              payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {payment.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <div className="text-4xl mb-4">💳</div>
                  <p className="text-lg font-medium mb-2">No payment history yet</p>
                  <p>Your payment history will appear here after your first purchase.</p>
                </div>
              )}
            </div>
          </div>

          {/* Subscription History */}
          {billingHistory?.subscriptions?.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Subscription History</h3>
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Plan
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Started
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {billingHistory.subscriptions.map((subscription, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {subscription.plan_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(subscription.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatAmount(subscription.amount)}/month
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              subscription.status === 'active' ? 'bg-green-100 text-green-800' :
                              subscription.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {subscription.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BillingDashboard;