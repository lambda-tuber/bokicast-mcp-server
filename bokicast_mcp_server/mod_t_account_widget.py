from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint
import sys

# 💡 AccountEntryWidget を別のファイルからインポートします
from mod_account_entry_widget import AccountEntryWidget

# --------------------------------------------------------
# TAccountWidget
# --------------------------------------------------------
class TAccountWidget(QFrame):
    """
    勘定科目（T字勘定）を表すウィジェット。
    高さ400px固定。
    ヘッダー（上）、フッター（下）は固定表示。
    中央の借方・貸方エリアはスクロール可能。
    """
    _drag_start_position: QPoint | None = None # 💡 TAccountWidget用ドラッグ開始位置
    SNAP_DISTANCE = 15 
    
    def __init__(self, parent, account_name: str, font: QFont):
        super().__init__(parent)
        self.font = font
        self.fm = QFontMetrics(self.font)

        # QFrameのプロパティで枠の形状を設定（スタイルシートの補助として）
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setContentsMargins(1, 1, 1, 1)

        # 💡 TAccountWidgetをフローティングウィンドウ化するための設定
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.OpenHandCursor)
        self.setObjectName("TAccountFrame")

        # 💡 高さを400pxに固定
        self.setFixedHeight(150)

        # メインレイアウト（縦方向: ヘッダー -> スクロールエリア -> フッター）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1) # TAccountWidget全体のマージン
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. ヘッダー（勘定名） - 上部固定
        # ----------------------------------------------------
        self.account_name_label = QLabel(account_name)
        self.account_name_label.setFont(self.font)
        self.account_name_label.setAlignment(Qt.AlignCenter)
        self.account_name_label.setFixedHeight(self.fm.height()+10) # 高さ固定
        self.account_name_label.setStyleSheet("font-weight: bold; border: 0px solid black; background-color: #A0E0A0;")
        main_layout.addWidget(self.account_name_label)

        # ----------------------------------------------------
        # 2. スクロールエリア（借方・貸方コンテンツ） - 中央可変
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # 内部ウィジェットのサイズ変更に追従
        # 💡 垂直スクロールバーを右端に常時表示
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # スクロールエリア自体の枠線は消して、デザインをすっきりさせる
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # スクロールエリアの中身となるコンテナウィジェット
        self.scroll_content = QWidget()
        
        # コンテナ内のレイアウト（水平配置）
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        # レイアウト全体のアライメントも念のため上寄せ設定
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # 借方（Debit）ウィジェット
        self.debit_widget = AccountEntryWidget(self, "借方", self.font, "#E0FFFF", False) 
        self.debit_widget.setWindowFlags(Qt.Widget) # フローティング無効化
        
        # 貸方（Credit）ウィジェット
        self.credit_widget = AccountEntryWidget(self, "貸方", self.font, "#FFE0E0", False) 
        self.credit_widget.setWindowFlags(Qt.Widget) # フローティング無効化

        # スタイル調整（ボーダーなど）
        # self.debit_widget.header_label.setStyleSheet(f"background-color: #E0FFFF; border-left: 1px solid black; border-right: 1px solid black;")
        # self.credit_widget.header_label.setStyleSheet(f"background-color: #FFE0E0; border-right: 1px solid black;")
        # self.debit_widget.table.setStyleSheet("border-left: 1px solid black; border-right: 1px solid black; border-bottom: 1px solid black;")
        # self.credit_widget.table.setStyleSheet("border-right: 1px solid black; border-bottom: 1px solid black;")
        
        # レイアウトに追加
        # 💡 【修正ポイント】第2引数(stretch)を0にし、第3引数で Qt.AlignTop を指定して上寄せを強制
        self.scroll_layout.addWidget(self.debit_widget, 0, Qt.AlignTop)
        self.scroll_layout.addWidget(self.credit_widget, 0, Qt.AlignTop)

        # コンテナをスクロールエリアにセット
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # ----------------------------------------------------
        # 3. フッター（貸借差額） - 最下部固定
        # ----------------------------------------------------
        self.balance_label = QLabel("貸借差額: 0 ")
        self.balance_label.setFont(self.font)
        self.balance_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        try:
            height = self.debit_widget._table_header_height
        except AttributeError:
            height = self.fm.height() + 10 
            
        self.balance_label.setFixedHeight(height) 
        self.balance_label.setStyleSheet("border: 0px solid black; background-color: #A0E0A0; padding-right: 5px;")
        main_layout.addWidget(self.balance_label)

        # ----------------------------------------------------
        # 初期調整
        # ----------------------------------------------------
        self.set_column_width_sync()
        self.update_balance_label()
        self.setStyleSheet("#TAccountFrame { border: 1px solid #333366; background-color: white; border-radius:8px; }")

    # ----------------------------------------------------
    # Public: 項目追加
    # ----------------------------------------------------
    def add_debit(self, item_name: str, amount: int):
        """借方（Debit）に項目を追加し、幅同期と残高更新を行います。"""
        self.debit_widget.add_item(item_name, amount)
        self.set_column_width_sync()
        self.update_balance_label()

    def add_credit(self, item_name: str, amount: int):
        """貸方（Credit）に項目を追加し、幅同期と残高更新を行います。"""
        self.credit_widget.add_item(item_name, amount)
        self.set_column_width_sync()
        self.update_balance_label()

    # ----------------------------------------------------
    # Public: 幅同期と残高更新
    # ----------------------------------------------------
    def set_column_width_sync(self):
        """借方と貸方のウィジェット間で、必要な最大列幅を同期させます。"""
        # 借方と貸方の両方で必要な最大幅を計算
        debit_max_width = self.debit_widget.get_max_column_width()
        credit_max_width = self.credit_widget.get_max_column_width()
        
        # 両方で同じ幅を使用するために、より大きな幅を採用
        unified_width = max(debit_max_width, credit_max_width)
        
        # 借方と貸方のウィジェットに統一幅を適用
        self.debit_widget.set_fixed_column_width(unified_width)
        self.credit_widget.set_fixed_column_width(unified_width)

        # 💡 TAccountWidget全体の幅を計算
        # 借方幅 + 貸方幅 + スクロールバーの幅
        scroll_bar_width = self.scroll_area.verticalScrollBar().sizeHint().width()
        total_content_width = self.debit_widget.width() + self.credit_widget.width() + scroll_bar_width
        
        # ヘッダーとフッターもこの幅に合わせる
        self.account_name_label.setFixedWidth(total_content_width)
        self.balance_label.setFixedWidth(total_content_width)
        
        # TAccountWidget全体の幅を固定
        self.setFixedWidth(total_content_width)
        
        # 💡 高さは固定(400)なので adjustSize() は呼ばない


    def get_balance(self):
        debit_total = self.debit_widget.get_total_amount()
        credit_total = self.credit_widget.get_total_amount()
        
        balance = debit_total - credit_total
        return balance

    def update_balance_label(self):
        """借方合計と貸方合計を計算し、差額を表示ラベルに反映します。
           残高に応じてアライメント(左寄せ/中央/右寄せ)を切り替えます。
        """
       
        balance = self.get_balance()
        
        if balance > 0:
            # 借方残高: 左寄せ
            balance_text = f"借方残高: {balance:,.0f} "
            color = "blue"
            alignment = Qt.AlignLeft | Qt.AlignVCenter
            # 💡 左寄せの場合、パディングを調整して借方側に寄せる
            padding_style = "padding-left: 5px; padding-right: 0;" 
        elif balance < 0:
            # 貸方残高: 右寄せ
            balance_text = f"貸方残高: {-balance:,.0f} "
            color = "red"
            alignment = Qt.AlignRight | Qt.AlignVCenter
            # 💡 右寄せの場合、パディングを調整して貸方側に寄せる
            padding_style = "padding-right: 5px; padding-left: 0;"
        else:
            # 貸借差額なし (0): 中央寄せ
            balance_text = "貸借差額: 0 "
            color = "black"
            alignment = Qt.AlignCenter
            padding_style = "padding-right: 0; padding-left: 0;"
            
        self.balance_label.setText(balance_text)
        self.balance_label.setAlignment(alignment) # 💡 ここでアライメントを設定
        
        # 💡 スタイルシートはアライメントとは別に設定し、パディングを動的に調整
        self.balance_label.setStyleSheet(
            f"color: {color}; border: none; border-top: 3px double black; background-color: #A0E0A0; {padding_style}"
        )
        
    # ----------------------------------------------------
    # TAccountWidget用 マウスイベントハンドラ (ドラッグ/スナップ機能)
    # ----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        """マウスの左ボタンが押されたとき、ドラッグ開始位置を記録しカーソルを変更"""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.position().toPoint() 
            self.setCursor(Qt.ClosedHandCursor) 
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウスが移動したとき、ウィンドウを移動させる"""
        if self._drag_start_position is not None:
            new_global_pos = event.globalPosition().toPoint() - self._drag_start_position 
            
            parent_widget = self.parent()
            if parent_widget:
                all_widgets = parent_widget.findChildren(TAccountWidget)
                all_entries = parent_widget.findChildren(AccountEntryWidget)
                all_widgets.extend(all_entries)
                
                snapped_pos = self._check_snap(new_global_pos, all_widgets)
                self.move(snapped_pos)
            else:
                self.move(new_global_pos)
            
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスボタンが離されたとき、ドラッグ状態を解除しカーソルを元に戻す"""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = None
            self.setCursor(Qt.OpenHandCursor) 
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _check_snap(self, current_pos: QPoint, all_widgets: list[QWidget]) -> QPoint:
        """現在の位置を周囲のウィジェットにスナップさせるか判定する (TAccountWidget用)"""
        
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
            
            # TAccountWidgetの子ウィジェットの場合は無視
            if other.parent() is self:
                continue
            
            other_rect = other.geometry()
            other_left = other_rect.x()
            other_right = other_rect.x() + other_rect.width()
            other_top = other_rect.y()
            other_bottom = other_rect.y() + other_rect.height()
            other_center_x = other_left + other_rect.width() / 2

            # --- 水平方向のスナップ判定 ---
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

            # --- 垂直方向のスナップ判定 ---
            if abs(current_top - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom
            elif abs(current_bottom - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top - current_rect.height()
            elif abs(current_top - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top
            elif abs(current_bottom - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom - current_rect.height()
                
        return QPoint(snapped_x, snapped_y)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()         # 非表示にする
            event.accept()
            return

        super().keyPressEvent(event)

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

    main_widget.show()

    sys.exit(app.exec())