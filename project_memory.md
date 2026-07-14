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

### Phase 2 — Crawler + Parser (tiếp theo)
- [ ] `src/crawler/base.py`: abstract interface chung cho crawler.
- [ ] `src/crawler/airdrops_io.py`, `galxe.py`, `layer3.py`, `zealy.py` — mỗi file 1 nguồn, bọc try/except, log lỗi, return `[]` nếu fail.
- [ ] `src/parser/normalizer.py`: map dict thô -> `Project`.
- [ ] `src/parser/dedupe.py`: merge project trùng theo `dedupe_key`.
- [ ] Unit test cho parser/dedupe (dùng mock HTML/JSON, không gọi mạng thật trong test).

### Phase 3 — History + Telegram
- [ ] `src/utils` (hoặc module riêng) quản lý đọc/ghi `history.json`, filter project mới.
- [ ] `src/telegram/notifier.py`: gửi message qua Bot API (dùng `httpx`, có retry).
- [ ] `main.py`: orchestrate toàn bộ pipeline V1 (crawl -> parse -> dedupe -> filter history -> gửi Telegram -> lưu state).
- [ ] Test thử chạy full pipeline local với `.env` thật (cần user điền token).

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
- [ ] Xoá `.pytest_cache/`, `__pycache__/` nếu còn sót trước khi commit lần cuối.
- [ ] Kiểm tra `.env` KHÔNG bị commit nhầm (`git status` phải sạch, `.env` phải nằm trong `.gitignore`).
- [ ] Xác nhận `data/*.json` đã có ở trạng thái mong muốn trước khi push public (không lộ thông tin nhạy cảm).
- [ ] **Sẽ nhắc user rõ ràng trước khi xoá bất kỳ file/thư mục nào** — không tự ý dọn.

## Bước tiếp theo ngay bây giờ
👉 Phase 2: viết crawler cho 4 nguồn (airdrops.io, Galxe, Layer3, Zealy) + parser + dedupe.
