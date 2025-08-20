import React, { useState, useEffect } from 'react';
import './DomainManager.css';
import { safeLog, safeStringify, hasCircularReferences } from './src/utils/safeJson';

interface Domain {
  id: string;
  domain: string;
  status: 'pending' | 'verified' | 'active' | 'error';
  verification_method: string;
  verification_data: string;
  created_at: string;
  workspace_id: string;
}

interface DomainManagerProps {
  userId: string;
  workspaceId: string;
  domainManagerUrl: string;
}

const DomainManager: React.FC<DomainManagerProps> = ({ 
  userId, 
  workspaceId, 
  domainManagerUrl 
}) => {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [newDomain, setNewDomain] = useState('');
  const [verificationMethod, setVerificationMethod] = useState<'dns' | 'http' | 'file'>('dns');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch domains on component mount
  useEffect(() => {
    fetchDomains();
  }, [userId, workspaceId]);

  const fetchDomains = async () => {
    try {
      const response = await fetch(
        `${domainManagerUrl}/api/domains?userId=${userId}&workspaceId=${workspaceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setDomains(data);
      } else {
        setError('Failed to fetch domains');
      }
    } catch (err) {
      safeLog(err, 'Error fetching domains:');
      setError('Error fetching domains');
    }
  };

  const addDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomain.trim()) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${domainManagerUrl}/api/domains`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: newDomain.trim(),
          workspaceId,
          userId,
          verificationMethod,
        }),
      });

      if (response.ok) {
        const domain = await response.json();
        setDomains([domain, ...domains]);
        setNewDomain('');
        setSuccess(`Domain ${domain.domain} added successfully!`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to add domain');
      }
    } catch (err) {
      safeLog(err, 'Error adding domain:');
      setError('Error adding domain');
    } finally {
      setLoading(false);
    }
  };

  const verifyDomain = async (domainId: string) => {
    try {
      const response = await fetch(`${domainManagerUrl}/api/domains/${domainId}/verify`, {
        method: 'POST',
      });

      if (response.ok) {
        setSuccess('Domain verified successfully!');
        setTimeout(() => setSuccess(null), 5000);
        fetchDomains(); // Refresh the list
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Verification failed');
      }
    } catch (err) {
      safeLog(err, 'Error verifying domain:');
      setError('Error verifying domain');
    }
  };

  const deleteDomain = async (domainId: string) => {
    if (!confirm('Are you sure you want to delete this domain?')) return;

    try {
      const response = await fetch(`${domainManagerUrl}/api/domains/${domainId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setDomains(domains.filter(d => d.id !== domainId));
        setSuccess('Domain deleted successfully!');
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError('Failed to delete domain');
      }
    } catch (err) {
      safeLog(err, 'Error deleting domain:');
      setError('Error deleting domain');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'text-green-600';
      case 'pending':
        return 'text-yellow-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return '✅';
      case 'pending':
        return '⏳';
      case 'error':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="domain-manager">
      <div className="domain-manager-header">
        <h2>🌐 Custom Domains</h2>
        <p>Manage custom domains for your workspace</p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Add New Domain Form */}
      <div className="add-domain-form">
        <h3>Add New Domain</h3>
        <form onSubmit={addDomain}>
          <div className="form-group">
            <label htmlFor="domain">Domain Name:</label>
            <input
              type="text"
              id="domain"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="dev.company.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="verification">Verification Method:</label>
            <select
              id="verification"
              value={verificationMethod}
              onChange={(e) => setVerificationMethod(e.target.value as 'dns' | 'http' | 'file')}
            >
              <option value="dns">DNS (TXT Record)</option>
              <option value="http">HTTP Response</option>
              <option value="file">File Upload</option>
            </select>
          </div>

          <button 
            type="submit" 
            disabled={loading || !newDomain.trim()}
            className="btn btn-primary"
          >
            {loading ? 'Adding...' : 'Add Domain'}
          </button>
        </form>
      </div>

      {/* Domains List */}
      <div className="domains-list">
        <h3>Your Domains ({domains.length})</h3>
        
        {domains.length === 0 ? (
          <div className="no-domains">
            <p>No custom domains configured yet.</p>
            <p>Add a domain above to get started!</p>
          </div>
        ) : (
          <div className="domains-grid">
            {domains.map((domain) => (
              <div key={domain.id} className="domain-card">
                <div className="domain-header">
                  <h4>{domain.domain}</h4>
                  <span className={`status ${getStatusColor(domain.status)}`}>
                    {getStatusIcon(domain.status)} {domain.status}
                  </span>
                </div>

                <div className="domain-details">
                  <p><strong>Method:</strong> {domain.verification_method}</p>
                  <p><strong>Added:</strong> {new Date(domain.created_at).toLocaleDateString()}</p>
                </div>

                {domain.status === 'pending' && (
                  <div className="verification-info">
                    <h5>Verification Required</h5>
                    <div className="verification-steps">
                      {domain.verification_method === 'dns' && (
                        <div>
                          <p>Add this TXT record to your domain:</p>
                          <code className="verification-token">
                            {domain.verification_data}
                          </code>
                        </div>
                      )}
                      {domain.verification_method === 'http' && (
                        <div>
                          <p>Create a file at <code>/.well-known/domain-verification</code> containing:</p>
                          <code className="verification-token">
                            {domain.verification_data.split('should contain: ')[1]}
                          </code>
                        </div>
                      )}
                      {domain.verification_method === 'file' && (
                        <div>
                          <p>Create a file at <code>/.well-known/domain-verification.txt</code> containing:</p>
                          <code className="verification-token">
                            {domain.verification_data.split('should contain: ')[1]}
                          </code>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => verifyDomain(domain.id)}
                      className="btn btn-secondary"
                    >
                      Verify Domain
                    </button>
                  </div>
                )}

                <div className="domain-actions">
                  <button
                    onClick={() => deleteDomain(domain.id)}
                    className="btn btn-danger"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="help-section">
        <h3>Need Help?</h3>
        <div className="help-content">
          <div className="help-item">
            <h4>DNS Verification</h4>
            <p>Add a TXT record to your domain's DNS settings with the verification token.</p>
          </div>
          <div className="help-item">
            <h4>HTTP Verification</h4>
            <p>Create a file that returns the verification token when accessed.</p>
          </div>
          <div className="help-item">
            <h4>File Verification</h4>
            <p>Upload a text file containing the verification token.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainManager;
