const { spawn } = require('child_process');
const path = require('path');
const { resolvePython } = require('./python');

const rootDir = path.resolve(__dirname, '..');
const backendDir = path.join(rootDir, 'speakit', 'backend');
const python = resolvePython();

const child = spawn(python, ['app.py'], {
  cwd: backendDir,
  stdio: 'inherit',
});

child.on('exit', (code) => process.exit(code || 0));
child.on('error', (error) => {
  console.error(`Backend failed to start: ${error.message}`);
  process.exit(1);
});
