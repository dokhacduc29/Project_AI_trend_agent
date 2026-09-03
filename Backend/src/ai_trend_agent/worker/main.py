"""
=====================================================================
AI TREND AGENT v4.0 — SOLID Edition
=====================================================================
FIX LIST:
    - [DIP] run_pipeline nhận BaseAgent thay vì concrete class
    - [ASYNC] Toàn bộ main() chạy trong asyncio.run() — loại bỏ schedule
    - [OCP] Factory không cần import class cụ thể — Agent tự đăng ký
    - [L09] Magic numbers → config.py
=====================================================================
"""
import os
import re
import sys
import asyncio
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Che secret trong log (webhook Discord, apiKey...) TRƯỚC mọi lời gọi mạng.
# httpx log nguyên URL ở mức INFO — xem log_redaction.py.
from ai_trend_agent.application.log_redaction import install_secret_redaction
install_secret_redaction()

# Import base_agent TRƯỚC để Factory sẵn sàng
from ai_trend_agent.application.base_agent import BaseAgent, AgentFactory
from ai_trend_agent.application.ports import RunRepository
from ai_trend_agent.domain.models import PipelineContext, RunStatus, RunTrigger
from ai_trend_agent.infrastructure.gemini_client import reset_budget, budget_report
from ai_trend_agent.domain import config

# Import các module Agent — decorator @register sẽ TỰ ĐĂNG KÝ vào Factory
from ai_trend_agent.infrastructure import scrapers   # noqa: F401 — side-effect import (đăng ký "scraper")
from ai_trend_agent.infrastructure import cleaner    # noqa: F401 — side-effect import (đăng ký "cleaner")
from ai_trend_agent.infrastructure import ai_agent   # noqa: F401 — side-effect import (đăng ký "analyzer")
from ai_trend_agent.infrastructure import trend_agent # noqa: F401 — side-effect import (đăng ký "trend" → phân tích xu hướng)
from ai_trend_agent.infrastructure import supabase_storage  # noqa: F401 — side-effect import (đăng ký "storage" → Supabase)
from ai_trend_agent.infrastructure import telegram_agent # noqa: F401 — side-effect import (đăng ký "telegram" — legacy, không dùng)
from ai_trend_agent.infrastructure import discord_agent  # noqa: F401 — side-effect import (đăng ký "discord" → publisher hiện hành)
from ai_trend_agent.infrastructure.supabase_run_repository import SupabaseRunRepository


def _load_env_file() -> None:
    """
    Nạp `.env` cho môi trường DEV. Không tìm thấy cũng không sao — trong container,
    biến môi trường đến từ K8s Secret / `--env-file`, không có file `.env` nào.

    [ADR 0014] Bản cũ tính đường dẫn `.env` từ vị trí file nguồn (`backend_dir`).
    Cách đó chết khi package được CÀI vào site-packages: lúc đó không còn thư mục
    `Backend/` nào bên cạnh code. Nay dò theo thư mục làm việc — đúng với cả hai
    kiểu chạy (từ gốc repo, hoặc từ `Backend/`).

    `load_dotenv` KHÔNG ghi đè biến môi trường đã tồn tại, nên biến truyền từ
    ngoài (K8s, docker run -e) luôn thắng file `.env`.
    """
    cwd = os.getcwd()
    candidates = [
        os.getenv("ENV_FILE", ""),              # ưu tiên chỉ định tường minh
        os.path.join(cwd, ".env"),              # chạy từ Backend/
        os.path.join(cwd, "Backend", ".env"),   # chạy từ gốc repo
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            load_dotenv(path)
            logging.debug(f"Da nap bien moi truong tu: {path}")
            return
    logging.debug("Khong tim thay file .env — dung bien moi truong san co.")


def validate_topic(user_input: str) -> str | None:
    topic = user_input.strip()
    if not topic:
        return "Artificial Intelligence"
    essence = re.sub(r'[^a-zA-Z0-9\s]', '', topic).strip()
    if not essence:
        return None
    clean_topic = re.sub(r'[\\/*?:"<>|]', "", topic).strip()
    return clean_topic[:config.MAX_TOPIC_LENGTH]


async def run_pipeline(
    agents: list[BaseAgent],
    ctx: PipelineContext,
    run_repo: "RunRepository | None" = None,
    trigger: RunTrigger = RunTrigger.CRONJOB,
    run_id: str | None = None,
) -> bool:
    """
    [FIX DIP] Nhận danh sách BaseAgent (abstraction), KHÔNG nhận concrete class.

    Nhờ đó, bạn có thể swap bất kỳ Agent nào mà KHÔNG sửa hàm này:
        - Thay StorageAgent bằng DatabaseStorageAgent? Được!
        - Thêm TelegramAgent vào cuối pipeline? Được!

    [FIX LSP] Vì execute() giờ có CÙNG chữ ký (ctx → ctx),
    ta có thể duyệt vòng lặp qua MỌI loại Agent một cách đồng nhất.

    [ADR 0011] Trả về True nếu chu kỳ đi hết pipeline, False nếu một agent
    CRITICAL lỗi giữa chừng. Dưới CronJob, giá trị này quyết định exit code:
    False → non-zero → Job Failed → backoffLimit. Không còn while True nuốt kết quả.

    [B3a] `run_repo` ghi nhật ký chu kỳ vào bảng `pipeline_runs` (SRS P11).
    Tham số này TÙY CHỌN và mặc định None: không truyền thì hành vi giống hệt
    v4.0, nên 18 test cũ chạy không cần sửa một dòng.

    Việc ghi nhật ký là ENRICHMENT theo ADR 0003 — chính `SupabaseRunRepository`
    tự nuốt lỗi bên trong. Supabase sập lúc ghi nhật ký thì chu kỳ vẫn chạy tiếp
    và vẫn đăng Discord. Mất một dòng nhật ký còn hơn mất cả mẻ tin.
    """
    logging.info("=" * 60)
    logging.info(f"KHOI DONG CHU KY QUET: '{ctx.topic.upper()}'")
    logging.info("=" * 60)

    # [ADR 0005] Reset budget Gemini cho chu kỳ mới
    reset_budget()

    # `run_id` có sẵn nghĩa là NGƯỜI GỌI đã tạo bản ghi trước (đường API: phải
    # có id để trả trong response 202 — AC-04.5). Lúc đó không tạo thêm, tránh
    # sinh hai bản ghi cho cùng một chu kỳ. Worker CronJob không truyền gì nên
    # tự tạo như cũ.
    if run_repo is not None:
        if run_id is None:
            run_id = await _safe_run_log(
                lambda: run_repo.create(topic=ctx.topic, trigger=trigger), "create"
            )
        if run_id is not None:
            await _safe_run_log(lambda: run_repo.mark_running(run_id), "mark_running")
            logging.info(f"[RUN] Bat dau ghi nhat ky chu ky: run_id={run_id}")

    articles_scraped: int | None = None

    for idx, agent in enumerate(agents):
        try:
            ctx = await agent.execute(ctx)

            # Số bài THÔ cào về = số bài ngay sau agent đầu tiên. Theo cấu trúc
            # pipeline, agent[0] luôn là scraper (xem thứ tự dựng ở `main()`);
            # các agent sau chỉ lọc bớt hoặc làm giàu, không thêm bài mới.
            if idx == 0:
                articles_scraped = len(ctx.articles)

            if not ctx.articles and isinstance(agent, BaseAgent):
                logging.warning(f"{agent.agent_name} tra ve 0 bai. Kiem tra nguon.")
        except Exception as e:
            # [RESILIENCE — ADR 0003] Agent critical lỗi → dừng chu kỳ.
            # Agent enrichment lỗi → log rồi đi tiếp, KHÔNG làm mất dữ liệu
            # đã cào/đã lưu ở các bước trước (no silent abort của cả pipeline).
            if getattr(agent, "is_critical", False):
                logging.error(f"[CRITICAL] {agent.agent_name} loi: {e}. Dung chu ky.")
                if run_id is not None and run_repo is not None:
                    # Ghi rõ TÊN AGENT gây lỗi, không chỉ thông điệp: đọc nhật ký
                    # là biết ngay hỏng ở khâu nào, khỏi mò log (FR-05 AC-05.2).
                    await _safe_run_log(
                        lambda: run_repo.finish(
                            run_id,
                            status=RunStatus.FAILED,
                            articles_scraped=articles_scraped,
                            articles_stored=_saved_count(agents),
                            error=f"{agent.agent_name} (critical) loi: {e}",
                        ),
                        "finish/failed",
                    )
                return False
            logging.error(f"[ENRICHMENT] {agent.agent_name} loi: {e}. Bo qua, pipeline di tiep.")
            continue

    # [ADR 0005] Tổng kết budget Gemini của chu kỳ (observability)
    b = budget_report()
    logging.info(
        f"[BUDGET] Gemini calls={b['calls']}/{config.GEMINI_MAX_CALLS_PER_CYCLE} "
        f"| ~input_tokens={b['approx_input_tokens']} | blocked={b['blocked']}"
    )

    if run_id is not None and run_repo is not None:
        # [AC-05.3] Enrichment agent lỗi vẫn tính là SUCCEEDED — đúng ngữ nghĩa
        # ADR 0003: chu kỳ đã đi hết pipeline và dữ liệu đã được lưu.
        await _safe_run_log(
            lambda: run_repo.finish(
                run_id,
                status=RunStatus.SUCCEEDED,
                articles_scraped=articles_scraped,
                articles_stored=_saved_count(agents),
                trend_report=ctx.trend_report,
            ),
            "finish/succeeded",
        )
        logging.info(f"[RUN] Da ghi ket qua chu ky: run_id={run_id}")

    logging.info("=" * 60 + "\n")
    return True


async def _safe_run_log(coro_factory, what: str) -> object | None:
    """
    Gọi một thao tác ghi nhật ký sao cho nó KHÔNG BAO GIỜ làm chết chu kỳ.

    [C-04] `SupabaseRunRepository` đã tự nuốt lỗi bên trong, nhưng chừng đó
    CHƯA ĐỦ. `RunRepository` khai bằng `Protocol` nên bất kỳ ai cũng viết được
    một bản hiện thực — chỉ cần một bản ném lỗi là pipeline chết theo. Bảo đảm
    "ghi nhật ký là enrichment" phải nằm ở NƠI CẦN NÓ, không uỷ thác cho từng
    bản hiện thực nhớ mà làm.

    Đây là phòng thủ nhiều lớp: implementation cẩn thận + call site cũng chặn.
    Lỗi đã bắt được bằng test với một repo cố tình hỏng hoàn toàn.

    Nhận `coro_factory` (hàm không tham số) chứ không nhận sẵn coroutine, để
    exception xảy ra ngay lúc DỰNG lời gọi cũng nằm trong vùng được bảo vệ.
    """
    try:
        return await coro_factory()
    except Exception as e:
        logging.error(f"[RUN] Ghi nhat ky that bai ({what}): {e}. Pipeline di tiep.")
        return None


def _saved_count(agents: list[BaseAgent]) -> int | None:
    """
    Số bài THỰC SỰ chèn mới, lấy từ storage agent.

    Không dùng `len(ctx.articles)` vì đó là số bài GỬI ĐI lưu, còn upsert với
    `ignore_duplicates=True` bỏ qua bài đã có — hai con số thường lệch nhau.
    Chỉ con số từ storage agent mới trả lời đúng "chu kỳ này thu được gì MỚI".

    Dò bằng `getattr` thay vì `isinstance` để không phải import concrete class
    vào đây: agent nào công bố `last_saved_count` thì agent đó là nơi lưu.
    """
    for agent in agents:
        count = getattr(agent, "last_saved_count", None)
        if count is not None:
            return count
    return None


async def main():
    """
    [FIX ASYNC] Toàn bộ main() giờ là async.
    Dùng asyncio.sleep() thay cho schedule + time.sleep().
    Loại bỏ dependency 'schedule', loại bỏ antipattern asyncio.run() trong sync wrapper.
    """
    _load_env_file()
    api_key = os.getenv("NEWS_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        # [Session 2] Thiếu key bắt buộc là lỗi cấu hình chí mạng, KHÔNG phải kết
        # thúc bình thường. Phải thoát non-zero để CronJob đánh dấu Job Failed
        # (nếu return/exit 0, K8s coi là Succeeded → dashboard xanh dù pipeline chết).
        logging.error("Thieu NEWS_API_KEY trong file .env! Thoat voi exit code loi cau hinh.")
        sys.exit(config.EXIT_CONFIG_ERROR)
    if not gemini_api_key:
        # GEMINI_API_KEY chỉ làm degrade (enrichment), không chí mạng → cảnh báo, chạy tiếp.
        logging.warning("Thieu GEMINI_API_KEY. Chuc nang AI se bi bo qua!")

    logging.info("AI TREND AGENT v4.0 (SOLID Edition)")

    # [CONTAINER] Đọc topic từ env var TOPIC (dùng trong Docker/K8s).
    # Nếu không có, fallback sang interactive stdin (dùng khi chạy local).
    env_topic = os.getenv("TOPIC", "").strip()
    if env_topic:
        target_topic = validate_topic(env_topic)
        if not target_topic:
            logging.error(f"TOPIC env var '{env_topic}' khong hop le! Su dung default.")
            target_topic = "Artificial Intelligence"
        logging.info(f"[CONTAINER MODE] Topic tu env: '{target_topic}'")
    else:
        target_topic = None
        while not target_topic:
            try:
                raw = input("\nMoi ban nhap tu khoa can tim: ")
            except (KeyboardInterrupt, EOFError):
                logging.info("Huy khoi dong. Tam biet!")
                return
            target_topic = validate_topic(raw)
            if not target_topic:
                logging.error("Tu khoa khong hop le. Vui long thu lai!")

    # Tạo pipeline context — chứa mọi thứ Agent cần
    ctx_template = PipelineContext(
        topic=target_topic, 
        api_key=api_key, 
        gemini_api_key=gemini_api_key or ""
    )

    # Tạo đội quân Agent qua Factory (Agent đã tự đăng ký nhờ decorator)
    agents: list[BaseAgent] = [
        AgentFactory.create("scraper"),
        AgentFactory.create("cleaner"),
        AgentFactory.create("analyzer"), # [Phase 4] Tích hợp bộ não AI
        AgentFactory.create("trend"),    # [Phase A] Phân tích xu hướng vĩ mô
        AgentFactory.create("storage"),  # Lưu vào Supabase cloud (supabase_storage)
        AgentFactory.create("discord"),  # [Phase 6] Gửi thông báo Discord (thay Telegram)
    ]

    for agent in agents:
        logging.info(f"Da trien khai: {agent}")

    # [ADR 0011] Mô hình ONE-SHOT: chạy ĐÚNG MỘT chu kỳ rồi thoát.
    # Việc lặp lại mỗi 4 giờ giờ là trách nhiệm của CronJob (schedule:
    # "0 */4 * * *" trong k8s/03-deployment.yaml), KHÔNG phải while True trong app.
    # Lý do: dưới CronJob, một pod sống-mãi là sai mô hình — K8s không biết khi nào
    # "một lần chạy" thành công. App làm 1 đơn vị việc, orchestrator lo việc lặp.
    logging.info(f"Che do ONE-SHOT (CronJob lo lich {config.SCHEDULE_INTERVAL_HOURS}h/lan).")

    # Chờ DNS/network sẵn sàng trong môi trường container (K8s pod start)
    startup_delay = int(os.getenv("STARTUP_DELAY_SECONDS", "0"))
    if startup_delay > 0:
        logging.info(f"Cho {startup_delay}s de DNS san sang...")
        await asyncio.sleep(startup_delay)

    # Context MỚI cho chu kỳ này (không còn nguy cơ dồn articles vì chỉ chạy 1 lần)
    ctx = PipelineContext(
        topic=ctx_template.topic,
        api_key=ctx_template.api_key,
        gemini_api_key=ctx_template.gemini_api_key,
    )
    # [B3a] Ghi nhật ký chu kỳ vào bảng `pipeline_runs` (SRS P11).
    #
    # `trigger=CRONJOB` vì đây là worker one-shot — thứ mà K8s CronJob gọi theo
    # lịch. Run do API kích hoạt sẽ truyền `RunTrigger.API` ở bước 9, và chính
    # trường này phân biệt hai nguồn khi đọc lịch sử (FR-06 AC-06.2).
    #
    # Dựng repository ở ĐÂY chứ không bên trong `run_pipeline`: hàm đó nhận phụ
    # thuộc từ ngoài để test thay được bằng bản giả. Ai dựng thì người đó biết
    # môi trường — worker biết nó nói chuyện với Supabase, `run_pipeline` không cần biết.
    run_repo = SupabaseRunRepository()
    completed = await run_pipeline(agents, ctx, run_repo, RunTrigger.CRONJOB)

    # [ADR 0011] Agent critical lỗi → chu kỳ CHƯA hoàn tất → thoát non-zero để
    # CronJob đánh dấu Job Failed (kích backoffLimit), thay vì Succeeded âm thầm.
    if not completed:
        logging.error("Chu ky KHONG hoan tat (agent critical loi). Thoat non-zero.")
        sys.exit(config.EXIT_PIPELINE_ERROR)

    logging.info("Chu ky hoan tat. Thoat 0.")


def cli() -> None:
    """
    Điểm vào console script `ai-trend-worker` (khai báo ở pyproject.toml).

    Tách khỏi khối `if __name__ == "__main__"` để entry point của setuptools gọi
    được: `pip install -e .` sinh ra lệnh `ai-trend-worker`, thay cho đường dẫn
    dài `python Backend/src/ai_trend_agent/worker/main.py`.
    """
    if "--profile" in sys.argv:
        import cProfile
        import pstats
        import io
        logging.info("BAT DAU CHE DO PROFILING (Day 47)...")
        pr = cProfile.Profile()
        pr.enable()
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            # Ctrl+C là thoát bình thường; nhưng KHÔNG nuốt SystemExit — exit code
            # lỗi cấu hình phải lọt ra ngoài (finally vẫn chạy, in stats trước khi thoát).
            pass
        finally:
            pr.disable()
            s = io.StringIO()
            sortby = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats(30)
            logging.info("=" * 60)
            logging.info("KET QUA PROFILING (Top 30 ham tieu ton thoi gian nhat):")
            logging.info(s.getvalue())
            logging.info("=" * 60)
    else:
        asyncio.run(main())


if __name__ == "__main__":
    cli()