-- =====================================================================
-- Migration 002 — Bảng `pipeline_runs`
-- =====================================================================
-- Ngày: 2026-08-28
-- Gỡ chặn: FR-03 (/trends/latest) và FR-04→06 (/runs)
--
-- VÌ SAO MỘT BẢNG PHỤC VỤ CẢ BỐN ENDPOINT:
--   Một báo cáo xu hướng LUÔN thuộc về một lần chạy — không có trend report
--   nào trôi nổi độc lập, nó là kết quả của chu kỳ nào đó. Nên thay vì dựng
--   thêm bảng `trends` riêng rồi phải nối khoá ngoại và giữ đồng bộ hai bên,
--   lưu thẳng vào cột `jsonb` của chính lần chạy sinh ra nó.
--
--   `/trends/latest` khi đó chỉ là: lấy `trend_report` của run `succeeded`
--   gần nhất. Không join, không lệch dữ liệu.
--
-- VÌ SAO `jsonb` MÀ KHÔNG TÁCH CỘT:
--   Cấu trúc TrendReport còn đổi (số xu hướng, có thêm điểm tin cậy hay không).
--   Tách cột thì mỗi lần đổi phải migrate. `jsonb` cho phép hình dạng tiến hoá
--   mà không đụng schema, và Postgres vẫn truy vấn/index được bên trong nếu
--   sau này cần. Đánh đổi: DB không kiểm tra được hình dạng — nên tầng ứng
--   dụng phải tự validate khi đọc lên.
--
-- Cách chạy: Supabase Dashboard → SQL Editor → dán → Run.
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    run_id            uuid PRIMARY KEY,

    topic             text NOT NULL,

    -- Ràng buộc ở tầng DB chứ không chỉ trong code: dữ liệu sai không lọt vào
    -- được kể cả khi ghi từ script tay hay từ một phiên bản app cũ.
    status            text NOT NULL
                      CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),

    -- Phân biệt run do API kích hoạt với run do CronJob chạy theo lịch (FR-06
    -- AC-06.2). Thiếu trường này thì không trả lời được "hôm qua ai chạy cái gì".
    trigger           text NOT NULL
                      CHECK (trigger IN ('api', 'cronjob', 'manual')),

    started_at        timestamptz,
    finished_at       timestamptz,

    -- Hai số này cho biết pipeline có thực sự làm được việc không. Cào về 18
    -- bài mà lưu 0 bài là dấu hiệu hỏng, dù status vẫn 'succeeded'.
    articles_scraped  integer,
    articles_stored   integer,

    -- Báo cáo xu hướng của chu kỳ này. NULL khi chưa chạy xong hoặc khi
    -- TrendSynthesisAgent (enrichment) lỗi — pipeline vẫn đi tiếp, chỉ là
    -- chu kỳ đó không có xu hướng.
    trend_report      jsonb,

    -- Chỉ có giá trị khi status='failed'. Ghi tên agent gây lỗi để đọc log
    -- không phải mò (FR-05 AC-05.2).
    error             text,

    created_at        timestamptz NOT NULL DEFAULT now()
);

-- Phục vụ FR-06 (lịch sử run, mặc định sắp xếp giảm dần theo started_at).
CREATE INDEX IF NOT EXISTS pipeline_runs_started_at_idx
    ON public.pipeline_runs (started_at DESC NULLS LAST);

-- Phục vụ FR-04 AC-04.4: kiểm tra "có run nào đang chạy không" trước khi cho
-- phép kích hoạt run mới. Truy vấn này chạy ở MỌI request POST /runs nên cần index.
CREATE INDEX IF NOT EXISTS pipeline_runs_status_idx
    ON public.pipeline_runs (status);

-- Phục vụ FR-03: tìm run 'succeeded' gần nhất CÓ trend_report.
-- Partial index — chỉ đánh index phần thoả điều kiện, nhỏ hơn nhiều so với
-- index toàn bảng, vì phần lớn truy vấn trend chỉ quan tâm nhóm này.
CREATE INDEX IF NOT EXISTS pipeline_runs_latest_trend_idx
    ON public.pipeline_runs (finished_at DESC)
    WHERE status = 'succeeded' AND trend_report IS NOT NULL;

-- =====================================================================
-- ROW LEVEL SECURITY — BẮT BUỘC, theo đúng ADR 0010
-- =====================================================================
-- Supabase phơi bảng ra REST API công khai. Không bật RLS thì bất kỳ ai có
-- SUPABASE_URL + publishable key (key Supabase thiết kế để nhúng thẳng vào
-- JavaScript trình duyệt, dashboard gắn nhãn "public") đều SELECT/INSERT/
-- UPDATE/DELETE được toàn bộ bảng.
--
-- ADR 0010 ghi rõ đây không phải lo xa: chu kỳ production 2026-07-10 đã thực
-- sự ghi 3 dòng vào `articles` bằng chính anon key đó.
--
-- Bảng này còn nhạy hơn `articles`: cột `error` chứa thông điệp lỗi nội bộ —
-- tên agent, đôi khi cả chi tiết hạ tầng. Lộ ra còn tệ hơn lộ danh sách bài.
--
-- KHÔNG tạo policy nào. Không policy = từ chối tất cả với `anon` và
-- `authenticated`. Pipeline dùng key `sb_secret_` (service_role) nên BỎ QUA
-- RLS hoàn toàn — bật RLS không ảnh hưởng gì tới app.
ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;
