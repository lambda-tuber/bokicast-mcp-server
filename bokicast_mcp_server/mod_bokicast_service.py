import sys
import yaml
from typing import Any
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Slot
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint

from mod_t_account_widget import TAccountWidget
from mod_journal_entry_widget import JournalEntryWidget
from mod_balance_sheet_widget import BalanceSheetWidget

# ロガーの設定
logger = logging.getLogger(__name__)

class BokicastService(QWidget):
    _instance = None

    @classmethod
    def instance(cls, conf: dict[str, Any]):
        if cls._instance is None:
            cls._instance = cls(conf)
            
        return cls._instance

    def __init__(self, conf: dict[str, Any]):
        if BokicastService._instance is not None:
            return 

        super().__init__()
        self.conf = conf
        logger.info(f"BokicastService.__init__: called.")
        self.account_dict: dict[str, TAccountWidget] = {}

        self.main_widget = QWidget()
        self.main_widget.setWindowTitle("Bokicast MCP Server")
        self.main_widget.setStyleSheet("background-color: #F0F0F0;")
        # self.main_widget.setWindowFlags(
        #     Qt.Window | 
        #     Qt.FramelessWindowHint | 
        #     Qt.WindowStaysOnTopHint
        # )
        self.main_widget.setGeometry(0, 0, 500, 10)
        self.main_widget.move(0, 100)
        self.main_widget.show()
        self.font = QFont("MS Gothic", 10)

        self.setup_account_dict(conf)
        self.bs = BalanceSheetWidget(self.main_widget, self.font, self.account_dict, self.conf)

    def setup_account_dict(self, conf: dict[str, Any]):
        account_to_category: Dict[str, str] = {}
        for category, accounts in conf.get('勘定', {}).items():
            for account in accounts:
                account_to_category[account] = category

        trial_balance_data = conf.get('決算整理前残高試算表', {})
        for account_name, initial_balance in trial_balance_data.items():
            t_account = TAccountWidget(self.main_widget, account_name, self.font)
            self.account_dict[account_name] = t_account

            if initial_balance == 0:
                print(f"  -> {account_name}: 残高が0のためスキップ")
                continue

            category = account_to_category.get(account_name)

            if category == '資産' or category == '費用':
                t_account.add_debit("期首残高", initial_balance)
            elif category == '負債' or category == '純資産' or category == '収益':
                t_account.add_credit("期首残高", initial_balance)
            else:
                print(f"  -> {account_name}: 勘定カテゴリ ({category}) が不明。期首残高は未登録。")


    #
    # セッター
    #
    @Slot(dict)
    def journal_entry(self, journal_data: dict):
        """
        仕訳データを受け取り、JournalEntryWidgetを生成して表示します。

        journal_data = {
            "journal_id" : "J-004",
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
        """

        journal_id = journal_data.get("journal_id", "NO_ID")
        logger.info(f"journal_entry: Processing Journal ID: {journal_id}")
        
        j = JournalEntryWidget(self.main_widget, journal_id, self.font, self.account_dict)
        
        main_x = self.main_widget.x()
        main_y = self.main_widget.y()
        j.move(main_x + 30, main_y + 30)
        j.show()
        
        j.add_journal(journal_data)


if __name__ == "__main__":

    yaml_file = "C:\\work\\lambda-tuber\\bokicast-mcp-server\\bokicast-mcp-server.yaml"
    config = {}
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    app = QApplication(sys.argv)
    s = BokicastService.instance(config)

    # 渡すべき仕訳データの例を定義
    test_journal_data = {
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

    # 修正: 辞書データを渡す
    s.journal_entry(test_journal_data) 
    
    sys.exit(app.exec())