module.exports = {
  apps: [
    {
      name: 'agentpulse-collector',
      script: '/home/ernando/projects/agentpulse/packages/collector/start.sh',
      env: {
        PORT: 3000,
        DB_PATH: './data/agentpulse.db'
      }
    },
    {
      name: 'agentpulse-dashboard',
      cwd: '/home/ernando/projects/agentpulse/packages/dashboard',
      script: 'build/index.js',
      interpreter: 'node',
      env: {
        PORT: 5173,
        HOST: '0.0.0.0',
        VITE_API_URL: 'http://localhost:3000',
        VITE_API_KEY: 'ap_dev_default'
      }
    }
  ]
};
