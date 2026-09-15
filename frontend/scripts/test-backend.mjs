import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
const backend = path.resolve('../backend');
const venv = path.join(backend, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const child = spawn(existsSync(venv) ? venv : 'python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
  cwd: backend, stdio: 'inherit', env: {...process.env, COPYCAT_DATABASE_URL: 'sqlite:///./data/e2e.db', COPYCAT_STORAGE_ROOT: './data/e2e_uploads', COPYCAT_REPORT_ROOT: './data/e2e_reports', COPYCAT_FRONTEND_BASE_URL: 'http://127.0.0.1:3000', COPYCAT_CELERY_TASK_ALWAYS_EAGER: 'true'},
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill());
child.on('exit', code => process.exit(code ?? 0));
