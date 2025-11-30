"""
MCP Server service module
MCPサーバクラスとToolsを定義する
"""
import json
import sys
from typing import Any, Dict
from threading import Thread
import logging
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QMetaObject, Qt, QTimer
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

from bokicast_mcp_server.mod_bokicast_service import BokicastService


import logging
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
    journal_data: str
) -> str:
    """
    仕訳データを受け取り、会計処理（JournalEntryWidgetの表示など）を実行します。

    Args:
        journal_data (文字列): 実行する仕訳の詳細データを含むJSONデータ文字列。
                             
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
        logger.info("journal entry tool called.")
        logger.info(journal_data)

        # journal_data = {
        #     "journal_id": "J-004", # 👈 journal_id を追加
        #     "debit": [
        #         {"account": "仕入", "amount": 1000},
        #         {"account": "荷役費", "amount": 500},
        #         {"account": "雑費", "amount": 500}
        #     ],
        #     "credit": [
        #         {"account": "買掛金", "amount": 2000}
        #     ],
        #     "remarks": "仕訳ID004の例"
        # }

        bokicast = BokicastService.instance(_config)
        QMetaObject.invokeMethod(bokicast, "journal_entry", Qt.ConnectionType.QueuedConnection, Q_ARG(str, journal_data))

        return f"簿記キャストが完了しました。仕訳表と関連するT勘定が表示されました。"

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


#
# MCP I/F
#
@mcp.tool()
async def get_bs() -> str:
    """
    貸借対照表データ(JSONデータ文字列)を返します。

    Args: なし
    Returns: 
        str: 貸借対照表データ(JSONデータ文字列)
        Data Example:
        {
            "資産": {
                "現金": 150000,
                "売掛金": 50000,
                "備品": 80000
            },
            "負債": {
                "買掛金": 60000,
                "短期借入金": 40000
            },
            "純資産": {
                "資本金": 100000,
                "利益剰余金": 90000
            }
        }

    """
    try:
        logger.info("get_bs tool called.")

        bokicast = BokicastService.instance(_config)
        return bokicast.get_bs_data()

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


#
# MCP I/F
#
@mcp.tool()
async def get_pl() -> str:
    """
    損益計算書データ(JSONデータ文字列)を返します。

    Args: なし
    Returns: 
        str: 損益計算書データ(JSONデータ文字列)
        Data Example:
        {
            "費用": {
                "仕入": 100000,
                "荷役費": 5000,
                "雑費": 2000
            },
            "収益": {
                "売上高": 150000,
                "雑収入": 3000
            }
        }
    """
    try:
        logger.info("get_pl tool called.")

        bokicast = BokicastService.instance(_config)
        return bokicast.get_pl_data()

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


#
# MCP I/F
#
@mcp.tool()
async def get_t_account(accout_name: str) -> str:
    """
    T字勘定の借方、貸方データ(JSONデータ文字列)を返します。

    Args: なし
    Returns: 
        str: T字勘定の借方、貸方データ(JSONデータ文字列)
        Data Example:
        {
            "勘定": "売上" 
            "借方": [
                {"ラベル": "J001-仕入", "金額": 100000},
                {"ラベル": "J002", "金額": 5000},
                {"ラベル": "J003-雑費", "金額": 2000}
            ],
            "貸方": [
                {"ラベル": "J003-売上高", "金額": 150000},
                {"ラベル": "J004", "金額": 3000}
            ],
            "残高": 200000
        }
    """
    try:
        logger.info("get_pl tool called.")

        bokicast = BokicastService.instance(_config)
        return bokicast.get_account_data(accout_name) 

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


#
# public function
#
def start(conf: dict[str, Any]):
    logger.info("mod_service.start called.")

    """stdio モードで FastMCP を起動"""
    global _config 

    _config = conf

    logger.debug(conf)

    logger.info("QT thread start.")
    app = QApplication(sys.argv) 

    BokicastService.instance(conf) 
    
    logger.info("mcp thread start.")
    Thread(target=start_mcp, args=(conf,), daemon=True).start()

    sys.exit(app.exec())

def start_mcp(conf: dict[str, Any]):
    logger.info("start_mcp called.")
    mcp.run(transport="stdio")


