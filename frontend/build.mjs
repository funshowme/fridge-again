import { existsSync, lstatSync, readdirSync, rmdirSync, unlinkSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { build } from 'vite';

/**
 * 在 Windows + OneDrive 同步目錄下，避免 Node 24 呼叫 fs.rmSync({ recursive: true })
 * 觸發重解析點例外（0xC0000409），改以標準逐檔刪除後再移除空目錄。
 */
function safeCleanDir(dirPath) {
  if (!existsSync(dirPath)) return;
  for (const entry of readdirSync(dirPath)) {
    const full = join(dirPath, entry);
    if (lstatSync(full).isDirectory()) {
      safeCleanDir(full);
      rmdirSync(full);
    } else {
      unlinkSync(full);
    }
  }
}

const distDir = resolve(import.meta.dirname, '..', 'dist');
safeCleanDir(distDir);

await build({
  configFile: resolve(import.meta.dirname, 'vite.config.js'),
});
