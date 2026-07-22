# Airdrop Intelligence Bot

⏸️ Dự án tạm dừng

> Crawl, chấm điểm và gửi thông báo Telegram cho các airdrop crypto mới, chạy miễn phí trên GitHub Actions. 

![Release](https://img.shields.io/github/v/release/tuananh511/airdrop-intelligence?label=release)
![License](https://img.shields.io/github/license/tuananh511/airdrop-intelligence)
![Build](https://img.shields.io/github/actions/workflow/status/tuananh511/airdrop-intelligence/crawl.yml?label=build)

## Overview

AI Research Assistant cho airdrop hunter — không chỉ tổng hợp airdrop, mà tự động crawl, chấm điểm (rule-based + AI), và gửi thông báo qua Telegram. Chạy hoàn toàn miễn phí trên GitHub Actions, không cần VPS, không cần database.

- **Chi phí ≈ 0**: chạy trên GitHub Actions (free tier), lưu state bằng file JSON commit thẳng vào repo — không cần thuê server, không cần database.
- **Thông báo qua Telegram**: chỉ cần mở Telegram là nhận được airdrop mới.
- **Không gửi trùng**: mỗi airdrop chỉ được thông báo 1 lần (theo dõi qua `data/history.json`).
- **Chấm điểm 2 lớp**: V2 rule-based (miễn phí, luôn chạy) + V3 AI qua Gemini (tùy chọn, đánh giá sâu hơn).
- **Dễ mở rộng**: interface `ProjectScorer` (V2) và `AIProvider` (V3) tách biệt, thêm nguồn crawl mới hoặc đổi AI provider không cần sửa code phía trên.

### Kiến trúc

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
│   └── list_gemini_models.py  # Liệt kê model Gemini khả dụng
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

## Features

- Crawl nhiều nguồn airdrop (hiện tại: `airdrops.io` hoạt động đầy đủ; `Galxe`, `Layer3`, `Zealy` đang ở dạng stub)
- Chấm điểm 2 lớp: rule-based (V2) miễn phí + AI qua Gemini (V3) tùy chọn
- Chống gửi trùng thông báo qua `data/history.json`
- Gửi thông báo qua Telegram Bot API
- Chạy hoàn toàn miễn phí trên GitHub Actions, cron mỗi 2 giờ
- Không cần database — lưu state bằng JSON commit thẳng vào repo
- Interface mở rộng dễ dàng: `ProjectScorer`, `AIProvider`

## Installation

Yêu cầu: Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/tuananh511/airdrop-intelligence.git
cd airdrop-intelligence
uv sync
cp .env.example .env
```

Mở `.env` vừa tạo và điền các giá trị thật:

| Biến | Bắt buộc | Mô tả |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token bot Telegram, lấy từ [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | ✅ | Chat ID nhận thông báo (qua [@userinfobot](https://t.me/userinfobot) hoặc API `getUpdates`) |
| `AI_PROVIDER` | | Mặc định `gemini` |
| `GEMINI_API_KEY` | Chỉ khi bật AI scoring | Lấy free tại [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | | Mặc định `gemini-3.1-flash-lite` |
| `ENABLE_AI_SCORING` | | `true`/`false`, mặc định `false` |
| `HTTP_TIMEOUT_SECONDS` | | Mặc định `15` |
| `HTTP_MAX_RETRIES` | | Mặc định `3` |
| `LOG_LEVEL` | | Mặc định `INFO` |

> ⚠️ File `.env` chứa token/API key thật — không bao giờ commit file này (đã nằm trong `.gitignore`).

## Usage

Chạy thử local:

```bash
uv run python main.py
```

Chạy test:

```bash
uv run pytest
```

Chạy tự động qua GitHub Actions:

1. Push code lên GitHub (repo có thể để Private).
2. Vào **Settings → Secrets and variables → Actions**, thêm Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY` (nếu dùng AI scoring).
3. (Tùy chọn) Thêm Variables để override mặc định: `GEMINI_MODEL`, `ENABLE_AI_SCORING`.
4. Vào tab **Actions**, chọn workflow **Airdrop Crawl**, bấm **Run workflow** để test thủ công lần đầu.
5. Kiểm tra log lần chạy đầu — xem crawler `airdrops.io` có bị chặn (403) không.

Workflow tự commit lại `data/projects.json` + `data/history.json` sau mỗi lần chạy — đây là cách lưu state duy nhất, không cần database.

### Giới hạn hiện tại

- Chỉ `airdrops.io` hoạt động đầy đủ; `Galxe`, `Layer3`, `Zealy` là stub vì đều là SPA không có API public.
- `airdrops.io` từng trả về 403 Forbidden khi test ở môi trường dev (nghi WAF chặn theo IP datacenter).
- Dedupe theo tên project đã normalize — có thể nhận nhầm hoặc bỏ sót một số trường hợp.

### Không làm (out of scope)

Không có frontend, không login, không database, không ví Web3, không tự động claim/swap/ký giao dịch. Đây là bot thông báo + hỗ trợ nghiên cứu, không tự động thực hiện hành động on-chain.

## Roadmap

- [x] V1: Crawler (1/4 nguồn hoạt động) + parser + dedupe + Telegram + chống gửi trùng
- [x] V2: `ProjectScorer` rule-based
- [x] V3: AI scoring qua Gemini (`AIProvider` interface)
- [x] GitHub Actions cron mỗi 2 giờ, tự commit lại state
- [ ] Implement crawler thật cho Galxe / Layer3 / Zealy
- [ ] Cân nhắc thêm nguồn mới (DappRadar, CoinMarketCap Airdrops)
- [ ] Dashboard xem lại lịch sử airdrop đã gửi

## License

MIT
