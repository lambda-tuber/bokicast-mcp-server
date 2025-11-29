from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint
import sys

# 💡 AccountEntryWidget をインポート
from mod_account_entry_widget import AccountEntryWidget
from mod_t_account_widget import TAccountWidget

# --------------------------------------------------------
# JournalEntryWidget
# --------------------------------------------------------
class JournalEntryWidget(QFrame):
    """
    仕訳入力用ウィジェット。全体高さ200px固定。
    - ヘッダー: 仕訳ID
    - 中央: 借方・貸方エントリー（3行程度表示、スクロール可）
    - 下部: 合計確認
    - フッター: 備考欄（ラベルなし、3行固定、縦スクロール常時）
    """
    _drag_start_position: QPoint | None = None
    SNAP_DISTANCE = 15 
    
    def __init__(self, parent, journal_id: str, font: QFont, account_dict: dict[str, TAccountWidget]):
        super().__init__(parent)
        self.font = font
        self.fm = QFontMetrics(self.font)
        self.account_dict = account_dict
        self.journal_id = journal_id
        self.balance_status = "✔ 正常"

        # QFrame設定
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setContentsMargins(1, 1, 1, 1)

        # フローティングウィンドウ設定
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.OpenHandCursor)
        
        self.setObjectName("JournalEntryFrame")

        # 💡 全体の高さを200pxに固定
        self.setFixedHeight(170)

        # --- メインレイアウト ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. ヘッダー（仕訳ID）
        # ----------------------------------------------------
        self.header_label = QLabel(f"仕訳ID: {journal_id}")
        self.header_label.setFont(self.font)
        self.header_label.setAlignment(Qt.AlignCenter)
        # 高さを少し詰める
        self.header_label.setFixedHeight(self.fm.height() + 10)
        self.header_label.setStyleSheet("font-weight: 0px solid black; background-color: #CCCCFF;")
        main_layout.addWidget(self.header_label, alignment=Qt.AlignHCenter)
        #main_layout.addWidget(self.header_label)

        # ----------------------------------------------------
        # 2. スクロールエリア（借方・貸方コンテンツ）
        #    レイアウトの伸縮(stretch)を利用して、残りのスペースを割り当てる
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # 借方・貸方ウィジェット
        self.debit_widget = AccountEntryWidget(self, "借方", self.font, "#E0FFFF", enable_drag=False) 
        self.credit_widget = AccountEntryWidget(self, "貸方", self.font, "#FFE0E0", enable_drag=False) 

        # 配置
        self.scroll_layout.addWidget(self.debit_widget, 0, Qt.AlignTop)
        self.scroll_layout.addWidget(self.credit_widget, 0, Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        # stretch=1 を設定して、余った縦幅をこのエリアに割り当てる
        main_layout.addWidget(self.scroll_area)

        # ----------------------------------------------------
        # 3. 合計表示・エラー確認エリア
        # ----------------------------------------------------
        self.totals_container = QFrame()
        self.totals_container.setStyleSheet("background-color:  #CCCCFF; border-top: 0px solid #999;")
        self.totals_container.setContentsMargins(4, 0, 4, 0)
        totals_layout = QHBoxLayout(self.totals_container)
        # 上下のマージンを詰める
        totals_layout.setContentsMargins(0, 0, 0, 0)
        totals_layout.setSpacing(0)
        try:
            height = self.debit_widget._table_header_height
        except AttributeError:
            height = self.fm.height() + 10 
            
        self.total_debit_label = QLabel("借方計: 0")
        self.total_debit_label.setFont(self.font)
        self.total_debit_label.setStyleSheet("color: blue; font-weight: bold;")
        self.total_debit_label.setFixedHeight(height) 

        self.status_label = QLabel("")
        self.status_label.setFont(self.font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(height) 

        self.total_credit_label = QLabel("貸方計: 0")
        self.total_credit_label.setFont(self.font)
        self.total_credit_label.setStyleSheet("color: red; font-weight: bold;")
        self.total_credit_label.setFixedHeight(height) 

        totals_layout.addWidget(self.total_debit_label)
        totals_layout.addStretch()
        totals_layout.addWidget(self.status_label)
        totals_layout.addStretch()
        totals_layout.addWidget(self.total_credit_label)
        
#        main_layout.addWidget(totals_container, alignment=Qt.AlignHCenter)
        main_layout.addWidget(self.totals_container)

        # ----------------------------------------------------
        # 4. 備考欄 (Footer) - 3行固定、ラベルなし
        # ----------------------------------------------------
        self.remarks_input = QTextEdit()
        self.remarks_input.setFont(self.font)
        self.remarks_input.setPlaceholderText("備考を入力...")
        
        # 💡 縦スクロールバーを常時表示
        self.remarks_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # 💡 高さ計算: (フォントの高さ * 3行) + 上下パディング
        line_height = self.fm.lineSpacing()
        # テキストエリアのフレーム幅やマージンを考慮して少し余裕を持たせる (+10)
        remarks_height = (line_height * 2) + 10
        self.remarks_input.setFixedHeight(remarks_height)
        
        self.remarks_input.setStyleSheet("border: 0px solid #CCC; border-top: none; background-color: white;")
        
        main_layout.addWidget(self.remarks_input, alignment=Qt.AlignHCenter)

        # ----------------------------------------------------
        # 初期調整
        # ----------------------------------------------------
        self.set_column_width_sync()
        self.update_totals()
        self.setStyleSheet("#JournalEntryFrame { border: 1px solid #333366; background-color: white; border-radius: 8px; }")

    # ----------------------------------------------------
    # Public: データ操作
    # ----------------------------------------------------

    def add_journal(self, journal_data: dict):
        """
        JSONデータ形式で借方・貸方・備考を一括追加
        journal_data = {
            "debit": [{"account": "仕入", "amount": 1000}, ...],
            "credit": [{"account": "買掛金", "amount": 3000}, ...],
            "remarks": "備考文字列"
        }
        """
        for debit_item in journal_data.get("debit", []):
            account_name = debit_item.get("account", "")
            amount = debit_item.get("amount", 0)
            self.debit_widget.add_item(account_name, amount)

        for credit_item in journal_data.get("credit", []):
            account_name = credit_item.get("account", "")
            amount = credit_item.get("amount", 0)
            self.credit_widget.add_item(account_name, amount)

        # 備考追加
        remarks_text = journal_data.get("remarks", "")
        if remarks_text:
            self.remarks_input.setText(remarks_text)

        # 幅や合計の更新
        self.set_column_width_sync()
        self.update_totals()
        self.commit()

    def add_debit(self, account_name: str, amount: int):
        """借方に追加"""
        self.debit_widget.add_item(account_name, amount)
        self.set_column_width_sync()
        self.update_totals()

    def add_credit(self, account_name: str, amount: int):
        """貸方に追加"""
        self.credit_widget.add_item(account_name, amount)
        self.set_column_width_sync()
        self.update_totals()

    def commit(self):
        if self.balance_status != "✔ 正常":
            print(f"Journal {self.journal_id} 不一致のため commit 中止")
            return

        # debit/credit をテーブルから取得
        debit_items = self.debit_widget.get_all_items()
        credit_items = self.credit_widget.get_all_items()

        cur_x = self.x()
        cur_y = self.y()
        inc = 30

        # 借方
        for account_name, amount in debit_items:
            cur_x += inc
            cur_y += inc
            t_widget = self.account_dict.get(account_name)
            if t_widget is None:
                # 新規作成
                t_widget = TAccountWidget(self.parent(), account_name, self.font)
                t_widget.move(cur_x, cur_y)
                t_widget.show()
                self.account_dict[account_name] = t_widget

            # 相手勘定が1つの場合は勘定名を付加
            if len(credit_items) == 1:
                credit_name = credit_items[0][0]
                t_widget.add_debit(f"{self.journal_id}-{credit_name}", amount)
            else:
                t_widget.add_debit(self.journal_id, amount)

        # 貸方
        for account_name, amount in credit_items:
            cur_x += inc
            cur_y += inc
            t_widget = self.account_dict.get(account_name)
            if t_widget is None:
                t_widget = TAccountWidget(self.parent(), account_name, self.font)
                t_widget.move(cur_x, cur_y)
                t_widget.show()
                self.account_dict[account_name] = t_widget

            if len(debit_items) == 1:
                debit_name = debit_items[0][0]
                t_widget.add_credit(f"{self.journal_id}-{debit_name}", amount)
            else:
                t_widget.add_credit(self.journal_id, amount)

        print(f"Journal {self.journal_id} を commit 完了")

    # ----------------------------------------------------
    # 内部処理: 幅同期
    # ----------------------------------------------------
    def set_column_width_sync(self):
        debit_max = self.debit_widget.get_max_column_width()
        credit_max = self.credit_widget.get_max_column_width()
        unified_width = max(debit_max, credit_max)
        
        self.debit_widget.set_fixed_column_width(unified_width)
        self.credit_widget.set_fixed_column_width(unified_width)

        scroll_bar_width = self.scroll_area.verticalScrollBar().sizeHint().width()
        total_content_width = self.debit_widget.width() + self.credit_widget.width() + scroll_bar_width
        
        self.header_label.setFixedWidth(total_content_width)
        self.totals_container.setFixedWidth(total_content_width)
        self.remarks_input.setFixedWidth(total_content_width)
        self.setFixedWidth(total_content_width) 

    # ----------------------------------------------------
    # 内部処理: 合計更新・エラーチェック
    # ----------------------------------------------------
    def update_totals(self):
        debit_total = self.debit_widget.get_total_amount()
        credit_total = self.credit_widget.get_total_amount()
        
        self.total_debit_label.setText(f"借方計: {debit_total:,}")
        self.total_credit_label.setText(f"貸方計: {credit_total:,}")
        
        if debit_total != credit_total:
            self.balance_status = "⚠️ 不一致"
            self.status_label.setText(self.balance_status)
            self.status_label.setStyleSheet("color: red; font-weight: bold; background-color: #FFEEEE; padding: 0px 4px; border-radius: 3px;")
        else:
            self.balance_status = "✔ 正常"
            self.status_label.setText(self.balance_status)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

    # ----------------------------------------------------
    # マウスイベント (ドラッグ移動用)
    # ----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        # 備考欄での操作を妨げない
        child = self.childAt(event.position().toPoint())
        if child:
            # 備考欄またはその子要素（viewportなど）かチェック
            widget = child
            while widget is not None and widget != self:
                if widget == self.remarks_input:
                    super().mousePressEvent(event)
                    return
                widget = widget.parent()

        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.position().toPoint() 
            self.setCursor(Qt.ClosedHandCursor) 
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_position is not None:
            new_global_pos = event.globalPosition().toPoint() - self._drag_start_position 
            
            parent_widget = self.parent()
            if parent_widget:
                all_widgets = parent_widget.findChildren(JournalEntryWidget)
                snapped_pos = self._check_snap(new_global_pos, all_widgets)
                self.move(snapped_pos)
            else:
                self.move(new_global_pos)
            
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start_position = None
            self.setCursor(Qt.OpenHandCursor) 
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _check_snap(self, current_pos: QPoint, all_widgets: list[QWidget]) -> QPoint:
        current_rect = self.geometry()
        snapped_x = current_pos.x()
        snapped_y = current_pos.y()

        current_left = current_pos.x()
        current_right = current_pos.x() + current_rect.width()
        current_top = current_pos.y()
        current_bottom = current_pos.y() + current_rect.height()
        current_center_x = current_left + current_rect.width() / 2
        
        for other in all_widgets:
            if other is self or other.isHidden() or not isinstance(other, QWidget):
                continue
            
            other_rect = other.geometry()
            other_left = other_rect.x()
            other_right = other_rect.x() + other_rect.width()
            other_top = other_rect.y()
            other_bottom = other_rect.y() + other_rect.height()
            other_center_x = other_left + other_rect.width() / 2

            if abs(current_left - other_right) <= self.SNAP_DISTANCE:
                snapped_x = other_right
            elif abs(current_right - other_left) <= self.SNAP_DISTANCE:
                snapped_x = other_left - current_rect.width()
            elif abs(current_left - other_left) <= self.SNAP_DISTANCE:
                snapped_x = other_left
            elif abs(current_right - other_right) <= self.SNAP_DISTANCE:
                snapped_x = other_right - current_rect.width()
            elif abs(current_center_x - other_center_x) <= self.SNAP_DISTANCE:
                snapped_x = int(other_center_x - current_rect.width() / 2)

            if abs(current_top - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom
            elif abs(current_bottom - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top - current_rect.height()
            elif abs(current_top - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top
            elif abs(current_bottom - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom - current_rect.height()
                
        return QPoint(snapped_x, snapped_y)


# --------------------------------------------------------
# 動作テスト
# --------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    main_widget = QWidget()
    main_widget.setWindowTitle("Main Container (Floater Test)")
    main_widget.setGeometry(0, 0, 1200, 800)
    main_widget.setStyleSheet("background-color: #F0F0F0;")
    

    font = QFont("MS Gothic", 10)
    
    
    # =======================================================
    # AccountEntryWidget 単体のテスト (フローティング)
    # =======================================================
    # 💡 AccountEntryWidgetをmain_widgetの子としてインスタンス化
    w1 = AccountEntryWidget(main_widget, "資産項目 (現金)", font, "#e0e0ff")
    w2 = AccountEntryWidget(main_widget, "負債項目 (買掛金)", font, "#e0e0ee")
    w3 = AccountEntryWidget(main_widget, "純資産項目 (資本金)", font, "#e0e0dd")

    # テストデータ
    w1.add_item("現金", 120000)
    w1.add_item("売掛金", 35000000000)
    w1.add_item("普通預金", 445500)
    w1.add_item("事務用品費", 2300)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("事務用品費", 2300)
    
    w2.add_item("買掛金", 150000)
    w2.add_item("短期借入金", 5000000)
    
    w3.add_item("資本金", 150000)

    # 初期位置設定
    w1.move(50, 50)
    w2.move(w1.width() + 100, 50)
    w3.move(w1.width() + 100 + w2.width() + 100, 50)

    col_width = w1.get_max_column_width()
    w2.set_fixed_column_width(col_width)
    w3.set_fixed_column_width(col_width)

    w1.show()
    w2.show()
    w3.show()

    print("--- AccountEntryWidget Test ---")
    print(f"w1 (資産) 合計: {w1.get_total_amount():,.0f}")
    print(f"w2 (負債) 合計: {w2.get_total_amount():,.0f}")
    print(f"w3 (純資産) 合計: {w3.get_total_amount():,.0f}")
    print("-------------------------------")
    
    # ---------------------------------------------------
    # TAccountWidget のテスト
    # ---------------------------------------------------
    
    # 1. 現金勘定（データ多め、スクロール確認用）
    t_cash = TAccountWidget(main_widget, "現金勘定 (スクロールテスト)", font)
    
    # 借方: たくさんのデータを追加してスクロールを確認
    for i in range(20):
        t_cash.add_debit(f"売上入金_{i+1}", 10000)
    
    # 貸方: 少しだけ
    t_cash.add_credit("仕入代金", 150000)
    t_cash.add_credit("光熱費支払", 25000)
    
    # 2. 買掛金勘定（データ少なめ、上寄せ確認用）
    t_payable = TAccountWidget(main_widget, "買掛金勘定 (上寄せテスト)", font)
    t_payable.add_debit("支払", 100000)
    t_payable.add_credit("期首残高", 200000)
    t_payable.add_credit("仕入発生", 500000)
    
    # 初期位置設定
    t_cash.move(50, 50)
    t_payable.move(t_cash.width() + 100, 50)
    
    t_cash.show()
    t_payable.show()

    #---------------------------------------------------

    account_dict: dict[str, TAccountWidget] = {}

    # 1. 正常な仕訳
    j1 = JournalEntryWidget(main_widget, "J-001", font, account_dict)
    j1.add_debit("現金", 100000)
    j1.add_credit("売上", 100000)
    j1.remarks_input.setText("商品Aの売上\n3行表示のテスト\nスクロール確認用")
    
    # 2. エラー（不一致）
    j2 = JournalEntryWidget(main_widget, "J-002", font, account_dict)
    j2.add_debit("旅費交通費", 12500)
    j2.add_credit("現金", 10000) 
    j2.remarks_input.setText("金額不一致のテスト")
    
    # 3. 複数行（スクロール確認）
    j3 = JournalEntryWidget(main_widget, "J-003", font, account_dict)
    j3.add_debit("仕入", 50000)
    j3.add_debit("租税公課", 5000) 
    j3.add_debit("発送費", 1500)
    j3.add_debit("雑費", 500)
    j3.add_credit("買掛金", 57000)
    j3.remarks_input.setText("材料仕入\n複数科目のテスト\n狭いエリアでの表示確認")

    j4 = JournalEntryWidget(main_widget, "J-004", font, account_dict)
    journal_data = {
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
    j4.add_journal(journal_data)

    # 配置
    j1.move(50, 50)
    j2.move(j1.width() + 100, 50)
    j3.move(50, j1.height() + 200)
    j3.move(50, j1.height() + 300)
    
    j1.show()
    j2.show()
    j3.show()
    j4.show()

    j1.commit()
    j2.commit()
    j3.commit()
    j4.commit()

    main_widget.show()

    sys.exit(app.exec())