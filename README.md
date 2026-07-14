# 🎯 Airdrop Intelligence Bot

AI Research Assistant cho airdrop hunter — không chỉ tổng hợp airdrop, mà tự
động crawl, chấm điểm (rule-based + AI), và gửi thông báo qua Telegram.
Chạy hoàn toàn miễn phí trên GitHub Actions, không cần VPS, không cần database.

---

## 1. Giới thiệu

- **Chi phí ≈ 0**: chạy trên GitHub Actions (free tier), lưu state bằng file JSON commit thẳng vào repo — không cần thuê server, không cần database.
- **Thông báo qua Telegram**: chỉ cần mở Telegram là nhận được airdrop mới, không cần mở app/web nào khác.
- **Không gửi trùng**: mỗi airdrop chỉ được thông báo 1 lần (theo dõi qua `data/history.json`).
- **Chấm điểm 2 lớp**:
  - **V2 (rule-based)**: chấm nhanh dựa trên độ đầy đủ thông tin, miễn phí, luôn chạy.
  - **V3 (AI, Gemini)**: đánh giá sâu hơn (đáng làm không, rủi ro scam, cần vốn/thời gian bao nhiêu) — tùy chọn bật/tắt qua `.env`.
- **Dễ mở rộng**: interface `ProjectScorer` (V2) và `AIProvider` (V3) tách biệt, thêm nguồn crawl mới hoặc đổi AI provider (Gemini → OpenRouter/OpenAI) không cần sửa code phía trên.

## 2. Kiến trúc

```
airdrop-intelligence/
├── main.py                  # Entry point - orchestrate toàn bộ pipeline
├── src/
│   ├── crawler/              # Lấy dữ liệu thô từ từng nguồn
│   │   ├── base.py           #   BaseCrawler - lỗi 1 nguồn không kill job
│   │   ├── airdrops_io.py    #   ✅ hoạt động (HTML scraping)
│   │   ├── galxe.py          #   🚧 stub - SPA, chưa có cách crawl ổn định
│   │   ├── layer3.py         #   🚧 stub - SPA, chưa có cách crawl ổn định
│   │   └── zealy.py          #   🚧 stub - API cần biết trước community
│   ├── parser/                # Chuẩn hóa dữ liệu thô -> Project + dedupe/merge
│   ├── scorer/                # ProjectScorer (V2, rule-based, miễn phí)
│   ├── ai/                    # AIProvider interface + GeminiProvider (V3)
│   ├── telegram/               # Format + gửi thông báo qua Bot API
│   ├── models/                 # Project, ProjectScore, AIScore (pydantic)
│   └── utils/                   # logger, config (.env), http_client (retry), json_store, history
├── data/
│   ├── projects.json          # Toàn bộ project đang active (ghi đè mỗi lần chạy)
│   ├── history.json            # unique_id đã từng gửi Telegram (chống gửi trùng)
│   └── config.json             # Bật/tắt từng nguồn crawl
├── scripts/
│   └── list_gemini_models.py  # Liệt kê model Gemini khả dụng (khi model bị đổi/retire)
├── tests/                       # pytest, mock hoàn toàn - không gọi mạng thật
└── .github/workflows/crawl.yml # Cron mỗi 2h
```

### Luồng chạy chính

```
crawl (mỗi nguồn, lỗi thì bỏ qua nguồn đó)
  → parse/normalize (dict thô → Project)
  → merge (dedupe project trùng giữa các nguồn)
  → chấm điểm rule-based (V2, luôn chạy)
  → lọc theo history.json (chỉ giữ project CHƯA từng gửi)
  → [nếu ENABLE_AI_SCORING=true] chấm điểm AI (V3, chỉ cho project mới)
  → gửi Telegram cho project mới
  → ghi lại data/projects.json + data/history.json
```

## 3. Cài đặt

Yêu cầu: Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd airdrop-intelligence
uv sync
cp .env.example .env
```

Mở `.env` vừa tạo, điền các giá trị thật (xem mục Cấu hình bên dưới).

Chạy thử local:

```bash
uv run python main.py
```

Chạy test:

```bash
uv run pytest
```

## 4. Cấu hình (`.env`)

> ⚠️ File `.env` chứa token/API key thật — **không bao giờ commit file này**
> (đã nằm sẵn trong `.gitignore`). Chỉ commit `.env.example` (placeholder).

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token bot Telegram, lấy từ [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | ✅ | Chat ID nhận thông báo (có thể lấy qua [@userinfobot](https://t.me/userinfobot) hoặc gọi API `getUpdates`) |
| `AI_PROVIDER` | | Mặc định `gemini` |
| `GEMINI_API_KEY` | Chỉ khi bật AI scoring | Lấy free tại [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | | Mặc định `gemini-3.1-flash-lite`. Nếu model bị lỗi/retire, chạy `python scripts/list_gemini_models.py` để xem danh sách model hiện có |
| `ENABLE_AI_SCORING` | | `true`/`false`, mặc định `false` (chỉ dùng rule-based, không tốn API call) |
| `HTTP_TIMEOUT_SECONDS` | | Mặc định `15` |
| `HTTP_MAX_RETRIES` | | Mặc định `3` |
| `LOG_LEVEL` | | Mặc định `INFO` |

## 5. GitHub Actions (chạy tự động mỗi 2 giờ)

1. Push code lên GitHub (repo có thể để **Private**, không ảnh hưởng gì).
2. Vào **Settings → Secrets and variables → Actions**, thêm các **Secrets**:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GEMINI_API_KEY` (nếu dùng AI scoring)
3. (Tùy chọn) Thêm **Variables** cùng chỗ trên nếu muốn override mặc định:
   - `GEMINI_MODEL` (mặc định `gemini-3.1-flash-lite` nếu không set)
   - `ENABLE_AI_SCORING` (mặc định `false` nếu không set)
4. Vào tab **Actions**, chọn workflow **Airdrop Crawl**, bấm **Run workflow** để test thủ công lần đầu trước khi để cron tự chạy.
5. Kiểm tra log lần chạy đầu — xem crawler `airdrops.io` có bị chặn (403) không (xem mục Giới hạn bên dưới).

Workflow tự commit lại `data/projects.json` + `data/history.json` sau mỗi lần chạy — đây là cách "lưu state" duy nhất, không cần database.

## 6. Giới hạn hiện tại (đọc trước khi dùng)

- **Chỉ `airdrops.io` hoạt động đầy đủ.** `Galxe`, `Layer3`, `Zealy` hiện là **stub** (luôn trả về rỗng) vì cả 3 đều là web app SPA không có API public để "khám phá campaign mới" (đã research kỹ, xem chi tiết trong docstring từng file `src/crawler/{galxe,layer3,zealy}.py` và `project_memory.md`).
- **`airdrops.io` từng trả về 403 Forbidden khi test ở môi trường dev** (nghi WAF chặn theo IP datacenter). Cần kiểm tra log lần chạy GitHub Actions đầu tiên — IP của GitHub Actions runner có thể bị chặn hoặc không, phải test thật mới biết.
- **Dedupe theo tên project (đã normalize)** — đơn giản cho V1, có thể nhận nhầm 2 project khác nhau nhưng trùng tên, hoặc bỏ sót project cùng 1 dự án nhưng đặt tên khác nhau ở 2 nguồn.

## 7. Screenshot

> _(Chèn ảnh chụp màn hình tin nhắn Telegram thực tế ở đây sau khi chạy thử)_

```
[ Ảnh chụp Telegram bot gửi thông báo airdrop mới ]
```

## 8. Roadmap

- [x] **V1**: Crawler (1/4 nguồn hoạt động) + parser + dedupe + Telegram + chống gửi trùng
- [x] **V2**: `ProjectScorer` rule-based
- [x] **V3**: AI scoring qua Gemini (`AIProvider` interface, dễ đổi sang OpenRouter/OpenAI sau)
- [x] GitHub Actions cron mỗi 2 giờ, tự commit lại state
- [ ] Implement crawler thật cho Galxe / Layer3 / Zealy (cần inspect network thật qua DevTools — xem hướng dẫn trong từng file stub)
- [ ] Cân nhắc thêm nguồn mới (vd DappRadar, CoinMarketCap Airdrops)
- [ ] Dashboard xem lại lịch sử airdrop đã gửi (hiện chỉ có JSON thô)

## 9. Không làm (out of scope, theo thiết kế)

Không có frontend, không login, không database, không ví Web3, không tự động claim/swap/ký giao dịch. Đây là bot **thông báo + hỗ trợ nghiên cứu**, không tự động thực hiện hành động on-chain nào.

---
