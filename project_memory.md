# PROJECT MEMORY — Airdrop Intelligence Bot

> File này là nguồn sự thật (source of truth) về tiến độ project.
> Luôn đọc file này trước khi làm task mới. Cập nhật sau mỗi phần việc lớn.

## Mục tiêu tổng
AI Research Assistant cho airdrop hunter, chạy free trên GitHub Actions,
gửi thông báo qua Telegram. Không dùng DB (chỉ JSON), zero-cost infra.

## Quy ước làm việc (bắt buộc)
- Đọc file này trước khi bắt đầu bất kỳ task nào.
- Thay đổi nhỏ, từng bước, không dồn logic vào 1 file lớn.
- Sau mỗi phần việc lớn (crawler xong, telegram xong, v.v.) → cập nhật file này
  (đã làm gì / quyết định gì / còn lại gì / bước tiếp theo) VÀ NHẮC user cập nhật/confirm.
- KHÔNG xoá / dọn file gì mà chưa hỏi ý kiến user trước.
- Giao tiếp bằng tiếng Việt cho phần code.

## Kiến trúc
```
src/
  crawler/   -> mỗi nguồn 1 file, trả về list[dict] thô, lỗi thì log + return [] (không raise)
  parser/    -> chuẩn hóa dict thô -> Project (pydantic model)
  scorer/    -> ProjectScorer interface (rule-based, V2)
  ai/        -> AIProvider interface + GeminiProvider (V3)
  telegram/  -> gửi notification
  models/    -> Project, ProjectScore, AIScore (pydantic, single source of truth)
  utils/     -> logger, config (.env loader), http_client (retry/timeout), json_store (atomic r/w)
data/
  projects.json  -> kết quả crawl lần gần nhất (toàn bộ project đang active)
  history.json   -> danh sách unique_id đã từng gửi Telegram (chống gửi trùng)
  config.json    -> bật/tắt từng nguồn crawl
```

Luồng chạy chính (main.py, sẽ code ở phase sau):
`crawl (nhiều nguồn, lỗi nguồn nào bỏ qua nguồn đó) -> parse -> dedupe/merge
-> filter theo history.json -> [optional] score (rule-based) -> [optional] AI score (Gemini)
-> gửi Telegram cho project mới -> ghi lại projects.json + history.json`

## Trạng thái: ĐÃ LÀM

### Phase 1 — Scaffold + Core Foundation ✅ (xong)
- Cấu trúc thư mục đầy đủ theo spec (`src/{crawler,parser,scorer,ai,telegram,models,utils}`, `data/`, `tests/`, `.github/workflows/`).
- `pyproject.toml`: deps chính (httpx, requests, beautifulsoup4, feedparser, pydantic, python-dotenv, tenacity, google-genai) + dev (pytest).
- `.env.example`: đầy đủ config (Telegram, Gemini, AI provider switch, HTTP timeout/retry, log level). Không hardcode gì trong code.
- `.gitignore`: ignore `.env`, cache, venv. **KHÔNG** ignore `data/*.json` vì đó là state cần commit lại (giống pattern `known_codes.json` ở project genshin-giftcode-notifier).
- `src/models/project.py`: pydantic models — `Project`, `ProjectCategory`, `ProjectSource`, `ProjectScore` (V2 rule-based), `AIScore` (V3 Gemini). `Project.dedupe_key` / `unique_id` dùng cho merge + chống gửi trùng.
- `src/utils/logger.py`: logging tập trung, không print, đọc `LOG_LEVEL` từ env.
- `src/utils/config.py`: `Settings` (pydantic) load từ `.env`, fail-fast nếu thiếu `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`, validate nếu bật AI scoring mà thiếu `GEMINI_API_KEY`. Cache qua `lru_cache`.
- `src/utils/http_client.py`: `fetch_text` / `fetch_json` dùng `httpx` + `tenacity` retry (exponential backoff, chỉ retry lỗi timeout/connect), timeout lấy từ config.
- `src/utils/json_store.py`: `read_json` / `write_json` ghi atomic (tmp file + rename) để tránh corrupt data nếu job bị GitHub Actions kill giữa chừng.
- `data/{projects,history}.json` khởi tạo `[]`, `data/config.json` khởi tạo bật cả 4 nguồn.
- `tests/test_models.py`: 3 test cơ bản cho `Project` model — **đã chạy pass (3 passed)**.

### Quyết định kỹ thuật quan trọng
- Dùng `google-genai` (SDK Gemini mới, thống nhất) thay vì `google-generativeai` cũ.
- `ProjectScore` (rule-based, V2) tách riêng khỏi `AIScore` (Gemini, V3) — rule-based không tốn API call, chạy được ngay cả khi `ENABLE_AI_SCORING=false`.
- Dedupe key = title đã normalize (lowercase, trim khoảng trắng thừa). Đơn giản cho V1, có thể nâng cấp fuzzy-match sau nếu cần.
- Crawler theo nguyên tắc: KHÔNG BAO GIỜ raise ra ngoài — lỗi thì log + trả `[]`, để 1 nguồn lỗi không kill cả job (đúng yêu cầu spec).

## Trạng thái: CHƯA LÀM (roadmap)

### Phase 2 — Crawler + Parser ✅ (xong, có giới hạn đã biết)
- [x] `src/crawler/base.py`: `BaseCrawler` abstract, method `crawl()` bọc try/except quanh `_crawl()` (subclass implement) - đảm bảo 1 nguồn lỗi không kill job, đúng spec. Logic này nằm ở base class (DRY), không lặp lại ở từng crawler con.
- [x] `src/crawler/airdrops_io.py` — **hoạt động đầy đủ**. Scrape `https://airdrops.io/latest/` bằng `requests`(qua `http_client`) + `BeautifulSoup`. Chiến lược parse: tìm mọi `<a href>` khớp pattern trang chi tiết project (loại trừ menu/nav qua `_EXCLUDED_SLUGS`), lấy heading `h2/h3/h4` gần nhất làm title, tìm dòng "Actions: ..." làm description, tìm keyword Ongoing/Ended/Upcoming làm status/tag. Đã unit test với HTML mock (`tests/test_crawler.py`) + test riêng "không raise khi network lỗi".
- [x] `src/crawler/galxe.py`, `layer3.py`, `zealy.py` — **STUB, trả về `[]`**, chưa implement thật. Lý do (đã research kỹ, xem chi tiết trong docstring từng file):
  - Galxe/Layer3: trang explore là SPA (React/Next.js client-render), GraphQL/API public chỉ lấy chi tiết 1 campaign đã biết ID, KHÔNG có endpoint liệt kê campaign mới toàn platform.
  - Zealy: API public hoạt động theo từng community (`subdomain` + `x-api-key`), không có endpoint discovery toàn platform - cần curated list community trước.
  - User đã xác nhận hướng đi: làm `airdrops.io` chắc trước, 3 nguồn kia để TODO, quay lại sau khi có network thật để inspect DevTools (mỗi file stub đã ghi rõ các bước cần làm khi quay lại).
- [x] `src/crawler/__init__.py`: `ALL_CRAWLERS` registry - `main.py` sau này chỉ cần loop qua danh sách này.
- [x] `src/parser/normalizer.py`: `build_project()` / `build_projects()` map dict thô -> `Project`, tự động skip + log warning nếu dữ liệu thiếu field bắt buộc (không raise).
- [x] `src/parser/dedupe.py`: `merge_projects()` merge theo `dedupe_key`, chọn giá trị "giàu thông tin hơn" cho từng field (`reward`/`deadline`/`cost`), cộng dồn `tags` + tên nguồn (vì `Project.source` chỉ giữ 1 giá trị, nguồn thứ 2 được lưu vào `tags` thay vì mất thông tin).
- [x] `tests/test_crawler.py`, `tests/test_parser.py` — **13/13 test pass**, toàn bộ dùng mock/monkeypatch, không gọi mạng thật.

### Phase 3 — History + Telegram (tiếp theo)
- [ ] `src/utils` (hoặc module riêng) quản lý đọc/ghi `history.json`, filter project mới (dùng `Project.unique_id` so với danh sách đã lưu).
- [ ] `src/telegram/notifier.py`: gửi message qua Bot API (dùng `httpx`, có retry qua `http_client` pattern có sẵn).
- [ ] `main.py`: orchestrate toàn bộ pipeline V1 (crawl tất cả nguồn trong `ALL_CRAWLERS` -> `build_projects` -> `merge_projects` -> filter theo history -> gửi Telegram -> ghi lại `projects.json` + `history.json`).
- [ ] Test thử chạy full pipeline local với `.env` thật (cần user điền `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` thật để test gửi tin nhắn).

### Phase 4 — Scorer (V2) + Gemini AI (V3)
- [ ] `src/scorer/base.py`: interface `ProjectScorer` (abstract).
- [ ] `src/scorer/rule_based.py`: implementation đơn giản chấm `worth_score` (V2).
- [ ] `src/ai/base.py`: interface `AIProvider` (để sau dễ thay OpenRouter/OpenAI).
- [ ] `src/ai/gemini_provider.py`: gọi Gemini, parse JSON response theo schema `AIScore`.
- [ ] Tích hợp vào `main.py`, gate bởi `ENABLE_AI_SCORING`.

### Phase 5 — GitHub Actions + README hoàn chỉnh
- [ ] `.github/workflows/crawl.yml`: cron mỗi 2h, cài `uv`, sync deps, chạy `main.py`, commit lại `data/*.json` nếu có thay đổi.
- [ ] README đầy đủ: giới thiệu, kiến trúc, cài đặt, cấu hình secrets trên GitHub, roadmap, screenshot placeholder.
- [ ] Review toàn bộ code, thêm docstring/type hint còn thiếu.

### Phase 6 — Dọn dẹp cuối cùng (khi user xác nhận xong việc)
Xem checklist đầy đủ ở section **"🧹 CHECKLIST DỌN DẸP CUỐI DỰ ÁN"** bên dưới.
Nguyên tắc chung: **không tự ý xoá gì** — luôn hỏi user xác nhận trước từng bước.

## Bước tiếp theo ngay bây giờ
👉 Phase 3: history filter (chống gửi trùng) + Telegram notifier + `main.py` orchestrate pipeline V1 đầu-cuối.

## Việc còn nợ (không quên)
- Galxe/Layer3/Zealy crawler còn là stub (`[]`) - cần quay lại sau khi có network thật để DevTools-inspect (chi tiết đã ghi trong docstring từng file `src/crawler/{galxe,layer3,zealy}.py`).

---

## 🧹 CHECKLIST DỌN DẸP CUỐI DỰ ÁN (để repo "clean & official")

> Chỉ chạy checklist này khi user xác nhận project đã xong (không phải giữa chừng).
> Với mỗi mục có xoá/sửa file, LUÔN hỏi user trước, không tự ý làm.

### 1. Rác trong quá trình dev (an toàn, có thể xoá ngay khi được xác nhận)
- [ ] `__pycache__/`, `*.pyc` ở mọi cấp thư mục
- [ ] `.pytest_cache/`
- [ ] `.venv/` hoặc `.uv/` nếu có tạo virtualenv local
- [ ] File tạm kiểu `*.tmp` sinh ra bởi `json_store.py` nếu job bị crash giữa chừng để sót lại

### 2. Bảo mật — kiểm tra kỹ trước khi public repo
- [ ] `.env` **KHÔNG** được nằm trong git history (`git log --all --full-history -- .env` phải rỗng)
- [ ] Không có API key/token nào bị hardcode trong code (grep thử `grep -rn "AIza\|xoxb-\|bot[0-9]" src/` trước khi push)
- [ ] `.env.example` chỉ chứa placeholder, không chứa giá trị thật đã lỡ điền vào lúc test
- [ ] Nếu lỡ commit `.env` ở đâu đó trong lịch sử git → cần rotate lại token/key đó (đổi token Telegram, tạo lại API key Gemini), xoá khỏi history không đủ vì key có thể đã bị lộ

### 3. Code quality trước khi "official"
- [ ] Xoá code thử nghiệm / debug print còn sót (nếu có chỗ nào lỡ dùng `print` thay vì logger)
- [ ] Xoá comment kiểu TODO đã làm xong, hoặc chuyển các TODO còn thật sự dở dang vào lại file này
- [ ] Chạy lại toàn bộ test (`pytest`) đảm bảo pass hết trước khi tag version
- [ ] Review lại README: đảm bảo hướng dẫn cài đặt đúng 100% với code thực tế (không còn mô tả tính năng chưa code xong)

### 4. Data/state trước khi public
- [ ] Xem lại `data/projects.json` và `data/history.json` — nếu có dữ liệu test/rác từ quá trình dev, hỏi user có muốn reset về `[]` trước khi public không
- [ ] `data/config.json` — xác nhận cấu hình nguồn bật/tắt đúng ý user

### 5. GitHub repo settings (làm thủ công trên GitHub, không phải code)
- [ ] Thêm secrets thật (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`) vào Settings → Secrets and variables → Actions
- [ ] Kiểm tra workflow chạy thử 1 lần bằng "Run workflow" thủ công trước khi để cron tự chạy
- [ ] Cân nhắc bật branch protection nếu có định mở PR từ người khác

### 6. Archive / xoá phần thử nghiệm không dùng nữa (nếu có phát sinh trong lúc code)
- [ ] Bất kỳ script/file nháp nào tạo ra ngoài `src/` để test nhanh (vd file `.py` thử ở root) — hỏi user trước khi xoá
- [ ] Branch git thử nghiệm không cần giữ lại

> Khi thực hiện checklist này, Claude sẽ hỏi xác nhận từng nhóm mục trước khi xoá bất kỳ file nào, không xoá hàng loạt một lúc.
