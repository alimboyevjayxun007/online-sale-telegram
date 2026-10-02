/* Browser E2E (needs: backend + worker running with DEV_MOCK_PROVIDER=true, `pnpm dev`, seeded dev data).
   Env: BASE_URL, INIT_USER / INIT_OWNER (signed initData; `python -m app.cli dev-mock` prints one), BACKEND_DIR, BACKEND_ENV_FILE, CHROMIUM. */
import { chromium } from "playwright";
import fs from "fs";
const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const CHROMIUM = process.env.CHROMIUM ?? undefined; // optional: path to a Chromium binary
const read = (envName, file) => (process.env[envName] ?? fs.readFileSync(file, "utf8")).trim();
const owner = read("INIT_OWNER", process.env.INIT_OWNER_FILE ?? "init_owner.txt");
const user = read("INIT_USER", process.env.INIT_USER_FILE ?? "init_user.txt");
const browser = await chromium.launch({ executablePath: CHROMIUM, args: ["--no-sandbox"] });
const mk = async (init) => { const c = await browser.newContext({ viewport: { width: 390, height: 844 } }); await c.addInitScript((i) => localStorage.setItem("devInitData", i), init); await c.route("**/telegram.org/**", (r) => r.abort()); return c.newPage(); };
const ok = (c, m) => { console.log(c ? "PASS" : "FAIL", m); if (!c) process.exitCode = 1; };
const admin = await mk(owner), buyer = await mk(user);

// 1. non-admin cannot enter /admin
await buyer.goto(`${BASE}/admin`); await buyer.waitForTimeout(2500);
ok(!buyer.url().includes("/admin") || (await buyer.textContent("body")).includes("Salom"), "non-admin redirected away from /admin");

// 2. pricing change shows up in the user catalog
await admin.goto(`${BASE}/admin/pricing`); await admin.waitForSelector("[data-testid=markup-3]");
await admin.fill("[data-testid=markup-3]", "12"); await admin.click("[data-testid=save-3]"); await admin.waitForTimeout(1500);
await buyer.goto(`${BASE}/premium`); await buyer.waitForSelector("[data-testid=plan-3]");
const t3 = await buyer.textContent("[data-testid=plan-3]");
ok(t3.includes("13.65"), `3-month price after 12% markup: ${t3.match(/\d+\.\d\d \$/)?.[0]}`);   // 12.15*1.12=13.608 -> 13.65
await admin.fill("[data-testid=markup-3]", "8"); await admin.click("[data-testid=save-3]"); await admin.waitForTimeout(1200);

// 3. promo created in admin, applied by user
await admin.goto(`${BASE}/admin/promo`); await admin.waitForSelector("[data-testid=promo-code]");
await admin.fill("[data-testid=promo-code]", "UIPROMO"); await admin.fill("[data-testid=promo-value]", "3"); await admin.click("[data-testid=promo-create]"); await admin.waitForTimeout(1200);
ok((await admin.textContent("body")).includes("UIPROMO"), "promo listed in admin");
await buyer.goto(`${BASE}/premium`); await buyer.waitForSelector("[data-testid=plan-12]"); await buyer.click("[data-testid=plan-12]");
await buyer.getByText("Promokodingiz bormi?").click(); await buyer.fill("[data-testid=promo-input]", "uipromo"); await buyer.click("[data-testid=promo-apply]"); await buyer.waitForTimeout(1200);
const bodyText = await buyer.textContent("body");
ok(bodyText.includes("Promokod qo'llandi") && bodyText.includes("30.55"), "promo applied: 31.50 → 30.55 (3% , clamped to 0.01 grid)");

// 4. maintenance toggle blocks users, admin still works
await admin.goto(`${BASE}/admin/settings`); await admin.waitForSelector("[data-testid=maint-btn]");
await admin.click("[data-testid=maint-btn]"); await admin.getByText("Tasdiqlash").click(); await admin.waitForTimeout(1500);
await buyer.goto(`${BASE}/`); await buyer.waitForTimeout(2500);
ok((await buyer.textContent("body")).includes("Texnik ishlar"), "maintenance screen for users");
await admin.goto(`${BASE}/admin`); await admin.waitForTimeout(2500);
ok((await admin.textContent("body")).includes("Dashboard"), "admin still works during maintenance");
await admin.goto(`${BASE}/admin/settings`); await admin.waitForSelector("[data-testid=maint-btn]");
await admin.click("[data-testid=maint-btn]"); await admin.getByText("Tasdiqlash").click(); await admin.waitForTimeout(1500);
await buyer.goto(`${BASE}/`); await buyer.waitForTimeout(2000);
ok((await buyer.textContent("body")).includes("Salom"), "maintenance off → users back");

// 5. audit trail has the actions
await admin.goto(`${BASE}/admin/audit`); await admin.waitForTimeout(2000);
const audit = await admin.textContent("body");
ok(audit.includes("price.update") && audit.includes("promo.create") && audit.includes("settings.update"), "audit log recorded price/promo/settings changes");
await browser.close();
