"""
MCP Server service module
MCPサーバクラスとToolsを定義する
"""
import json
import sys
from typing import Any
from threading import Thread
import logging
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

import mod_bokicast_service

# ロガーの設定
logger = logging.getLogger(__name__)

#
# global settings
#
mcp = FastMCP("bokicast-mcp-server")
_config = None


#
# MCP I/F
#
@mcp.tool()
async def journal_entry(
    journal_data: Dict[str, Any]
) -> str:
    """
    仕訳データを受け取り、会計処理（JournalEntryWidgetの表示など）を実行します。

    Args:
        journal_data (dict): 実行する仕訳の詳細データを含む辞書。
                             
                             以下の構造を持ちます:
                             - journal_id (str): 仕訳のユニークID (例: "J-004")。
                             - debit (list[dict]): 借方項目（勘定科目と金額）のリスト。
                             - credit (list[dict]): 貸方項目（勘定科目と金額）のリスト。
                             - remarks (str, optional): 摘要/備考。

    Data Example:
    {
        "journal_id": "J-004",
        "debit": [
            {"account": "仕入", "amount": 1000},
            {"account": "荷役費", "amount": 500},
            {"account": "雑費", "amount": 500}
        ],
        "credit": [
            {"account": "買掛金", "amount": 2000}
        ],
        "remarks": "仕訳ID004の例"
    }

    Returns:
        str: 実行結果メッセージ
    """
    try:

        journal_data = {
            "journal_id": "J-004", # 👈 journal_id を追加
            "debit": [
                {"account": "仕入", "amount": 1000},
                {"account": "荷役費", "amount": 500},
                {"account": "雑費", "amount": 500}
            ],
            "credit": [
                {"account": "買掛金", "amount": 2000}
            ],
            "remarks": "仕訳ID004の例"
        }

        bokicast = BokicastService.instance()
        QMetaObject.invokeMethod(bokicast, "journal_entry", Qt.ConnectionType.QueuedConnection, Q_ARG(dict, journal_data))

        return f"簿記キャストが完了しました。仕訳表と関連するT勘定が表示されました。"

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


#
# public function
#
def start(conf: dict[str, Any]):
    """stdio モードで FastMCP を起動"""
    global _config 

    _config = conf

    logger.debug(conf)

    Thread(target=start_mcp, args=(conf,), daemon=True).start()

    app = QApplication(sys.argv) 
    mod_bokicast_service.BokicastService.instance(conf) 
    sys.exit(app.exec())

def start_mcp(conf: dict[str, Any]):
    logger.info("start_mcp called.")
    mcp.run(transport="stdio")


