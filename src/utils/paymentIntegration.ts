/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Payment Integration Utilities - Supports Checklist Item #10 (Payments & Billing)
 */

import { Plan } from '../types';

export interface PaymentProvider {
  name: 'shopee' | 'stripe' | 'billplz';
  publicKey?: string;
  webhookSecret?: string;
}

export interface PaymentRequest {
  plan: Plan;
  billingPeriod: 'monthly' | 'yearly';
  customerEmail: string;
  customerName?: string;
  successUrl?: string;
  cancelUrl?: string;
}

export interface PaymentResult {
  success: boolean;
  orderId?: string;
  paymentUrl?: string;
  error?: string;
}

class PaymentService {
  private provider: PaymentProvider;

  constructor(provider: PaymentProvider) {
    this.provider = provider;
  }

  /**
   * Create a payment session for the selected plan
   */
  async createPaymentSession(request: PaymentRequest): Promise<PaymentResult> {
    const amount = request.billingPeriod === 'monthly' 
      ? request.plan.priceMonthly 
      : request.plan.priceYearly;

    const orderData = {
      provider: this.provider.name,
      order_id: this.generateOrderId(request.plan.id),
      customer: {
        email: request.customerEmail,
        name: request.customerName,
      },
      line_items: [{
        sku: `${request.plan.id.toUpperCase()}-${request.billingPeriod === 'monthly' ? '1M' : '1Y'}`,
        name: `${request.plan.name} Plan (${request.billingPeriod})`,
        amount: amount,
        currency: 'RM',
        qty: 1,
      }],
      metadata: {
        plan_id: request.plan.id,
        billing_period: request.billingPeriod,
        cpu: request.plan.cpu,
        ram: request.plan.ram,
        storage: request.plan.storage,
      },
      success_url: request.successUrl || `${window.location.origin}/success`,
      cancel_url: request.cancelUrl || `${window.location.origin}/pricing`,
    };

    try {
      // In production, this would call your backend payment endpoint
      const response = await fetch('/api/payments/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      if (!response.ok) {
        throw new Error(`Payment creation failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      return {
        success: true,
        orderId: result.order_id,
        paymentUrl: result.payment_url,
      };
    } catch (error) {
      console.error('Payment creation failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Payment creation failed',
      };
    }
  }

  /**
   * Verify webhook signature for security
   */
  verifyWebhookSignature(payload: string, signature: string): boolean {
    if (!this.provider.webhookSecret) {
      console.warn('No webhook secret configured');
      return false;
    }

    // Implementation would depend on your payment provider
    // This is a placeholder for the actual verification logic
    return true;
  }

  /**
   * Handle webhook payload from payment provider
   */
  async handleWebhook(payload: any): Promise<void> {
    const { event_type, order_id, status, customer } = payload;

    switch (event_type) {
      case 'payment.completed':
        await this.handlePaymentSuccess(order_id, customer);
        break;
      case 'payment.failed':
        await this.handlePaymentFailure(order_id, customer);
        break;
      case 'subscription.cancelled':
        await this.handleSubscriptionCancellation(order_id, customer);
        break;
      default:
        console.warn(`Unhandled webhook event: ${event_type}`);
    }
  }

  private async handlePaymentSuccess(orderId: string, customer: any): Promise<void> {
    try {
      // Trigger workspace provisioning
      await fetch('/api/orders/provision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          customer,
          status: 'paid',
        }),
      });

      // Send welcome email
      await this.sendWelcomeEmail(customer.email, orderId);
    } catch (error) {
      console.error('Failed to handle payment success:', error);
      // Could trigger admin alert here
    }
  }

  private async handlePaymentFailure(orderId: string, customer: any): Promise<void> {
    console.log(`Payment failed for order ${orderId}`);
    // Could send payment failure email or retry logic
  }

  private async handleSubscriptionCancellation(orderId: string, customer: any): Promise<void> {
    try {
      // Mark workspace for suspension after grace period
      await fetch('/api/workspaces/schedule-suspension', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          customer,
          suspension_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days grace
        }),
      });
    } catch (error) {
      console.error('Failed to handle subscription cancellation:', error);
    }
  }

  private async sendWelcomeEmail(email: string, orderId: string): Promise<void> {
    try {
      await fetch('/api/emails/welcome', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: email,
          order_id: orderId,
          template: 'workspace_ready',
        }),
      });
    } catch (error) {
      console.error('Failed to send welcome email:', error);
    }
  }

  private generateOrderId(planId: string): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `${planId.toUpperCase()}-${timestamp}-${random}`;
  }
}

// Initialize with provider from environment
const getPaymentProvider = (): PaymentProvider => {
  const providerName = import.meta.env.VITE_PAYMENT_PROVIDER || 'shopee';
  
  return {
    name: providerName as 'shopee' | 'stripe' | 'billplz',
    publicKey: import.meta.env.VITE_PAYMENT_PUBLIC_KEY,
    webhookSecret: import.meta.env.VITE_PAYMENT_WEBHOOK_SECRET,
  };
};

export const paymentService = new PaymentService(getPaymentProvider());

/**
 * React hook for payment operations
 */
export const usePayments = () => {
  const createPayment = async (request: PaymentRequest): Promise<PaymentResult> => {
    return await paymentService.createPaymentSession(request);
  };

  const redirectToCheckout = async (plan: Plan, billingPeriod: 'monthly' | 'yearly', customerEmail: string) => {
    const result = await createPayment({
      plan,
      billingPeriod,
      customerEmail,
    });

    if (result.success && result.paymentUrl) {
      window.location.href = result.paymentUrl;
    } else {
      throw new Error(result.error || 'Payment creation failed');
    }
  };

  return {
    createPayment,
    redirectToCheckout,
  };
};
