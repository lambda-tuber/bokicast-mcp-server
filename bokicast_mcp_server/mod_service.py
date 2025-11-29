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
_avatar_enbled = False


#
# MCP I/F
#
@mcp.tool()
async def speak(
    style_id: int,
    msg: str,
    speedScale: float = 1.0,
    pitchScale: float = 0.0,
    intonationScale: float = 1.0,
    volumeScale: float = 1.0
) -> str:
    """
    詳細オプションを指定して、VOICEVOXで音声合成し、音声を再生する。
    
    Args:
        style_id: voicevox 発話音声を指定するID(必須)
        msg: 発話するメッセージ(必須)
        speedScale: 話速。デフォルト 1.0
        pitchScale: 声の高さ。デフォルト 0.0
        intonationScale: 抑揚の強さ。デフォルト 1.0
        volumeScale: 音量。デフォルト 1.0
    
    Returns:
        str: 実行結果メッセージ
    """
    try:
        # mod_speakのspeak関数を呼び出し
        mod_speak.speak(
            style_id=style_id,
            msg=msg,
            speedScale=speedScale,
            pitchScale=pitchScale,
            intonationScale=intonationScale,
            volumeScale=volumeScale
        )
        return f"音声合成・再生が完了しました。(style_id={style_id})"
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
    bokicast_mcp_server.mod_bokicast_manager.setup(conf) 
    sys.exit(app.exec())

def start_mcp(conf: dict[str, Any]):
    logger.info("start_mcp called.")
    mcp.run(transport="stdio")


