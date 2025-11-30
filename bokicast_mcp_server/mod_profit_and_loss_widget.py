from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QTimer
import sys
from typing import Any, Dict, List
import yaml

# 💡 AccountEntryWidget を別のファイルからインポートします
from mod_account_entry_widget import AccountEntryWidget
from mod_t_account_widget import TAccountWidget

# --------------------------------------------------------
# TAccountWidget
# --------------------------------------------------------
class ProfitAndLossWidget(QFrame):
    BASE_HEIGHT = 250

    def __init__(self, parent, font: QFont, account_dict: dict[str, TAccountWidget], conf: dict[str, Any]):
        super().__init__(parent)
        self.font = font
        self.fm = QFontMetrics(self.font)
        self.conf = conf
        self.account_dict = account_dict

        self.expense = AccountEntryWidget(parent, "費用", font, "#92D9C9")
        self.revenue = AccountEntryWidget(parent, "収益", font, "#F6A6A6")

        # 初期位置設定
        self.expense.move(50, 50)

        self._update_bs_balance()
        self.asset_base_amount =self.expense.get_total_amount()
        self._update_bs()

        self.expense.show()
        self.revenue.show()

        self.update_bs_timer = QTimer()
        self.update_bs_timer.timeout.connect(lambda: self._update_bs())
        self.update_bs_timer.start(1000)

        self.update_bs_pos_timer = QTimer()
        self.update_bs_pos_timer.timeout.connect(lambda: self._update_bs_pos())
        self.update_bs_pos_timer.start(200)

        # ダブルクリックハンドラ接続
        self.expense.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.expense, row, col)
        )
        self.revenue.table.cellDoubleClicked.connect(
            lambda row, col: self._on_account_clicked(self.revenue, row, col)
        )


    def _update_bs(self):
        self._update_bs_balance()
        self._update_bs_widths()
        self._update_bs_height()

    def _update_bs_balance(self):
        accounts_conf = self.conf.get('勘定', {})

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
                if category_name == '収益':
                    balance = abs(balance)

                # 残高が0でない場合にのみ追加（任意だが、通常ゼロ残高は表示しない）
                if balance != 0:
                    entry_widget.update_item(account_name, balance)
                else:
                    print(f"{account_name} の残高は0のためスキップ。")
            else:
                print(f"TAccountWidget ({account_name}) が account_dict に見つかりません。")

    def _update_bs_pos(self):
        # 1. Expenseの位置は固定
        expense_x = self.expense.x()
        expense_y = self.expense.y()
        
        # 2. Revenueの位置を決定 (Expenseに右隣で隙間なく追従)
        
        # X座標: Expenseの右端に隣接
        revenue_x = expense_x + self.expense.width() 
        # Y座標: Expenseと同じ高さ (上揃え)
        revenue_y = expense_y
        
        self.revenue.move(revenue_x, revenue_y)
        
    def _update_bs_widths(self):
        """
        渡されたすべてのウィジェットの中で最大の幅を計算し、全ウィジェットにその幅を適用します。
        """
        widgets = [self.expense, self.revenue]

        max_widths = [w.get_max_column_width() for w in widgets]
        
        unified_width = max(max_widths)
        
        for w in widgets:
            w.set_fixed_column_width(unified_width)

    def _update_bspl_height(self):
        """
        費用の基準高 (BASE_HEIGHT) と基準合計額 (asset_base_amount) を基に、
        各勘定科目ウィジェットの高さを動的に設定します。
        """
        
        if self.asset_base_amount == 0:
            print("asset_base_amountがゼロです。高さの計算をスキップします。")
            return

        # 1. 各ウィジェットの合計金額を取得 (get_total_amount() は AccountEntryWidget に存在すると仮定)
        
        # 費用の合計金額
        total_expense = self.expense.get_total_amount()
        # 収益の合計金額
        total_revenue = self.revenue.get_total_amount()

        # 2. 費用ウィジェットの高さ計算と設定
        # 費用は、基準金額と基準高さを基に計算されます。
        # 計算式: (現在の合計金額 / 基準合計金額) * 基準高さ
        asset_height = int((total_expense / self.asset_base_amount) * self.BASE_HEIGHT)
        self.expense.setFixedHeight(asset_height)
        print(f"Expense height set to: {asset_height}")

        # 3. 収益ウィジェットの高さ計算と設定
        # 収益の高さも、費用の基準を基に計算されます。
        revenue_height = int((total_revenue / self.asset_base_amount) * self.BASE_HEIGHT)
        self.revenue.setFixedHeight(revenue_height)
        print(f"Revenue height set to: {revenue_height}")

    # ----------------------------------------------------
    # マウスイベント
    # ----------------------------------------------------
    def _on_account_clicked(self, section_widget, row, col):
        """
        どのセクション（費用/収益）で
        どの行がダブルクリックされたかを受け取る
        """
        # 勘定科目名は常に column 0
        account_name_item = section_widget.table.item(row, 0)
        if not account_name_item:
            return

        account_name = account_name_item.text().strip()
        t = self.account_dict.get(account_name)

        if not t:
            print(f"T勘定が存在しません: {account_name}")
            return

        # -------------------------
        #   すでに表示中 → 非表示
        # -------------------------
        if t.isVisible():
            t.hide()
            print(f"[BS] {account_name} → 非表示")
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

        print(f"[BS] {account_name} → 表示@local_pos:{local_pos}, global_pos:{global_pos}, logical_global_pos:{logical_global_pos}, parent_pos:{parent_pos}, dpr:{dpr} ")
        
# --------------------------------------------------------
# 動作テスト
# --------------------------------------------------------
if __name__ == "__main__":
    yaml_file = "C:\\work\\lambda-tuber\\bokicast-mcp-server\\bokicast-mcp-server.yaml"
    config = {}
    with open(yaml_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    print(config)

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
            print(f"  -> {account_name}: 残高が0のためスキップ")
            continue

        category = account_to_category.get(account_name)

        if category == '費用' or category == '費用':
            t_account.add_debit("期首残高", initial_balance)
        elif category == '収益' or category == '収益':
            t_account.add_credit("期首残高", initial_balance)
        else:
            print(f"  -> {account_name}: 勘定カテゴリ ({category}) が不明。期首残高は未登録。")



    bs = ProfitAndLossWidget(main_widget, font, account_dict, config)
    
    main_widget.show()

    sys.exit(app.exec())