#!/usr/bin/env python3
"""
블로그 자동화 GUI
더블클릭으로 실행하면 창이 열립니다.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
import io
from pathlib import Path
from dotenv import load_dotenv

# ── Thread-safe stdout 리다이렉터 ─────────────────────────────────────────────
_thread_local = threading.local()
_real_stdout = sys.stdout  # 원본 stdout 보존


class _GuiStdout(io.TextIOBase):
    """write()를 호출한 thread가 GUI callback을 등록했으면 GUI 로그로,
    아니면 원본 stdout으로 출력합니다."""

    def write(self, s):
        cb = getattr(_thread_local, "log_callback", None)
        if cb and s.strip():
            cb(s.rstrip())
        elif _real_stdout is not None:
            _real_stdout.write(s)
        return len(s)

    def flush(self):
        if _real_stdout is not None:
            _real_stdout.flush()


sys.stdout = _GuiStdout()

load_dotenv()
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("블로그 자동화  돈·건강·AI 이야기")
        self.geometry("700x620")
        self.resizable(True, True)
        self.configure(bg="#f8fafc")
        self._build_ui()
        self._check_api_key()

    def _build_ui(self):
        # ── 헤더 ────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#3b82f6", height=60)
        header.pack(fill="x")
        tk.Label(header, text="📝 블로그 자동화 시스템",
                 font=("맑은 고딕", 18, "bold"), fg="white", bg="#3b82f6").pack(
                 side="left", padx=20, pady=12)

        # ── 입력 영역 ─────────────────────────────────────────────
        form = tk.Frame(self, bg="#f8fafc", padx=20, pady=15)
        form.pack(fill="x")

        # API 키
        tk.Label(form, text="API 키:", bg="#f8fafc", font=("맑은 고딕", 11)).grid(
            row=0, column=0, sticky="w", pady=4)
        self.api_var = tk.StringVar(value=os.getenv("ANTHROPIC_API_KEY", ""))
        api_entry = tk.Entry(form, textvariable=self.api_var, show="*", width=55,
                             font=("Consolas", 10))
        api_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)

        # 주제
        tk.Label(form, text="주제:", bg="#f8fafc", font=("맑은 고딕", 11)).grid(
            row=1, column=0, sticky="w", pady=4)
        self.topic_var = tk.StringVar()
        tk.Entry(form, textvariable=self.topic_var, width=55,
                 font=("맑은 고딕", 11)).grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        # 키워드
        tk.Label(form, text="키워드:", bg="#f8fafc", font=("맑은 고딕", 11)).grid(
            row=2, column=0, sticky="w", pady=4)
        self.kw_var = tk.StringVar()
        tk.Entry(form, textvariable=self.kw_var, width=40,
                 font=("맑은 고딕", 11)).grid(row=2, column=1, sticky="ew", pady=4)
        tk.Label(form, text="(선택)", bg="#f8fafc", font=("맑은 고딕", 9),
                 fg="gray").grid(row=2, column=2, sticky="w")

        # 저장 경로
        tk.Label(form, text="저장 폴더:", bg="#f8fafc", font=("맑은 고딕", 11)).grid(
            row=3, column=0, sticky="w", pady=4)
        self.out_var = tk.StringVar(value=str(BASE_DIR / "outputs"))
        tk.Entry(form, textvariable=self.out_var, width=42,
                 font=("맑은 고딕", 10)).grid(row=3, column=1, sticky="ew", pady=4)
        tk.Button(form, text="찾아보기", command=self._browse,
                  bg="#e5e7eb", font=("맑은 고딕", 9)).grid(row=3, column=2, padx=6, pady=4)

        form.columnconfigure(1, weight=1)

        # ── 버튼 영역 ─────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg="#f8fafc")
        btn_frame.pack(fill="x", padx=20, pady=5)

        self.run_btn = tk.Button(
            btn_frame, text="▶  글 생성 시작",
            command=self._start,
            bg="#3b82f6", fg="white",
            font=("맑은 고딕", 13, "bold"),
            relief="flat", padx=20, pady=8,
            activebackground="#2563eb"
        )
        self.run_btn.pack(side="left")

        self.open_btn = tk.Button(
            btn_frame, text="📂 저장 폴더 열기",
            command=self._open_output,
            bg="#22c55e", fg="white",
            font=("맑은 고딕", 11),
            relief="flat", padx=14, pady=8,
            activebackground="#16a34a"
        )
        self.open_btn.pack(side="left", padx=10)

        self.topics_btn = tk.Button(
            btn_frame, text="📋 topics.json 처리",
            command=self._run_auto,
            bg="#f59e0b", fg="white",
            font=("맑은 고딕", 11),
            relief="flat", padx=14, pady=8,
        )
        self.topics_btn.pack(side="left")

        # ── 로그 영역 ─────────────────────────────────────────────
        tk.Label(self, text="실행 로그", bg="#f8fafc",
                 font=("맑은 고딕", 10, "bold")).pack(anchor="w", padx=20)
        self.log = scrolledtext.ScrolledText(
            self, height=18, font=("Consolas", 10),
            bg="#1e293b", fg="#e2e8f0",
            insertbackground="white"
        )
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # ── 상태바 ────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="준비")
        tk.Label(self, textvariable=self.status_var, bg="#e5e7eb",
                 font=("맑은 고딕", 9), anchor="w").pack(fill="x")

    def _check_api_key(self):
        if not os.getenv("ANTHROPIC_API_KEY"):
            self.log_msg("⚠️  API 키가 없습니다. 위에 API 키를 입력하세요.\n")

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.out_var.set(d)

    def _open_output(self):
        path = self.out_var.get()
        if os.path.exists(path):
            os.startfile(path) if sys.platform == "win32" else os.system(f"xdg-open '{path}'")
        else:
            messagebox.showwarning("폴더 없음", f"폴더가 없습니다:\n{path}")

    def log_msg(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _start(self):
        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showwarning("주제 필요", "주제를 입력해주세요.")
            return
        self._run_thread(topic=topic, keyword=self.kw_var.get().strip())

    def _run_auto(self):
        self._run_thread(topic=None, keyword=None)

    def _save_api_key(self, api_key: str):
        """API 키를 .env 파일에 저장"""
        env_path = BASE_DIR / ".env"
        env_path.write_text(f"ANTHROPIC_API_KEY={api_key}\n", encoding="utf-8")

    def _run_thread(self, topic, keyword):
        api_key = self.api_var.get().strip()
        if not api_key:
            messagebox.showerror("API 키 없음",
                "API 키를 입력해주세요.\n\n"
                "GUI 상단 'API 키' 입력란에\n"
                "sk-ant-... 로 시작하는 키를 붙여넣으세요.")
            return

        # API 키 환경변수 설정 + .env 저장 (다음 실행부터 자동 입력)
        os.environ["ANTHROPIC_API_KEY"] = api_key
        self._save_api_key(api_key)

        self.run_btn.config(state="disabled")
        self.topics_btn.config(state="disabled")
        self.log.delete("1.0", "end")
        self.status_var.set("실행 중...")

        app_ref = self  # 클로저용 참조

        def worker():
            # 이 thread에서만 GUI 로그 콜백 등록 (thread-local)
            def _cb(msg):
                app_ref.after(0, lambda m=msg: app_ref.log_msg(m))
            _thread_local.log_callback = _cb

            try:
                from run import run
                run(topic=topic, keyword=keyword, output_dir=app_ref.out_var.get())

                app_ref.after(0, lambda: app_ref.status_var.set("✅ 완료!"))
                app_ref.after(0, lambda: messagebox.showinfo(
                    "완료", "글 생성이 완료됐습니다!\n저장 폴더를 열어서 파일을 확인하세요."))
                app_ref.after(0, app_ref._open_output)
            except Exception as e:
                import traceback
                err = traceback.format_exc()
                app_ref.after(0, lambda: app_ref.log_msg(f"\n❌ 오류: {e}\n{err}"))
                app_ref.after(0, lambda: app_ref.status_var.set(f"오류: {e}"))
            finally:
                _thread_local.log_callback = None
                app_ref.after(0, lambda: app_ref.run_btn.config(state="normal"))
                app_ref.after(0, lambda: app_ref.topics_btn.config(state="normal"))

        t = threading.Thread(target=worker, daemon=True)
        t.start()


if __name__ == "__main__":
    try:
        app = BlogApp()
        app.mainloop()
    except Exception as e:
        import traceback
        # tkinter가 없거나 초기화 실패 시 에러를 파일로 저장
        err_path = Path(__file__).parent / "error_log.txt"
        with open(err_path, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        try:
            import tkinter.messagebox as mb
            mb.showerror("시작 오류", f"{e}\n\n자세한 내용: {err_path}")
        except Exception:
            pass
        input(f"오류 발생: {e}\n자세한 내용은 error_log.txt를 확인하세요.\n엔터를 눌러 종료...")
        raise
