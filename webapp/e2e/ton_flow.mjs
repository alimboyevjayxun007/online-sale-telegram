/* Browser E2E (needs: backend + worker running with DEV_MOCK_PROVIDER=true, `pnpm dev`, seeded dev data).
   Env: BASE_URL, INIT_USER / INIT_OWNER (signed initData; `python -m app.cli dev-mock` prints one), BACKEND_DIR, BACKEND_ENV_FILE, CHROMIUM. */
import { chromium } from "playwright";
import fs from "fs";
const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const CHROMIUM = process.env.CHROMIUM ?? undefined; // optional: path to a Chromium binary
const read = (envName, file) => (process.env[envName] ?? fs.readFileSync(file, "utf8")).trim();
import { execSync } from "child_process";
const init = read("INIT_USER", process.env.INIT_USER_FILE ?? "init_user.txt");
const out = process.env.SHOTS_DIR ?? "e2e-shots";
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROMIUM, args: ["--no-sandbox"] });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
await ctx.addInitScript((i) => localStorage.setItem("devInitData", i), init);
await ctx.route("**/telegram.org/**", (r) => r.abort());
const page = await ctx.newPage();
const ok = (c, m) => { console.log(c ? "PASS" : "FAIL", m); if (!c) process.exitCode = 1; };
await page.goto(`${BASE}/premium`);
await page.waitForSelector("[data-testid=plan-12]");
await page.click("[data-testid=plan-12]");
await page.click("[data-testid=method-ton]");
await page.fill("[data-testid=promo-input]", "x").catch(() => {});
await page.click("[data-testid=main-action]");
await page.waitForURL(/checkout\/PR-/);
await page.waitForSelector("[data-testid=amount]");
const amount = await page.textContent("[data-testid=amount]");
ok(/10\.50 TON/.test(amount), `TON amount shown: ${amount}`);
await page.getByText("Qo'lda to'lash").click();
await page.waitForTimeout(400);
const body = await page.textContent("body");
const comment = body.match(/PM-[A-Z0-9]{6}/)?.[0];
ok(!!comment, `comment visible: ${comment}`);
ok(body.includes("UQDevHotWallet"), "hot wallet address visible");
ok(/⏳ \d\d:\d\d qoldi/.test(body) || body.includes("qoldi"), "countdown visible");
await page.screenshot({ path: `${out}/user-ton-checkout.png` });
// simulate the on-chain transfer arriving (unique hash per run: duplicates are ignored by design)
const txHash = Array.from({ length: 64 }, () => "0123456789abcdef"[Math.floor(Math.random() * 16)]).join("");
const res = execSync(`cd ${process.env.BACKEND_DIR ?? "../backend"} && ${process.env.BACKEND_ENV_FILE ? `source ${process.env.BACKEND_ENV_FILE} &&` : ""} uv run python - <<'PY'
import asyncio
from decimal import Decimal
from app.core.db import session_maker, dispose_engine
from app.api.runtime import Services
from app.providers.ton.chain import IncomingTx
async def main():
    async with session_maker()() as s:
        svc = Services(s)
        print(await svc.checkout.payments.process_incoming(IncomingTx("${txHash}", 10**12, Decimal("10.5"), "${comment}", "UQsender")))
        await s.commit()
    await dispose_engine()
asyncio.run(main())
PY`, { shell: "/bin/bash" }).toString().trim();
ok(res.endsWith("confirmed"), `watcher result: ${res}`);
await page.waitForSelector("text=Tayyor!", { timeout: 20000 });
ok(true, "page progressed to 'Tayyor!' via polling");
await page.screenshot({ path: `${out}/user-ton-done.png` });
await browser.close();
