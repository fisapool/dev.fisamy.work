/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Analytics Hook - Supports Checklist Item #6 (Monitoring & Metrics)
 */

import { useEffect, useCallback } from 'react';

interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
  timestamp?: Date;
}

interface AnalyticsConfig {
  endpoint?: string;
  userId?: string;
  sessionId?: string;
  enabled?: boolean;
}

class Analytics {
  private config: AnalyticsConfig;
  private queue: AnalyticsEvent[] = [];
  private sessionId: string;

  constructor(config: AnalyticsConfig = {}) {
    this.config = {
      enabled: true,
      endpoint: '/api/analytics',
      ...config,
    };
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  async track(event: string, properties: Record<string, any> = {}): Promise<void> {
    if (!this.config.enabled) return;

    const analyticsEvent: AnalyticsEvent = {
      event,
      properties: {
        ...properties,
        sessionId: this.sessionId,
        userId: this.config.userId,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
      },
      timestamp: new Date(),
    };

    // Add to queue for batch sending
    this.queue.push(analyticsEvent);

    // Send immediately for critical events, batch for others
    const criticalEvents = ['purchase', 'signup', 'error', 'workspace_created'];
    if (criticalEvents.includes(event)) {
      await this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.queue.length === 0 || !this.config.endpoint) return;

    const events = [...this.queue];
    this.queue = [];

    try {
      await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ events }),
      });
    } catch (error) {
      console.warn('Analytics tracking failed:', error);
      // Re-queue events if they failed to send
      this.queue.unshift(...events);
    }
  }

  // Business metrics specific to your service
  async trackPurchase(plan: string, amount: number, currency = 'RM'): Promise<void> {
    await this.track('purchase', {
      plan,
      amount,
      currency,
      revenue: amount,
    });
  }

  async trackWorkspaceAction(action: 'created' | 'started' | 'stopped' | 'suspended', workspaceId: string): Promise<void> {
    await this.track(`workspace_${action}`, {
      workspaceId,
      action,
    });
  }

  async trackResourceUsage(cpu: number, memory: number, disk: number): Promise<void> {
    await this.track('resource_usage', {
      cpu,
      memory,
      disk,
      timestamp: Date.now(),
    });
  }

  async trackError(error: Error, context?: Record<string, any>): Promise<void> {
    await this.track('error', {
      error: error.message,
      stack: error.stack,
      context,
    });
  }
}

const analytics = new Analytics();

export const useAnalytics = (config?: AnalyticsConfig) => {
  useEffect(() => {
    if (config) {
      Object.assign(analytics.config, config);
    }
  }, [config]);

  const track = useCallback(async (event: string, properties?: Record<string, any>) => {
    await analytics.track(event, properties);
  }, []);

  const trackPageView = useCallback(async (page?: string) => {
    await analytics.track('page_view', {
      page: page || window.location.pathname,
    });
  }, []);

  const trackPurchase = useCallback(async (plan: string, amount: number, currency = 'RM') => {
    await analytics.trackPurchase(plan, amount, currency);
  }, []);

  const trackWorkspace = useCallback(async (action: 'created' | 'started' | 'stopped' | 'suspended', workspaceId: string) => {
    await analytics.trackWorkspaceAction(action, workspaceId);
  }, []);

  const trackError = useCallback(async (error: Error, context?: Record<string, any>) => {
    await analytics.trackError(error, context);
  }, []);

  const flush = useCallback(async () => {
    await analytics.flush();
  }, []);

  // Auto-flush on page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      analytics.flush();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Periodic flush every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      analytics.flush();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    track,
    trackPageView,
    trackPurchase,
    trackWorkspace,
    trackError,
    flush,
  };
};
