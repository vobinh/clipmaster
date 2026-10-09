#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

// Ensure ~/.cargo/bin is in PATH for environments where terminal hasn't loaded ~/.cargo/env
const cargoBin = path.join(os.homedir(), '.cargo', 'bin');
const env = { ...process.env };
if (cargoBin && !env.PATH.includes(cargoBin)) {
  env.PATH = `${cargoBin}${path.delimiter}${env.PATH}`;
}

const args = process.argv.slice(2);
const isWindows = process.platform === 'win32';
const cmd = isWindows ? 'npx.cmd' : 'npx';

const child = spawn(cmd, ['@tauri-apps/cli', ...args], {
  stdio: 'inherit',
  shell: true,
  env
});

child.on('exit', (code) => {
  process.exit(code !== null ? code : 0);
});
