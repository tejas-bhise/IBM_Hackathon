'use client';

import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

const mockDataExamples = [
  {
    type: 'Email Address',
    value: 'user@company.com',
    description: 'Personally Identifiable Information (PII)',
  },
  {
    type: 'Phone Number',
    value: '+1-555-123-4567',
    description: 'Contact Information',
  },
  {
    type: 'API Key',
    value: 'DEMO_STRIPE_KEY_REDACTED',
    description: 'Payment secret placeholder',
  },
  {
    type: 'Database Password',
    value: 'pgdb_prod_a7f9b2e4c1d6...',
    description: 'PostgreSQL Connection String (Masked)',
  },
  {
    type: 'JWT Token',
    value: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    description: 'Bearer Token (Masked)',
  },
  {
    type: 'OAuth Token',
    value: 'ghp_16C7e42F292c6912E7710c838347Ae178B4a...',
    description: 'GitHub Personal Access Token (Masked)',
  },
];

export function MockDataGenerator() {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const handleCopy = (value: string, id: number) => {
    navigator.clipboard.writeText(value);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="glass-panel rounded-xl p-6">
      <h3 className="text-lg font-semibold text-foreground mb-2">Sensitive Data Detection</h3>
      <p className="text-sm text-muted-foreground mb-6">
        Examples of sensitive information that should never be committed to version control:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockDataExamples.map((item, idx) => (
          <div key={idx} className="bg-background/70 rounded-lg border border-border p-4 hover:border-accent/50 hover:-translate-y-1 hover:shadow-[0_18px_44px_-34px_oklch(0.55_0.19_262.95_/_0.85)] transition-all duration-300">
            <h4 className="font-semibold text-foreground text-sm mb-1">{item.type}</h4>
            <p className="text-xs text-muted-foreground mb-3">{item.description}</p>

            <div className="bg-background rounded p-2 mb-3 border border-border/50">
              <code className="text-xs text-muted-foreground break-all">{item.value}</code>
            </div>

            <button
              onClick={() => handleCopy(item.value, idx)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-medium text-sm transition-colors border border-accent/20"
            >
              {copiedId === idx ? (
                <>
                  <Check size={16} /> Copied!
                </>
              ) : (
                <>
                  <Copy size={16} /> Copy
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-accent/10 rounded-lg border border-accent/20">
        <p className="text-sm text-foreground">
          <span className="font-semibold">Security Reminder:</span> Store all sensitive data in environment variables or secure configuration management systems. Never commit secrets to version control.
        </p>
      </div>
    </div>
  );
}
