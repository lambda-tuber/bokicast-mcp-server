import sys
import yaml
import json
from typing import Any, List, Dict
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Slot, QEvent
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint

from bokicast_mcp_server.mod_t_account_widget import TAccountWidget
from bokicast_mcp_server.mod_journal_entry_widget import JournalEntryWidget
from bokicast_mcp_server.mod_bs_pl_widget import BsPlWidget


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
        self.ledger_dict = {}
        self.bspl_widget_dict = {}
        self.journal_dict: dict[str, JournalEntryWidget] = {}
        self.main_widget = QWidget()
        self.main_widget.setWindowTitle("Bokicast MCP Server")
        self.main_widget.setStyleSheet("background-color: #F0F0F0;")
        self.main_widget.setWindowFlags(
            Qt.Window | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.main_widget.setGeometry(0, 0, 500, 10)
        self.main_widget.move(0, 100)
        font_type = self.conf.get("フォント", {}).get("種別", "MS Gothic")
        font_size = self.conf.get("フォント", {}).get("サイズ", 14)
        self.font = QFont(font_type, font_size)


        self.ledger_dict["前期"] = self.get_account_dict("期首残高試算表")
        self.pre_bspl = BsPlWidget(self.main_widget, self.font, self.ledger_dict["前期"], "前期")
        self.bspl_widget_dict["前期"] = self.pre_bspl

        self.ledger_dict["当期"] = self.get_account_dict("期首残高試算表")
        self.cur_bspl = BsPlWidget(self.main_widget, self.font, self.ledger_dict["当期"], "")
        self.cur_bspl.assets.header_label.installEventFilter(self)
        self.bspl_widget_dict["当期"] = self.cur_bspl


    def get_account_dict(self, target_set):
        opening_balances = self.conf.get(target_set, {})
        account_dict = {}
        for category, accounts_data in opening_balances.items():
            # データ形式のチェック (念のため)
            if not isinstance(accounts_data, dict):
                logger.warning(f"カテゴリ '{category}' のデータ形式が不正です。辞書形式である必要があります。")
                continue

            for account_name, initial_balance in accounts_data.items():
                # 1. TAccountWidget の作成と登録
                #    残高が0でも、取引で使用する可能性があるためウィジェット自体は作成します
                t_account = TAccountWidget(self.main_widget, account_name, self.font, self.journal_dict, category)
                account_dict[account_name] = t_account

                # 2. 期首残高の登録処理
                if initial_balance == 0:
                    logger.debug(f"  -> {account_name} ({category}): 残高が0のため期首仕訳の登録はスキップ")
                    continue

                # カテゴリに基づいて 借方(Debit) か 貸方(Credit) かを判断
                if category in ['資産', '費用']:
                    t_account.add_debit("期首残高", initial_balance)
                elif category in ['負債', '純資産', '収益']:
                    t_account.add_credit("期首残高", initial_balance)
                else:
                    logger.warning(f"  -> {account_name}: 未知のカテゴリ '{category}' です。期首残高は未登録。")

        return account_dict

    #
    # セッター
    #
    @Slot(str)
    def journal_entry(self, journal_str: str):
        """
        仕訳データを受け取り、JournalEntryWidgetを生成して表示します。

        journal_data = {
            "journal_id" : "J004",
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
        journal_data = json.loads(journal_str)
        journal_id = journal_data.get("journal_id", "NO_ID")
        logger.info(f"journal_entry: Processing Journal ID: {journal_id}")
        
        account_dict = self.ledger_dict["当期"]
        j = JournalEntryWidget(self.main_widget, journal_id, self.font, account_dict, self.journal_dict)
        self.journal_dict[journal_id] = j

        j.add_journal(journal_data)
        #main_x = self.main_widget.x()
        #main_y = self.main_widget.y()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        center_x = screen_geometry.width() // 2
        center_y = screen_geometry.height() // 2

        j.move(center_x, center_y)
        j.show()

    def get_bs_data(self):
        data = {
                    "前期": self.pre_bspl.get_bs_data(),
                    "当期": self.cur_bspl.get_bs_data()
               }

        return json.dumps(data, ensure_ascii=False, indent=4)

    def get_pl_data(self):
        data = {
                    "前期": self.pre_bspl.get_pl_data(),
                    "当期": self.cur_bspl.get_pl_data()
               }
               
        return json.dumps(data, ensure_ascii=False, indent=4)

    def get_account_data(self, acc_name):

        account_dict = self.ledger_dict["当期"]
        if acc_name not in account_dict:
            logger.warning(f"Account '{acc_name}' not found.")
            return json.dumps({"error": "Account not found"}, ensure_ascii=False)

        t_account = account_dict[acc_name]

        return t_account.get_account_data()



    def eventFilter(self, source, event):
        """
        特定のウィジェットで発生したイベントを横取りして処理します
        """

        # ダブルクリックイベントかどうか確認
        if event.type() == QEvent.MouseButtonDblClick:
            
            # どのラベルがダブルクリックされたか判定
            if source == self.cur_bspl.assets.header_label:
                logger.debug("資産ヘッダーがダブルクリックされました")

                if self.pre_bspl.assets.isVisible():
                    logger.debug("前期BSPLを非表示にする。")
                    self.pre_bspl.hide()
                else:
                    logger.debug("前期BSPLを表示する。")
                    self.pre_bspl.show()

                return True # イベント処理済みとする
        
        return False


if __name__ == "__main__":

    yaml_file = "C:\\work\\lambda-tuber\\bokicast-mcp-server\\bokicast-mcp-server.yaml"
    config = {}
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    app = QApplication(sys.argv)
    s = BokicastService.instance(config)

    test_journal_data = {
        "journal_id": "J004", # 👈 journal_id を追加
        "debit": [
            {"account": "仕入", "amount": 20000},
        ],
        "credit": [
            {"account": "買掛金", "amount": 20000}
        ],
        "remarks": "仕訳ID004の例"
    }

    s.journal_entry(json.dumps(test_journal_data)) 

    test_journal_data = {
        "journal_id": "J005", # 👈 journal_id を追加
        "debit": [
            {"account": "現金", "amount": 40000},
        ],
        "credit": [
            {"account": "売上", "amount": 40000}
        ],
        "remarks": "仕訳ID005の例"
    }

    s.journal_entry(json.dumps(test_journal_data)) 



    # test_journal_data = {
    #     "journal_id": "J005", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "仕入", "amount": 20000},
    #     ],
    #     "credit": [
    #         {"account": "買掛金", "amount": 20000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s = BokicastService.instance(config)
    # s.journal_entry(json.dumps(test_journal_data)) 


    # test_journal_data = {
    #     "journal_id": "J006", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "現金", "amount": 30000},
    #     ],
    #     "credit": [
    #         {"account": "売上", "amount": 30000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s = BokicastService.instance(config)
    # s.journal_entry(json.dumps(test_journal_data)) 

    # test_journal_data = {
    #     "journal_id": "J006", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "現金", "amount": 30000},
    #     ],
    #     "credit": [
    #         {"account": "資本金", "amount": 30000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s = BokicastService.instance(config)
    # s.journal_entry(json.dumps(test_journal_data)) 

    # test_journal_data = {
    #     "journal_id": "J007", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "売上", "amount": 30000},
    #     ],
    #     "credit": [
    #         {"account": "損益", "amount": 30000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s = BokicastService.instance(config)
    # s.journal_entry(json.dumps(test_journal_data)) 

    # test_journal_data = {
    #     "journal_id": "J007", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "損益", "amount": 20000},
    #     ],
    #     "credit": [
    #         {"account": "仕入", "amount": 20000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s.journal_entry(json.dumps(test_journal_data)) 

    # test_journal_data = {
    #     "journal_id": "J008", # 👈 journal_id を追加
    #     "debit": [
    #         {"account": "損益", "amount": 10000},
    #     ],
    #     "credit": [
    #         {"account": "利益剰余金", "amount": 10000},
    #     ],
    #     "remarks": "仕訳ID005の例"
    # }
    # s.journal_entry(json.dumps(test_journal_data)) 

    print(s.get_bs_data())
    print(s.get_pl_data())
    print(s.get_account_data("資本金"))

    sys.exit(app.exec())