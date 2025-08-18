const express = require('express');
const { Pool } = require('pg');
const axios = require('axios');
const dns = require('dns').promises;
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const cron = require('node-cron');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// Domain verification methods
class DomainVerifier {
  static async verifyDNS(domain, expectedValue) {
    try {
      const records = await dns.resolveTxt(domain);
      return records.flat().some(record => record.includes(expectedValue));
    } catch (error) {
      console.error(`DNS verification failed for ${domain}:`, error);
      return false;
    }
  }

  static async verifyHTTP(domain, path, expectedValue) {
    try {
      const response = await axios.get(`http://${domain}${path}`, {
        timeout: 10000,
        validateStatus: () => true
      });
      return response.data.includes(expectedValue);
    } catch (error) {
      console.error(`HTTP verification failed for ${domain}:`, error);
      return false;
    }
  }

  static async verifyFile(domain, filePath, expectedValue) {
    try {
      const response = await axios.get(`http://${domain}${filePath}`, {
        timeout: 10000,
        validateStatus: () => true
      });
      return response.data.trim() === expectedValue;
    } catch (error) {
      console.error(`File verification failed for ${domain}:`, error);
      return false;
    }
  }
}

// Caddy configuration generator
class CaddyConfigGenerator {
  static async generateDomainConfig(domain, workspaceId, targetPort = 3000) {
    const config = `${domain} {
  encode zstd gzip
  
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    X-XSS-Protection "1; mode=block"
    Referrer-Policy "strict-origin-when-cross-origin"
  }

  # Route to specific workspace
  reverse_proxy coder:3000 {
    header_up Host {host}
    header_up X-Workspace-ID ${workspaceId}
    flush_interval -1
  }
}`;

    const configPath = `/etc/caddy/custom-domains/${domain}.caddy`;
    await fs.writeFile(configPath, config);
    
    // Reload Caddy configuration
    await this.reloadCaddy();
  }

  static async removeDomainConfig(domain) {
    try {
      const configPath = `/etc/caddy/custom-domains/${domain}.caddy`;
      await fs.unlink(configPath);
      await this.reloadCaddy();
    } catch (error) {
      console.error(`Failed to remove domain config for ${domain}:`, error);
    }
  }

  static async reloadCaddy() {
    try {
      // Send reload signal to Caddy container
      const { exec } = require('child_process');
      exec('docker exec caddy caddy reload', (error, stdout, stderr) => {
        if (error) {
          console.error('Failed to reload Caddy:', error);
        } else {
          console.log('Caddy configuration reloaded successfully');
        }
      });
    } catch (error) {
      console.error('Failed to reload Caddy:', error);
    }
  }
}

// API Endpoints
app.post('/api/domains', async (req, res) => {
  try {
    const { domain, workspaceId, userId, verificationMethod = 'dns' } = req.body;
    
    if (!domain || !workspaceId || !userId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Validate domain format
    const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!domainRegex.test(domain)) {
      return res.status(400).json({ error: 'Invalid domain format' });
    }

    // Check if domain already exists
    const existingDomain = await pool.query(
      'SELECT id FROM custom_domains WHERE domain = $1',
      [domain]
    );

    if (existingDomain.rows.length > 0) {
      return res.status(409).json({ error: 'Domain already exists' });
    }

    // Generate verification token
    const verificationToken = uuidv4();
    
    // Insert domain record
    const result = await pool.query(
      `INSERT INTO custom_domains (domain, workspace_id, user_id, verification_token, verification_method)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [domain, workspaceId, userId, verificationToken, verificationMethod]
    );

    const newDomain = result.rows[0];

    // Generate verification data based on method
    let verificationData = '';
    switch (verificationMethod) {
      case 'dns':
        verificationData = `TXT record: ${domain} -> "${verificationToken}"`;
        break;
      case 'http':
        verificationData = `HTTP response at http://${domain}/.well-known/domain-verification should contain: ${verificationToken}`;
        break;
      case 'file':
        verificationData = `File at http://${domain}/.well-known/domain-verification.txt should contain: ${verificationToken}`;
        break;
    }

    // Insert verification record
    await pool.query(
      'INSERT INTO domain_verifications (domain_id, verification_type, verification_data) VALUES ($1, $2, $3)',
      [newDomain.id, verificationMethod, verificationData]
    );

    res.status(201).json({
      id: newDomain.id,
      domain: newDomain.domain,
      status: newDomain.status,
      verification_method: verificationMethod,
      verification_data: verificationData
    });

  } catch (error) {
    console.error('Error creating domain:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/domains/:id/verify', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Get domain and verification details
    const domainResult = await pool.query(
      'SELECT * FROM custom_domains WHERE id = $1',
      [id]
    );

    if (domainResult.rows.length === 0) {
      return res.status(404).json({ error: 'Domain not found' });
    }

    const domain = domainResult.rows[0];
    
    if (domain.status === 'verified') {
      return res.status(200).json({ message: 'Domain already verified' });
    }

    // Get verification details
    const verificationResult = await pool.query(
      'SELECT * FROM domain_verifications WHERE domain_id = $1 ORDER BY created_at DESC LIMIT 1',
      [id]
    );

    if (verificationResult.rows.length === 0) {
      return res.status(400).json({ error: 'No verification method found' });
    }

    const verification = verificationResult.rows[0];
    let isVerified = false;

    // Perform verification based on method
    switch (verification.verification_type) {
      case 'dns':
        isVerified = await DomainVerifier.verifyDNS(domain.domain, domain.verification_token);
        break;
      case 'http':
        isVerified = await DomainVerifier.verifyHTTP(domain.domain, '/.well-known/domain-verification', domain.verification_token);
        break;
      case 'file':
        isVerified = await DomainVerifier.verifyFile(domain.domain, '/.well-known/domain-verification.txt', domain.verification_token);
        break;
    }

    if (isVerified) {
      // Update domain status
      await pool.query(
        'UPDATE custom_domains SET status = $1, updated_at = NOW() WHERE id = $2',
        ['verified', id]
      );

      // Update verification record
      await pool.query(
        'UPDATE domain_verifications SET verified_at = NOW() WHERE id = $1',
        [verification.id]
      );

      // Generate Caddy configuration
      await CaddyConfigGenerator.generateDomainConfig(domain.domain, domain.workspace_id);

      res.json({ 
        message: 'Domain verified successfully',
        status: 'verified'
      });
    } else {
      res.status(400).json({ 
        error: 'Domain verification failed',
        verification_data: verification.verification_data
      });
    }

  } catch (error) {
    console.error('Error verifying domain:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/domains', async (req, res) => {
  try {
    const { userId, workspaceId, status } = req.query;
    let query = 'SELECT * FROM custom_domains WHERE 1=1';
    const params = [];
    let paramCount = 0;

    if (userId) {
      paramCount++;
      query += ` AND user_id = $${paramCount}`;
      params.push(userId);
    }

    if (workspaceId) {
      paramCount++;
      query += ` AND workspace_id = $${paramCount}`;
      params.push(workspaceId);
    }

    if (status) {
      paramCount++;
      query += ` AND status = $${paramCount}`;
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';

    const result = await pool.query(query, params);
    res.json(result.rows);

  } catch (error) {
    console.error('Error fetching domains:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.delete('/api/domains/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Get domain details before deletion
    const domainResult = await pool.query(
      'SELECT domain FROM custom_domains WHERE id = $1',
      [id]
    );

    if (domainResult.rows.length === 0) {
      return res.status(404).json({ error: 'Domain not found' });
    }

    const domain = domainResult.rows[0].domain;

    // Delete domain record (cascades to verifications and health)
    await pool.query('DELETE FROM custom_domains WHERE id = $1', [id]);

    // Remove Caddy configuration
    await CaddyConfigGenerator.removeDomainConfig(domain);

    res.json({ message: 'Domain deleted successfully' });

  } catch (error) {
    console.error('Error deleting domain:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', database: 'connected' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', database: 'disconnected' });
  }
});

// Scheduled domain health monitoring
cron.schedule('*/5 * * * *', async () => {
  console.log('Running domain health check...');
  
  try {
    const domains = await pool.query(
      'SELECT id, domain FROM custom_domains WHERE status = $1',
      ['verified']
    );

    for (const domain of domains.rows) {
      try {
        const startTime = Date.now();
        const response = await axios.get(`https://${domain.domain}`, {
          timeout: 10000,
          validateStatus: () => true
        });
        const responseTime = Date.now() - startTime;

        await pool.query(
          `INSERT INTO domain_health (domain_id, status_code, response_time_ms, ssl_valid, checked_at)
           VALUES ($1, $2, $3, $4, NOW())`,
          [domain.id, response.status, responseTime, true]
        );

      } catch (error) {
        await pool.query(
          `INSERT INTO domain_health (domain_id, status_code, response_time_ms, ssl_valid, checked_at)
           VALUES ($1, $2, $3, $4, NOW())`,
          [domain.id, null, null, false]
        );
      }
    }
  } catch (error) {
    console.error('Error in health check cron:', error);
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Domain Manager service running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await pool.end();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down gracefully...');
  await pool.end();
  process.exit(0);
});
