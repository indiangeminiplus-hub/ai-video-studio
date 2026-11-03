# Tự động: b-roll + âm thanh một bấm

Code: `scripts/auto_broll.mjs`, `scripts/auto_sfx.py --level`, `studio/routes/80_autofill.mjs`, `studio/features/80_autofill.js` (panel **Tự động**), ô “Tự thêm b-roll + âm thanh sau khi dựng” trong **AI dựng giúp** (`20_ai.js`). Thư viện: `scripts/gen_sfx.py` (309 SFX), `scripts/gen_music.py` (30 nhạc) — bảng ở `references/sound-library.md`.

## 1. B-roll tự động — `auto_broll.mjs`
```bash
node scripts/auto_broll.mjs <dự án>/timeline.json --density vua --src preset,text,emoji,media [--claude] [--seed 1] [--dry] [--clear]
```
| Tham số | Ý nghĩa |
|---|---|
| `--density` | `thua` ≈ 1 chèn / 8 s · `vua` ≈ 1/5 s · `day` ≈ 1/3 s · `ratday` ≈ 1/2 s |
| `--src` | `preset` (b-roll động từ `assets/broll/catalog.json`), `text` (chữ nổi từ khoá), `emoji` (emoji 3D khi câu có từ cảm xúc/từ khoá), `media` (ảnh/clip trong `media/` của dự án), `stock` (ảnh Commons/Openverse qua `ai_broll.mjs`, tối đa 3, chỉ danh từ cụ thể, cần mạng) |
| `--claude` | `claude -p --model sonnet` chọn preset (chỉ trong danh sách ứng viên của câu) + chữ IN HOA ≤ 18 ký tự + emoji; lỗi/không có CLI → tự dùng luật offline |
| `--clear` | chỉ xoá cảnh `_auto` |

Luật:
- Gộp phụ đề thành câu (`sentences()` của `ai_broll.mjs`), đặt mốc theo mật độ, bắt đầu đúng từ gần nhất.
- Câu có **số** → template số (`counter_big`/`bar_chart`/`line_chart`, `%` → `pie`/`progress`), `num` đúng số nói; mỗi số dùng một lần.
- Preset chấm điểm theo tag catalog; **không lặp template trong 3 lần gần nhất**; palette chính theo gói (`slate`→ocean, `hypecam`→ember, `luxury`/`realestate`→gold…) hoặc màu `brand.accent` gần nhất, cứ 4 preset có 1 palette phụ.
- Bố cục xoay vòng `card → right → full → pip → person → left`; mọi khung được kiểm tra **không giao vùng mặt** (`TL.face` ± ~150×180 px thiết kế); dọc: thẻ trên đầu hoặc dưới phụ đề, tránh huy hiệu `frame_grid`. `full` chỉ 1–1,5 s. `person` (b-roll nền, người cutout đứng trước) chỉ khi clip có `cutouts` và không dùng `frame_grid`.
- Bỏ 0–1,5 s, thẻ kết/CTA cuối, và mọi cảnh lớn không phải `_auto` (cảnh nền như `frame_grid`, `*_frame`, `*_grade` không chặn).
- Dọc: preset → `media_card` (`screen.broll`); ngang: `broll` (`layout` card/full + `x,y,w,h`); `person` → `broll` `layout:full, person:true` (+ `fit:"cover"` ở khổ dọc — engine phóng preset 16:9 phủ kín khung).
- Mỗi cảnh có `"_auto": true, "note": "tự động"`. Chạy lại chỉ thay cảnh `_auto`; cảnh đã sửa trong Studio (`_orig`) và cảnh của bạn/AI được giữ. Ghi đè tại chỗ, có `timeline.json.bak`. In `@@ <tiến độ> <bước>` và 1 dòng JSON tóm tắt.

## 2. Âm thanh tự động — `auto_sfx.py --level`
```bash
$PY scripts/auto_sfx.py timeline.json --level nhe|vua|phongphu [--music auto] [--claude] [--clear]
```
Không có `--level` = hành vi cũ, không đổi (đã so 23 timeline mẫu: giống từng byte).
- Luật cũ theo module vẫn chạy, cộng luật chung cho **mọi** loại cảnh (24 gói, gói người dùng `u_*`, broll, text, photo, emoji, sticker): theo tên/field — full-frame → whoosh nặng vào + swoosh ra; thẻ/pip → pop/swipe; hero/hook/title → hit (+ riser/reverse cymbal 0,6 s trước, mức vừa+); chat/điện thoại → notification; tiền/giá → cash/coin; số liệu → ding; gõ chữ (`anim:"type"`, typewriter, search) → typing; ảnh → camera_shutter; emoji/sticker → pop + sparkle; chuyển clip trong `TL.clips` → whip/glitch/whoosh/transition_soft theo `transition.type`.
- Hook: hit ở graphic lớn đầu tiên (< 2,5 s), `sub_drop_short` khi hook kết thúc; outro: `outro_hit` ở thẻ kết.
- Phụ đề: số → ding / coin (nếu kèm đơn vị tiền), từ tiền (“tiền, triệu, tỷ, lương, giá…”) → coin (mức vừa+); từ `hl`, từ cảm xúc, từ khoá → pop/whoosh rất nhẹ −26 dB (phong phú). So khớp **có dấu** (không nhầm “tiến”/“tiền”).
- Limiter: tối đa 2/3/4 tiếng mỗi 1 s và 1/2/2 mỗi 0,5 s (nhẹ/vừa/phong phú), cách nhau ≥ 0,1 s, ưu tiên hit lớn; riser/typing tính riêng. Đang có giọng → giảm 4/3/2 dB (hit lớn −2 dB). Xoay biến thể từng họ âm.
- Chỉ thay mục `_auto`; SFX khác giữ nguyên, hit mới không đặt trùng (±0,15 s) hit đã có.
- `--music auto`: chia đoạn ≥ 8 s, chấm mood theo từ khoá (hoặc Claude với `--claude`), mood gốc = nhạc đang có hoặc theo gói; tối đa 1 lần đổi / 10 s; `xfade` 0,8 s, đoạn sau vào phần “lift” (`offset` = ½ track), fade cuối 1,5 s, gain −18. Nhạc cũ bị thay được cất trong `_was` → “Xoá phần tự động” trả lại. Có nhạc file riêng của bạn hoặc gói `beatslide` → không đụng nhạc. Luôn bật `audio.duck` kiểu object (−10 dB).

## 3. Studio — panel “Tự động”
Mật độ · nguồn (B-roll động / Chữ nổi / Emoji / Media của tôi / Ảnh stock / Claude chọn) · mức âm thanh · tự chọn nhạc · tự chạy sau AI dựng giúp (lưu trong localStorage). Nút **Tự thêm B-roll + âm thanh**, **Chỉ B-roll**, **Chỉ âm thanh**, **Xoá tự động**. Mỗi lần: lưu → `pushUndo` (⌘Z quay lại) → job `POST /api/autofill {mode, density, src, claude, level, music}` (snapshot `.studio/history/<giờ>_autofill.json`) → `Studio.reload()`. `Studio.autofill.run(mode, {noUndo})` dùng cho AI dựng giúp (chung 1 bước hoàn tác).

## Đo trên clip thật (clip-mau, 31,6 s, dọc slate)
- B-roll: thưa 4 · vừa 5 · dày 9 · rất dày 12 chèn; mặt không bị che ở mọi still (contact sheet).
- Âm thanh (dày): nhẹ 13 / vừa 24 / phong phú 33 SFX (0,41 / 0,76 / 1,05 mỗi giây, đỉnh 1 / 3 / 4 trong 1 s). Bản xuất −14,3 LUFS, true peak −3,4 dBFS. Proxy che giọng (đường bao RMS 50 ms): SFX sát giọng < 6 dB chỉ 0,4–1,5 % thời gian nói (rất dày + phong phú: 3,1 %), trung vị giọng hơn SFX ~25 dB.

## Giới hạn
- Chọn b-roll offline theo từ khoá/tag — đúng ý ở mức “minh hoạ chủ đề”; `--claude` tốt hơn nhưng chậm 20–60 s.
- `TL.face` là một điểm cố định; người di chuyển nhiều có thể bị che một phần. Không có `TL.face` → giả định giữa khung.
- Ảnh stock Commons/Openverse là CC (nhiều ảnh CC BY/BY-SA → **phải ghi nguồn**, xem `media/credits.json`); chất lượng/độ đúng ý không đảm bảo; không có Pexels/Pixabay nếu chưa có key.
- Preset 16:9 trong khung dọc `full` hiện dạng letterbox (nền tối trên/dưới).
- Mood nhạc offline chỉ dựa trên từ khoá; video ngắn thường giữ 1 mood.
