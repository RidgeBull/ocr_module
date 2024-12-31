import os
import logging
import time
from pathlib import Path


def setup_function_logger(function_name: str) -> logging.Logger:
    """関数ごとの実行時間ロガーを設定"""
    logger = logging.getLogger(f"performance.{function_name}")
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ログディレクトリ作成
    log_dir = Path("logs/performance")
    log_dir.mkdir(parents=True, exist_ok=True)

    # CSVファイルのパス
    log_file = log_dir / f"{function_name}.csv"

    # ファイルが存在する場合は削除
    if log_file.exists():
        log_file.unlink()

    # CSVファイル用のハンドラを作成
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "%(asctime)s,%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
