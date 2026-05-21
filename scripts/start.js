const { spawn } = require('child_process');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const backendScript = path.join(rootDir, 'scripts', 'start-backend.js');
const frontendDir = path.join(rootDir, 'speakit', 'frontend');

let shuttingDown = false;
const children = [];

function shutdown(code) {
  if (shuttingDown) {
    return;
  }

  shuttingDown = true;

  for (const child of children) {
    if (child && !child.killed) {
      child.kill();
    }
  }

  process.exit(code);
}

function launch(command, args, cwd, label) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
  });

  child.on('error', (error) => {
    console.error(`${label} failed to start: ${error.message}`);
    shutdown(1);
  });

  child.on('exit', (code) => {
    if (shuttingDown) {
      return;
    }

    if (code && code !== 0) {
      console.error(`${label} exited with code ${code}.`);
      shutdown(code);
      return;
    }

    shutdown(0);
  });

  return child;
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

children.push(launch(process.execPath, [backendScript], rootDir, 'Backend'));
children.push(launch('npm', ['start'], frontendDir, 'Frontend'));
