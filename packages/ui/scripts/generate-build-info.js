#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get git commit SHA
let commitSha = 'unknown';
try {
  commitSha = execSync('git rev-parse --short HEAD', { encoding: 'utf8' }).trim();
} catch (error) {
  console.warn('Failed to get git commit SHA:', error.message);
}

// Get build timestamp
const buildTime = new Date().toISOString();

// Build info object
const buildInfo = {
  commitSha,
  buildTime,
  version: process.env.npm_package_version || '0.1.0',
};

// Write to public directory so it's served statically
const outputPath = path.join(__dirname, '..', 'public', 'build-info.json');
fs.writeFileSync(outputPath, JSON.stringify(buildInfo, null, 2));

console.log('Generated build info:', buildInfo);