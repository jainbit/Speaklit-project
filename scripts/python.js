const { spawnSync } = require('child_process');

function resolvePython() {
  const candidates = [process.env.SPEAKIT_PYTHON, 'python3', 'python'].filter(Boolean);

  for (const candidate of candidates) {
    const result = spawnSync(candidate, ['--version'], { stdio: 'ignore' });
    if (result.status === 0) {
      return candidate;
    }
  }

  throw new Error('Python was not found. Install Python 3 or set SPEAKIT_PYTHON to its executable path.');
}

module.exports = { resolvePython };
