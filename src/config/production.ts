/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Production Configuration - Supports ALL Checklist Items
 */

// Environment variable validation and defaults
const requiredEnvVars = [
  'VITE_DOMAIN_ROOT',
  'VITE_API_ENDPOINT',
] as const;

const optionalEnvVars = [
  'VITE_CHECKOUT_SOLO',
  'VITE_CHECKOUT_PRO', 
  'VITE_CHECKOUT_TEAM',
  'VITE_PAYMENT_PROVIDER',
  'VITE_PAYMENT_PUBLIC_KEY',
  'VITE_ANALYTICS_ENDPOINT',
  'VITE_SUPPORT_EMAIL',
  'VITE_STATUS_PAGE_URL',
  'VITE_ENVIRONMENT',
] as const;

// Validate required environment variables
const validateEnv = () => {
  const missing = requiredEnvVars.filter(
    varName => !import.meta.env[varName]
  );
  
  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing);
    if (import.meta.env.PROD) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }
};

// Run validation
validateEnv();

export const config = {
  // Environment
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,

  // Domain configuration (Checklist #1)
  domain: {
    root: import.meta.env.VITE_DOMAIN_ROOT || 'code.fisamy.work',
    protocol: 'https',
    workspace: (id: string) => `https://${id}.${import.meta.env.VITE_DOMAIN_ROOT || 'code.fisamy.work'}`,
  },

  // API endpoints (Checklist #5)
  api: {
    baseUrl: import.meta.env.VITE_API_ENDPOINT || 'https://api.code.fisamy.work',
    timeout: 10000,
    retries: 3,
    endpoints: {
      health: '/healthz',
      workspaces: '/api/workspaces',
      orders: '/api/orders',
      payments: '/api/payments',
      analytics: '/api/analytics',
      status: '/api/status',
    },
  },

  // Payment configuration (Checklist #10)
  payments: {
    provider: import.meta.env.VITE_PAYMENT_PROVIDER || 'shopee',
    publicKey: import.meta.env.VITE_PAYMENT_PUBLIC_KEY,
    checkoutUrls: {
      solo: import.meta.env.VITE_CHECKOUT_SOLO || 'https://checkout.shopee.my/solo',
      pro: import.meta.env.VITE_CHECKOUT_PRO || 'https://checkout.shopee.my/pro',
      team: import.meta.env.VITE_CHECKOUT_TEAM || 'https://checkout.shopee.my/team',
    },
    currency: 'RM',
  },

  // Authentication (Checklist #2)
  auth: {
    tokenKey: 'code_fisamy_token',
    sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours
    refreshThreshold: 60 * 60 * 1000, // 1 hour before expiry
  },

  // Monitoring & Analytics (Checklist #6)
  monitoring: {
    analyticsEndpoint: import.meta.env.VITE_ANALYTICS_ENDPOINT || '/api/analytics',
    enabled: import.meta.env.PROD || import.meta.env.VITE_ANALYTICS_ENABLED === 'true',
    batchSize: 10,
    flushInterval: 30000, // 30 seconds
    errorTracking: true,
    performanceTracking: true,
  },

  // Support & Contact (Checklist #8, #11)
  support: {
    email: import.meta.env.VITE_SUPPORT_EMAIL || 'support@code.fisamy.work',
    salesEmail: 'sales@code.fisamy.work',
    statusPage: import.meta.env.VITE_STATUS_PAGE_URL || 'https://status.code.fisamy.work',
    responseTime: '24 hours',
  },

  // Workspace configuration (Checklist #4, #9)
  workspaces: {
    plans: {
      solo: {
        cpu: '2 vCPU',
        memory: '4 GB',
        disk: '20 GB',
        idleTimeout: 45, // minutes
        maxConcurrent: 1,
      },
      pro: {
        cpu: '4 vCPU', 
        memory: '8 GB',
        disk: '40 GB',
        idleTimeout: 60, // minutes
        maxConcurrent: 2,
      },
      team: {
        cpu: '4 vCPU per seat',
        memory: '8 GB per seat',
        disk: '40 GB per seat',
        idleTimeout: 120, // minutes
        maxConcurrent: 4,
      },
    },
    limits: {
      diskWarningThreshold: 0.8, // 80%
      diskCriticalThreshold: 0.9, // 90%
      cpuThrottleThreshold: 0.8, // 80%
      memoryThrottleThreshold: 0.85, // 85%
    },
  },

  // Security settings (Checklist #3)
  security: {
    csp: {
      'default-src': ["'self'"],
      'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.tailwindcss.com'],
      'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.tailwindcss.com'],
      'img-src': ["'self'", 'data:', 'https:'],
      'connect-src': ["'self'", 'https://api.code.fisamy.work'],
    },
    hsts: {
      maxAge: 31536000, // 1 year
      includeSubDomains: true,
      preload: true,
    },
  },

  // Feature flags
  features: {
    statusPage: true,
    analytics: import.meta.env.PROD,
    adminInterface: import.meta.env.VITE_ADMIN_ENABLED === 'true',
    gpuPlans: import.meta.env.VITE_GPU_ENABLED === 'true',
    betaFeatures: import.meta.env.VITE_BETA_FEATURES === 'true',
  },

  // Legal compliance (Checklist #11)
  legal: {
    termsUrl: '/terms',
    privacyUrl: '/privacy',
    acceptableUseUrl: '/aup',
    dataRetentionDays: 365,
    jurisdiction: 'Malaysia',
    complianceStandards: ['PDPA', 'SOC2'],
  },

  // Deployment info (for debugging)
  deployment: {
    version: import.meta.env.VITE_VERSION || 'unknown',
    buildDate: import.meta.env.VITE_BUILD_DATE || new Date().toISOString(),
    commit: import.meta.env.VITE_COMMIT_HASH || 'unknown',
  },
} as const;

// Runtime configuration validation
export const validateConfig = () => {
  const errors: string[] = [];

  // Validate URLs
  try {
    new URL(`${config.domain.protocol}://${config.domain.root}`);
  } catch {
    errors.push('Invalid domain configuration');
  }

  try {
    new URL(config.api.baseUrl);
  } catch {
    errors.push('Invalid API base URL');
  }

  // Validate payment URLs
  Object.entries(config.payments.checkoutUrls).forEach(([plan, url]) => {
    try {
      new URL(url);
    } catch {
      errors.push(`Invalid checkout URL for ${plan} plan`);
    }
  });

  if (errors.length > 0 && config.isProduction) {
    throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
  }

  return errors;
};

// Auto-validate in production
if (config.isProduction) {
  validateConfig();
}

// Export individual sections for convenience
export const { 
  domain, 
  api, 
  payments, 
  auth, 
  monitoring, 
  support, 
  workspaces, 
  security, 
  features, 
  legal,
  deployment 
} = config;

// Debug helper (development only)
if (config.isDevelopment) {
  (window as any).__APP_CONFIG__ = config;
  console.log('🔧 Development mode: App config available at window.__APP_CONFIG__');
}
