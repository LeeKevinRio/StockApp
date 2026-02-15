"""
測試啟動腳本

用法:
    python run_tests.py          # 只跑測試
    python run_tests.py --start  # 測試通過後自動啟動 uvicorn
"""
import sys
import subprocess


def main():
    start_after = "--start" in sys.argv

    print("=" * 60)
    print("  執行測試套件")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "--tb=short", "-q"],
        cwd=sys.path[0] or ".",
    )

    if result.returncode != 0:
        print()
        print("=" * 60)
        print("  測試失敗！請修復上述錯誤後再試。")
        print("=" * 60)
        sys.exit(1)

    print()
    print("=" * 60)
    print("  所有測試通過！")
    print("=" * 60)

    if start_after:
        print()
        print("  啟動伺服器 (port 8000)...")
        print("=" * 60)
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
