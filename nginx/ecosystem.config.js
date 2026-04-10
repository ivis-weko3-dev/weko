module.exports = {
  apps: [
    {
      name: 'AMS',
      port: '3000',
      exec_mode: 'cluster',
      instances: 'max',
      script: '/usr/local/weko-frontend/.output/server/index.mjs',
      output: '/root/.pm2/logs/AMS-out.log',
      error: '/root/.pm2/logs/AMS-error.log',
      merge_logs: true
    }
  ]
}
