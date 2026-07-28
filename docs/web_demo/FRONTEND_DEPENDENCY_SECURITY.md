# Bảo mật dependency frontend

## 1. Phạm vi và mốc audit

- Ngày audit: `2026-07-27`.
- Runtime dùng để xác minh: system Node `v24.18.0`, npm `11.16.0`.
- Package manager contract: `npm@11.16.0`, lockfile version `3`.
- Phạm vi: `apps/web/`; không khởi động Next dev/start, backend, database, browser
  hoặc bất kỳ listener nào.
- Nguồn advisory: output `npm audit --json`, `npm audit --omit=dev --json` và
  GitHub Advisory Database. Audit JSON chỉ được giữ tạm ngoài Git rồi đã xóa.

Không dùng `npm audit fix`, `npm audit fix --force`, `npm update`, `--force`,
`--legacy-peer-deps`, range không pin hoặc blind override.

## 2. Dependency trước và sau hardening

| Dependency | Trước | Sau | Ghi chú |
| --- | --- | --- | --- |
| `next` | `14.2.26` | `15.5.21` | Exact Maintenance LTS security target. |
| `react` | `18.3.1` | `19.2.8` | Exact stable; khớp peer của Next và React DOM. |
| `react-dom` | `18.3.1` | `19.2.8` | Cùng version với React. |
| `@types/react` | `18.3.18` | `19.2.17` | Đồng bộ React 19. |
| `@types/react-dom` | `18.3.5` | `19.2.3` | Đồng bộ React DOM 19. |
| `@types/node` | `22.10.10` | `22.20.1` | Đáp ứng peer của Vite 7. |
| `eslint` | `8.57.1` | `10.8.0` | ESLint 9 vẫn kéo `minimatch@3`/`brace-expansion@1` high; chuyển sang native flat config sạch audit. |
| `eslint-config-next` | `14.2.26` | loại bỏ | Thay bằng direct Next plugin để không giữ legacy config/minimatch tree. |
| `@eslint/js` | chưa có | `10.0.1` | Native flat-config base. |
| `@next/eslint-plugin-next` | transitive `14.2.26` | direct `15.5.21` | Giữ Next recommended/core-web-vitals rules. |
| `eslint-plugin-react-hooks` | transitive `5.2.0` | direct `7.1.1` | React Hooks flat-config, hỗ trợ ESLint 10. |
| `typescript-eslint` | chưa có | `8.65.0` | Native TypeScript flat-config, hỗ trợ ESLint 10. |
| `vitest` | `2.1.8` | `3.2.6` | Exact patched version cho hai critical advisory. |

Engine Node đổi từ `>=18.17` thành
`^20.19.0 || ^22.13.0 || >=24`, khớp ESLint 10; system Node hiện tại đáp ứng.

## 3. Baseline audit

`npm audit` baseline ngày `2026-07-27` báo theo package-node:

- critical: `1`;
- high: `17`;
- moderate: `3`;
- low: `0`;
- tổng: `21`;
- production: critical `0`, high `2`, moderate `0`.

Con số `21` là số package-node bị đánh dấu, không phải số GHSA. Có `38` GHSA
riêng biệt trong các `via` object. Bảng dưới ghi affected range mà npm audit thấy
ở baseline và bản exact đã dùng để loại advisory.

### 3.1. Tooling và transitive advisories

| GHSA / CVE | Severity | Package và affected range | Class/path baseline | Reachability và quyết định |
| --- | --- | --- | --- | --- |
| `GHSA-mh99-v99m-4gvg` / `CVE-2026-14257` | high | `brace-expansion <=5.0.7`; có `1.1.16` | dev transitive: `eslint@8.57.1 -> minimatch@3.1.5 -> brace-expansion` và các plugin của `eslint-config-next` | Chỉ nhận glob từ repo trong lint nên remote reach thấp, nhưng chạy trong pipeline và là blocker. Loại legacy tree; final dùng `minimatch@10.2.5 -> brace-expansion@5.0.8`. |
| `GHSA-5j98-mcp5-4vw2` / `CVE-2025-64756` | high | `glob >=10.2.0 <10.5.0`; có `10.3.10` | dev transitive: `eslint-config-next@14.2.26 -> @next/eslint-plugin-next -> glob` | Không gọi `glob` CLI với input ngoài, nhưng dev high vẫn là blocker. Loại legacy config; final không còn package `glob`. |
| `GHSA-67mh-4wv8-2f99` / không có CVE | moderate | `esbuild <=0.24.2`; có `0.21.5` | dev transitive: `vitest@2.1.8 -> vite@5.4.21 -> esbuild` | Exploit cần Vite dev server; task chỉ dùng `vitest run`, không mở server. Vẫn nâng Vitest/Vite; final `esbuild@0.28.1`. |
| `GHSA-4w7w-66w2-5vf9` / `CVE-2026-39365` | moderate | các nhánh Vite tới `6.4.1`; baseline `5.4.21` | dev transitive: `vitest@2.1.8 -> vite@5.4.21` | Optimized-deps map path chỉ reachable khi Vite server xử lý request; không mở server. Nâng tới `vite@7.3.6` qua Vitest. |
| `GHSA-v6wh-96g9-6wx3` / `CVE-2026-53632` | moderate | các nhánh Vite tới `6.4.2`; baseline `5.4.21` | dev transitive: `vitest@2.1.8 -> vite@5.4.21` | UNC/launch-editor path không dùng trong `vitest run`, nhưng Windows dev tooling phải sạch. Nâng tới `vite@7.3.6`. |
| `GHSA-fx2h-pf6j-xcff` / `CVE-2026-53571` | high | các nhánh Vite tới `6.4.2`; baseline `5.4.21` | dev transitive: `vitest@2.1.8 -> vite@5.4.21` | Cần Vite server và alternate Windows path; không reachable trong finite test, nhưng dev high là blocker. Nâng tới `vite@7.3.6`. |
| `GHSA-9crc-q9x8-hgqq` / `CVE-2025-24964` | critical | `vitest >=2.0.0 <2.1.9`; có `2.1.8` | direct dev: `vitest@2.1.8` | RCE cần Vitest API server lắng nghe và user thăm site độc hại; task không chạy UI/API server. Critical vẫn bị cấm. Nâng `vitest@3.2.6`. |
| `GHSA-5xrq-8626-4rwp` / `CVE-2026-47429` | critical | các nhánh trước patched `3.2.6`; có `2.1.8` | direct dev: `vitest@2.1.8` | File read/execute cần Vitest UI server; không chạy UI, nhưng critical vẫn bị cấm. Nâng `vitest@3.2.6`. |

`vitest` không có install script. Transitive `esbuild` có postinstall, nhưng
advisory critical thuộc Vitest UI/API listener, không thuộc install hook. Final
`npm ci` chỉ báo policy warning cho install script của `esbuild@0.28.1`; không
thêm allow-list rộng, và finite Vitest/build gates vẫn pass.

### 3.2. PostCSS production advisories

| GHSA / CVE | Severity | Affected range | Class/path baseline | Reachability và quyết định |
| --- | --- | --- | --- | --- |
| `GHSA-qx2v-qp2m-jg93` / `CVE-2026-41305` | moderate | `postcss <8.5.10`; có `8.4.31` | production transitive: `next@14.2.26 -> postcss@8.4.31` | Build chỉ xử lý CSS tin cậy trong repo, nhưng dependency nằm trong production graph. |
| `GHSA-6g55-p6wh-862q` / `CVE-2026-45623` | high | `postcss <=8.5.11`; có `8.4.31` | cùng path | Attacker-controlled `sourceMappingURL` không có trong architecture hiện tại, nhưng production high là blocker. |
| `GHSA-r28c-9q8g-f849` / không có CVE | high | `postcss <=8.5.17`; có `8.4.31` | cùng path | Previous source-map auto-loading không nhận input ngoài ở build hiện tại, nhưng production high là blocker. |

Next `15.5.21` vẫn pin `postcss@8.4.31`, nên direct framework upgrade chưa đủ.
Override exact `postcss@8.5.23` được thêm sau khi audit chứng minh advisory còn tồn
tại. Đây là cùng major, hỗ trợ Node hiện tại, được dedupe cho Next/Vite và đã qua
`npm ci`, Vitest, typecheck, lint, production build.

### 3.3. Next.js baseline advisories

Mọi row sau là direct production path
`court-ocr-web -> next@14.2.26`. `fixAvailable` của npm yêu cầu thay direct
framework version; remediation áp dụng cho mọi row là exact `next@15.5.21`, được
audit lại bằng full và production audit.

| GHSA / CVE | Severity | Affected range npm baseline | Reachability trong application shell |
| --- | --- | --- | --- |
| `GHSA-3h52-269p-cp9r` / `CVE-2025-48068` | low | `>=13 <14.2.30` | Dev-server origin path; Codex không chạy dev server. |
| `GHSA-g5qg-72qw-gw5v` / `CVE-2025-57752` | moderate | `>=0.9.9 <14.2.31` | `next/image` không dùng; không trực tiếp reachable. |
| `GHSA-4342-x723-ch2f` / `CVE-2025-57822` | moderate | `>=0.9.9 <14.2.32` | Không có middleware, nhưng app có rewrite; xử lý trước local run. |
| `GHSA-xv57-4mr9-wg8v` / `CVE-2025-55173` | moderate | `>=0.9.9 <14.2.31` | `next/image` không dùng. |
| `GHSA-mwv6-3258-q52c` / không có CVE | high | `>=13.3 <14.2.34` | App Router/Server Components có dùng; production blocker. |
| `GHSA-5j59-xgg2-r9c4` / không có CVE | high | `>=13.3.1-canary <14.2.35` | App Router/Server Components có dùng; production blocker. |
| `GHSA-9g9p-9gw9-jx7f` / `CVE-2025-59471` | moderate | `>=10 <15.5.10` | `next/image`/remotePatterns không dùng. |
| `GHSA-h25m-26qc-wcjf` / không có CVE | high | `>=13 <15.0.8` | RSC có dùng; không dùng custom insecure deserializer nhưng vẫn là blocker. |
| `GHSA-ggv3-7p47-pfv8` / `CVE-2026-29057` | moderate | `>=9.5 <15.5.13` | Rewrite có dùng; production blocker cho đến khi nâng. |
| `GHSA-3x4c-7xq6-9pq8` / `CVE-2026-27980` | moderate | `>=10 <15.5.14` | `next/image` không dùng. |
| `GHSA-q4gf-8mx6-v5v3` / không có CVE | high | `>=13 <15.5.15` | App Router/Server Components có dùng; production blocker. |
| `GHSA-8h8q-6873-q5fj` / không có CVE | high | `>=13 <15.5.16` | App Router/Server Components có dùng; production blocker. |
| `GHSA-3g8h-86w9-wvmq` / `CVE-2026-44572` | low | `>=12.2 <15.5.16` | Không có middleware/proxy route. |
| `GHSA-ffhc-5mcf-pf4q` / `CVE-2026-44581` | moderate | `>=13.4 <15.5.16` | App Router có dùng nhưng CSP nonce không dùng. |
| `GHSA-vfv6-92ff-j949` / `CVE-2026-44582` | low | `>=13.4.6 <15.5.16` | RSC cache path có thể liên quan; xử lý trước local run. |
| `GHSA-gx5p-jg67-6x7h` / `CVE-2026-44580` | moderate | `>=13 <15.5.16` | `beforeInteractive` với input không tin cậy không dùng. |
| `GHSA-h64f-5h5j-jqjh` / `CVE-2026-44577` | moderate | `>=10 <15.5.16` | Image Optimization API không dùng. |
| `GHSA-c4j6-fc7j-m34r` / `CVE-2026-44578` | high | `>=13.4.13 <15.5.16` | Không dùng WebSocket upgrade, nhưng production high là blocker. |
| `GHSA-wfc6-r584-vfw7` / `CVE-2026-44576` | moderate | `>=14.2 <15.5.16` | App Router/RSC có dùng; production blocker. |
| `GHSA-36qx-fr4f-26g5` / `CVE-2026-44573` | high | `>=12.2 <15.5.16` | Pages Router i18n/middleware không dùng, nhưng production high là blocker. |
| `GHSA-m99w-x7hq-7vfj` / `CVE-2026-64641` | high | `>=13 <15.5.21` | App Router có dùng; Server Actions không dùng. Boundary `15.5.21` được chọn. |
| `GHSA-89xv-2m56-2m9x` / `CVE-2026-64649` | high | `>=14.1.1 <15.5.21` | Server Actions/custom server không dùng; production high vẫn là blocker. |
| `GHSA-68g3-v927-f742` / `CVE-2026-64648` | moderate | `>=13 <15.5.21` | Cache/request-body path không chủ động dùng; boundary `15.5.21`. |
| `GHSA-4633-3j49-mh5q` / `CVE-2026-64647` | moderate | `>=13 <15.5.21` | Cùng cache/request-body class; boundary `15.5.21`. |
| `GHSA-4c39-4ccg-62r3` / `CVE-2026-64646` | moderate | `>=13 <15.5.21` | Edge Server Actions không dùng; boundary `15.5.21`. |
| `GHSA-p9j2-gv94-2wf4` / `CVE-2026-64645` | high | `>=12 <15.5.21` | App có fixed loopback rewrite, không có attacker-controlled destination; production high vẫn là blocker. |
| `GHSA-955p-x3mx-jcvp` / `CVE-2026-64643` | moderate | `>=13 <15.5.21` | Server Functions/Actions không dùng; boundary `15.5.21`. |

## 4. Advisory phát hiện trong quá trình migration

Sau khi nâng direct dependencies nhưng trước override, audit còn:

- `GHSA-f88m-g3jw-g9cj`, high, optional production
  `next@15.5.21 -> sharp@0.34.5`, affected `<0.35.0`; advisory kế thừa
  `CVE-2026-33327`, `CVE-2026-33328`, `CVE-2026-35590`,
  `CVE-2026-35591` từ libvips. App không dùng `next/image`, nhưng production high
  là blocker. Next cho phép optional `sharp ^0.34.3`; override exact
  `sharp@0.35.0` yêu cầu Node `>=20.9.0` và đã qua build.
- Ba PostCSS GHSA ở mục 3.2 vì Next `15.5.21` vẫn pin `8.4.31`.
- `GHSA-mh99-v99m-4gvg` tiếp tục nằm trong ESLint 9 legacy tree. Không override
  `brace-expansion@5.0.8` mù vì API v5 khác API callable mà `minimatch@3` dùng.
  Thay vào đó loại tree cũ và dùng ESLint 10 native flat config.
- Khi thử `esbuild@0.27.7`, audit phát hiện
  `GHSA-g7r4-m6w7-qqqr` (low, không có CVE, range `>=0.27.3 <0.28.1`).
  Version thử nghiệm bị loại, final pin `esbuild@0.28.1`.

## 5. Overrides được chấp nhận

| Override exact | Lý do | Điều kiện gỡ |
| --- | --- | --- |
| `esbuild@0.28.1` | Vite cho phép `^0.27.0 || ^0.28.0`; tránh low advisory ở `0.27.7`. | Gỡ khi Vite/Vitest direct upgrade tự resolve bản sạch và `npm audit` + gates vẫn pass. |
| `postcss@8.5.23` | Next `15.5.21` pin vulnerable `8.4.31`; bản vá cùng major và Node-compatible. | Gỡ khi Next direct dependency dùng PostCSS `>8.5.17`. |
| `sharp@0.35.0` | Next optional range resolve `0.34.5` high; `0.35.0` là patched boundary. | Gỡ khi Next optional range tự resolve `>=0.35.0`. |

Không có override cho React/RSC, ESLint plugins, `minimatch` hoặc
`brace-expansion`. Không thêm RSC package trực tiếp; `npm ls` xác nhận không có
`react-server-dom-webpack`, `react-server-dom-turbopack` hoặc
`react-server-dom-parcel` độc lập trong dependency graph.

## 6. Migration source/config

- Ba App Router dynamic pages chuyển `params` sang `Promise<...>` và `await`
  đúng Next 15 request API contract.
- `.eslintrc.json` được thay hoàn toàn bởi `eslint.config.mjs`; không giữ hai
  nguồn cấu hình.
- Flat config giữ JS recommended, TypeScript recommended, React Hooks
  recommended và Next recommended/core-web-vitals; lint vẫn dùng
  `eslint . --max-warnings=0`.
- Không có `cookies`, `headers`, `draftMode`, `searchParams`, middleware,
  `next/image`, custom server hoặc Server Actions cần migration.
- Same-origin `/api/v1` rewrite và exact-loopback `WEB_API_ORIGIN` không đổi.

## 7. Audit và acceptance sau hardening

Kết quả cuối:

| Gate | Kết quả |
| --- | --- |
| `npm audit` | exit `0`; critical/high/moderate/low đều `0` |
| `npm audit --omit=dev` | exit `0`; critical/high/moderate/low đều `0` |
| `npm ci` | pass; 302 packages |
| Vitest | 6 files, 6 tests pass |
| TypeScript | pass |
| ESLint | pass, zero warning |
| Next build | pass; 13 business routes, 14 generated pages gồm `_not-found` |
| Python `tests/web` | 71 pass |
| Python full suite | 495 pass |

Build không gọi backend, không cần PostgreSQL và không mở port. Vitest lần đầu
trong sandbox bị chặn khi esbuild dò parent directory; cùng command finite chạy
ngoài filesystem sandbox pass. Đây không phải assertion/dependency failure và
không thay test script để che lỗi.

## 8. Cadence và deployment rule

- Chạy `npm ci`, `npm audit` và `npm audit --omit=dev` trước mỗi deployment.
- Chạy lại ngay khi Next, React/RSC, Vitest/Vite, PostCSS, sharp hoặc ESLint có
  security release.
- Review dependency security tối thiểu mỗi tháng trong thời gian demo active.
- Không public deploy khi full audit còn critical/high hoặc production audit còn
  critical/high/moderate.
- Không dùng `npm audit fix --force`; mọi direct upgrade/override phải pin exact,
  có dependency-path rationale, test và điều kiện gỡ.
- Local visual QA vẫn do Project Owner chạy; PASS security không cấp phép public
  deployment, authentication-free LAN bind hoặc wildcard CORS.
