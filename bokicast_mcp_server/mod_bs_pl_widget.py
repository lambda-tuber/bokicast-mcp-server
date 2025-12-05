from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QTimer
import sys
from typing import Any, Dict, List
import yaml
import json

# 💡 AccountEntryWidget を別のファイルからインポートします
from bokicast_mcp_server.mod_account_entry_widget import AccountEntryWidget
from bokicast_mcp_server.mod_t_account_widget import TAccountWidget

import logging
logger = logging.getLogger(__name__)

# --------------------------------------------------------
# TAccountWidget
# --------------------------------------------------------
class BsPlWidget(QFrame):
    BASE_HEIGHT = 250

    def __init__(self, parent, font: QFont, account_dict: dict[str, TAccountWidget], conf: dict[str, Any]):
        super().__init__(parent)
        self.font = font
        self.fm = QFontMetrics(self.font)
        self.conf = conf
        self.account_dict = account_dict

        self.assets = AccountEntryWidget(parent, "資産", font, "#92D9C9")
        self.liabilities = AccountEntryWidget(parent, "負債", font, "#F6A6A6")
        self.equity = AccountEntryWidget(parent, "純資産", font, "#A8B2F0")
        self.expense = AccountEntryWidget(parent, "費用", font, "#F7CE9D")
        self.revenue = AccountEntryWidget(parent, "収益", font, "#C6E49F")

        # 初期位置設定

        self._update_bspl_balance()
        self.asset_base_amount = self.assets.get_total_amount()
        self._update_bspl()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        widget_size = self.assets.size()
        center_x = (screen_geometry.width() - widget_size.width()) // 2
        center_y = (screen_geometry.height() - widget_size.height()) // 2
        self.assets.move(center_x, center_y)
        self.expense.move(self.assets.x(), self.assets.y() + self.assets.height()+20)

        self.update_bspl_timer = QTimer()
        self.update_bspl_timer.timeout.connect(lambda: self._update_bspl())
        self.update_bspl_timer.start(1000)

        self.update_bs_pos_timer = QTimer()
        self.update_bs_pos_timer.timeout.connect(lambda: self._update_bs_pos())
        self.update_bs_pos_timer.start(200)

        self.update_pl_pos_timer = QTimer()
        self.update_pl_pos_timer.timeout.connect(lambda: self._update_pl_pos())
        self.update_pl_pos_timer.start(200)

        self.assets.show()
        self.liabilities.show()
        self.equity.show()
        self.expense.show()
        self.revenue.show()


        # ダブルクリックハンドラ接続
        self.assets.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.assets, row, col)
        )
        self.liabilities.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.liabilities, row, col)
        )
        self.equity.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.equity, row, col)
        )
        self.expense.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.expense, row, col)
        )
        self.revenue.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.revenue, row, col)
        )

    def _update_bspl(self):
        self._update_bspl_balance()
        self._update_bspl_widths()
        self._update_bspl_height()

    def _update_bspl_balance(self):
        accounts_conf = self.conf.get('勘定', {})

        self._add_balances_to_entry_widget(
            category_name='資産', 
            entry_widget=self.assets, 
            accounts_list=accounts_conf.get('資産', [])
        )

        self._add_balances_to_entry_widget(
            category_name='負債', 
            entry_widget=self.liabilities, 
            accounts_list=accounts_conf.get('負債', [])
        )
        
        self._add_balances_to_entry_widget(
            category_name='純資産', 
            entry_widget=self.equity, 
            accounts_list=accounts_conf.get('純資産', [])
        )

        self._add_balances_to_entry_widget(
            category_name='費用', 
            entry_widget=self.expense, 
            accounts_list=accounts_conf.get('費用', [])
        )

        self._add_balances_to_entry_widget(
            category_name='収益', 
            entry_widget=self.revenue, 
            accounts_list=accounts_conf.get('収益', [])
        )
        

    def _add_balances_to_entry_widget(self, category_name: str, entry_widget: AccountEntryWidget, accounts_list: List[str]):
        """
        特定のカテゴリに属する勘定科目の残高を取得し、対応する AccountEntryWidget に追加します。
        """
        #entry_widget.clear_all()

        for account_name in accounts_list:
            # account_dictに該当するTAccountWidgetが存在するか確認
            if account_name in self.account_dict:
                t_account = self.account_dict[account_name]
                
                # TAccountWidgetから現在の残高を取得
                balance = t_account.get_balance()
                if category_name == '負債' or category_name == '純資産' or category_name == '収益':
                    balance = abs(balance)

                entry_widget.update_item(account_name, balance)
                
                # 残高が0でない場合にのみ追加（任意だが、通常ゼロ残高は表示しない）
                # if balance != 0:
                #     entry_widget.update_item(account_name, balance)
                # else:
                #     logger.debug(f"{account_name} の残高は0のためスキップ。")
            else:
                logger.debug(f"TAccountWidget ({account_name}) が account_dict に見つかりません。")

    def _update_bs_pos(self):
        # 1. Assetsの位置は固定
        assets_x = self.assets.x()
        assets_y = self.assets.y()
        
        # 2. Liabilitiesの位置を決定 (Assetsに右隣で隙間なく追従)
        
        # X座標: Assetsの右端に隣接
        liabilities_x = assets_x + self.assets.width() 
        # Y座標: Assetsと同じ高さ (上揃え)
        liabilities_y = assets_y
        
        self.liabilities.move(liabilities_x, liabilities_y)
        
        # 3. Equityの位置を決定 (Liabilitiesの真下に隙間なく追従)
        
        # X座標: Liabilitiesと同じX座標
        equity_x = liabilities_x
        # 🌟 変更点: PADDING_Y の参照を削除 🌟
        # Y座標: Liabilitiesの下端に隣接
        equity_y = liabilities_y + self.liabilities.height()
        
        self.equity.move(equity_x, equity_y)


    def _update_pl_pos(self):
        # 1. Expense の位置（左側）
        expense_x = self.expense.x()
        expense_y = self.expense.y()
        expense_h = self.expense.height()

        # 2. Revenue の高さを取得
        revenue_h = self.revenue.height()

        # --- 下揃えにする ---
        # Expense の下端
        expense_bottom = expense_y + expense_h
        # Revenue の y は「下端 - 自身の高さ」
        revenue_y = expense_bottom - revenue_h

        # X座標は右隣
        revenue_x = expense_x + self.expense.width()

        # 移動
        self.revenue.move(revenue_x, revenue_y)

    def _update_bspl_widths(self):
        """
        渡されたすべてのウィジェットの中で最大の幅を計算し、全ウィジェットにその幅を適用します。
        """
        widgets = [self.assets, self.liabilities, self.equity, self.expense, self.revenue]

        max_widths = [w.get_max_column_width() for w in widgets]
        
        unified_width = max(max_widths)
        
        for w in widgets:
            w.set_fixed_column_width(unified_width)

    def _update_bspl_height(self):
        """
        資産の基準高 (BASE_HEIGHT) と基準合計額 (asset_base_amount) を基に、
        各勘定科目ウィジェットの高さを動的に設定します。
        """
        
        if self.asset_base_amount == 0:
            logger.debug("asset_base_amountがゼロです。高さの計算をスキップします。")
            return
 
        minimum_height = self.assets.get_minimum_height()

        # 1. 各ウィジェットの合計金額を取得 (get_total_amount() は AccountEntryWidget に存在すると仮定)
        
        # 資産の合計金額
        total_assets = self.assets.get_total_amount()
        # 負債の合計金額
        total_liabilities = self.liabilities.get_total_amount()
        # 純資産の合計金額
        total_equity = self.equity.get_total_amount()
        # 費用の合計金額
        total_expense = self.expense.get_total_amount()
        # 収益の合計金額
        total_revenue = self.revenue.get_total_amount()

        # 2. 資産ウィジェットの高さ計算と設定
        # 資産は、基準金額と基準高さを基に計算されます。
        # 計算式: (現在の合計金額 / 基準合計金額) * 基準高さ
        asset_height = int((total_assets / self.asset_base_amount) * self.BASE_HEIGHT)
        self.assets.setFixedHeight(asset_height)
        logger.debug(f"Assets height set to: {asset_height}")

        # 3. 負債ウィジェットの高さ計算と設定
        # 負債の高さも、資産の基準を基に計算されます。
        liabilities_height = int((total_liabilities / self.asset_base_amount) * self.BASE_HEIGHT)
        self.liabilities.setFixedHeight(liabilities_height)
        logger.debug(f"Liabilities height set to: {liabilities_height}")

        # 4. 純資産ウィジェットの高さ計算と設定
        equity_height = int((total_equity / self.asset_base_amount) * self.BASE_HEIGHT)
        self.equity.setFixedHeight(equity_height)
        logger.debug(f"Equity height set to: {equity_height}")

        geta = max(self.expense.get_needed_height(), self.revenue.get_needed_height());

        # 5. 費用ウィジェットの高さ計算と設定
        # 費用は、基準金額と基準高さを基に計算されます。
        # 計算式: (現在の合計金額 / 基準合計金額) * 基準高さ
        expense_height = int((total_expense / self.asset_base_amount) * self.BASE_HEIGHT)
        self.expense.setFixedHeight(expense_height + geta)
        logger.debug(f"Expense height set to: {expense_height} + {geta}")

        # 6. 収益ウィジェットの高さ計算と設定
        # 収益の高さも、費用の基準を基に計算されます。
        revenue_height = int((total_revenue / self.asset_base_amount) * self.BASE_HEIGHT)
        self.revenue.setFixedHeight(revenue_height + geta)
        logger.debug(f"Revenue height set to: {revenue_height} + {geta}")

    # ----------------------------------------------------
    # マウスイベント
    # ----------------------------------------------------
    def _on_account_clicked(self, section_widget, row, col):
        """
        どのセクション（資産/負債/純資産）で
        どの行がダブルクリックされたかを受け取る
        """
        # 勘定科目名は常に column 0
        account_name_item = section_widget.table.item(row, 0)
        if not account_name_item:
            return

        account_name = account_name_item.text().strip()
        t = self.account_dict.get(account_name)

        if not t:
            logger.debug(f"T勘定が存在しません: {account_name}")
            return

        # -------------------------
        #   すでに表示中 → 非表示
        # -------------------------
        if t.isVisible():
            t.hide()
            logger.debug(f"[BS] {account_name} → 非表示")
            return

        # -------------------------
        #     位置合わせ（DPI対応）
        # -------------------------

        # テーブル上のセルの矩形（ローカル座標）
        cell_rect = section_widget.table.visualItemRect(account_name_item)

        # セルの左下ローカル座標
        local_pos = cell_rect.bottomLeft()

        # テーブル→グローバル座標（物理座標）
        global_pos = section_widget.table.mapToGlobal(local_pos)

        # DPI倍率（物理→論理変換に必要）
        dpr = self.window().devicePixelRatio()

        # グローバル物理座標 → 親ウィジェットの論理座標へ補正
        logical_global_pos = QPoint(
            int(global_pos.x() / dpr),
            int(global_pos.y() / dpr)
        )

        # 親座標へ変換（論理座標 → 論理座標）
        parent_pos = t.parent().mapFromGlobal(logical_global_pos)

        # 最終移動
        t.move(global_pos)
        t.show()
        t.raise_()

        logger.debug(f"[BS] {account_name} → 表示@local_pos:{local_pos}, global_pos:{global_pos}, logical_global_pos:{logical_global_pos}, parent_pos:{parent_pos}, dpr:{dpr} ")
        

    def get_bs_data(self):
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
        data = {
                    "資産": self._collect_category_dict("資産"),
                    "負債": self._collect_category_dict("負債"),
                    "純資産": self._collect_category_dict("純資産")
                }
        
        return json.dumps(data, ensure_ascii=False, indent=4)


    def get_pl_data(self):
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

        data = {
                    "費用": self._collect_category_dict("費用"),
                    "収益": self._collect_category_dict("収益")
                }

        return json.dumps(data, ensure_ascii=False, indent=4)

    def _collect_category_dict(self, category_name: str) -> Dict[str, int]:
        """
        指定されたカテゴリの勘定科目と残高の辞書を作成するヘルパーメソッド
        形式: {"科目名": 金額, ...}
        """
        result = {}
        accounts_list = self.conf.get('勘定', {}).get(category_name, [])

        for account_name in accounts_list:
            if account_name in self.account_dict:
                t_account = self.account_dict[account_name]
                balance = t_account.get_balance()

                # 負債・純資産・収益は貸方(マイナス)で管理されているため絶対値にする
                if category_name in ['負債', '純資産', '収益']:
                    balance = abs(balance)

                # 残高が0でない場合のみ追加
                if balance != 0:
                    result[account_name] = balance
        
        return result


# --------------------------------------------------------
# 動作テスト
# --------------------------------------------------------
if __name__ == "__main__":
    yaml_file = "C:\\work\\lambda-tuber\\bokicast-mcp-server\\bokicast-mcp-server.yaml"
    config = {}
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    logger.debug(config)

    account_to_category: Dict[str, str] = {}
    for category, accounts in config.get('勘定', {}).items():
        for account in accounts:
            account_to_category[account] = category

    app = QApplication(sys.argv)
    

    main_widget = QWidget()
    main_widget.setWindowTitle("Main Container (Floater Test)")
    main_widget.setGeometry(0, 0, 100, 50)
    main_widget.setStyleSheet("background-color: #F0F0F0;")
    

    font = QFont("MS Gothic", 10)
    account_dict: Dict[str, TAccountWidget] = {}
    trial_balance_data = config.get('決算整理前残高試算表', {})
    for account_name, initial_balance in trial_balance_data.items():
        t_account = TAccountWidget(main_widget, account_name, font)
        account_dict[account_name] = t_account

        if initial_balance == 0:
            logger.debug(f"  -> {account_name}: 残高が0のためスキップ")
            continue

        category = account_to_category.get(account_name)

        if category == '資産' or category == '費用':
            t_account.add_debit("期首残高", initial_balance)
        elif category == '負債' or category == '純資産' or category == '収益':
            t_account.add_credit("期首残高", initial_balance)
        else:
            logger.debug(f"  -> {account_name}: 勘定カテゴリ ({category}) が不明。期首残高は未登録。")



    bspl = BsPlWidget(main_widget, font, account_dict, config)
    
    main_widget.show()

    print(bspl.get_bs_data())
    print(bspl.get_pl_data())

    sys.exit(app.exec())