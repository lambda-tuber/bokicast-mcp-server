from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint
import sys
import json
from typing import Any, List, Dict

# 💡 AccountEntryWidget を別のファイルからインポートします
from bokicast_mcp_server.mod_account_entry_widget import AccountEntryWidget
#from bokicast_mcp_server.mod_journal_entry_widget import JournalEntryWidget

import logging
logger = logging.getLogger(__name__)

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
    
    def __init__(self, parent, account_name: str, font: QFont, journal_dict, category):
        super().__init__(parent)
        self.font = font
        self.fm = QFontMetrics(self.font)
        self.journal_dict = journal_dict
        self.category = category
        
        # QFrameのプロパティで枠の形状を設定（スタイルシートの補助として）
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setContentsMargins(4, 4, 4, 4)

        # 💡 TAccountWidgetをフローティングウィンドウ化するための設定
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
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
        self.debit_widget = AccountEntryWidget(self.scroll_content, "借方", self.font, "#E0FFFF", False) 
        
        # 貸方（Credit）ウィジェット
        self.credit_widget = AccountEntryWidget(self.scroll_content, "貸方", self.font, "#FFE0E0", False) 

        self.debit_widget.table.cellDoubleClicked.connect(
            lambda row, col: self._on_entry_double_clicked(self.debit_widget, row, col)
        )
        self.credit_widget.table.cellDoubleClicked.connect(
            lambda row, col: self._on_entry_double_clicked(self.credit_widget, row, col)
        )

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
            
        self.account_name_label.setFixedHeight(height) 
        
        self.balance_label.setFixedHeight(height) 
        self.balance_label.setStyleSheet("border: 0px solid black; background-color: #A0E0A0; padding-right: 5px;")
        main_layout.addWidget(self.balance_label)

        # ----------------------------------------------------
        # 初期調整
        # ----------------------------------------------------
        self.set_column_width_sync()
        self.update_balance_label()
        self.setStyleSheet("#TAccountFrame { border: 0px solid #333366; background-color: #A0E0A0; border-radius:0px; }")

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
        
        self.account_name_label.setFixedWidth(total_content_width)
        self.scroll_area.setFixedWidth(total_content_width)
        self.balance_label.setFixedWidth(total_content_width)
        
        # TAccountWidget全体の幅を固定
        self.setFixedWidth(total_content_width + 8)
        
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

    def get_account_data(self):
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
        # データの収集
        # ここで debit_widget.get_all_items() が呼び出されることを前提とします
        debit_items_raw = self.debit_widget.get_all_items()
        credit_items_raw = self.credit_widget.get_all_items()
        
        debit_data = self._format_items_to_json(debit_items_raw)
        credit_data = self._format_items_to_json(credit_items_raw)
        
        # 残高の取得
        balance = self.get_balance()

        result = {
            "勘定": self.account_name_label.text(),
            "借方": debit_data,
            "貸方": credit_data,
            "残高": balance
        }

        return json.dumps(result, ensure_ascii=False, indent=4)

    def _format_items_to_json(self, items: list[tuple[str, int]]) -> List[Dict[str, Any]]:
        formatted_list = []
        for label, amount in items:
            formatted_list.append({
                "ラベル": label,
                "金額": amount
            })
        return formatted_list

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

    def enterEvent(self, event):
        self.setStyleSheet("""
            #TAccountFrame {
                background-color: #FFFACD;
                border: 0px solid #333366;
                border-radius: 0px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            #TAccountFrame {
                background-color: #A0E0A0;
                border: 0px solid #333366;
                border-radius: 0px;
            }
        """)
        super().leaveEvent(event)


    # ======================================================================
    #   🔥 ダブルクリック処理（仕訳検索 + T版表示/非表示 + 位置移動）
    # ======================================================================
    def _on_entry_double_clicked(self, entry_widget, row: int, col: int):
        """
        ダブルクリックで処理する内容:

        1.セルの文字を取得 → "J001-売上" 形式なら仕訳ID抽出
        2.仕訳IDが journal_dict に存在すれば対応データ表示
        3.T字勘定ウィジェットの表示 / 非表示切り替え
        4.表示する場合はクリックしたセル位置に移動（DPI対応）
        """

        # -------------------------
        #   仕訳ID取得処理
        # -------------------------
        account_name_item = entry_widget.table.item(row, 0)
        if not account_name_item:
            return

        label = account_name_item.text().strip()

        if not label:
            return

        journal_id = label.split("-")[0].strip()
        journal_obj = None
        if journal_id in self.journal_dict:
            journal_obj = self.journal_dict[journal_id]
            logger.debug(f"[DEBUG] 仕訳ID '{journal_id}' → 仕訳データ:")
            logger.debug(journal_obj)

            # TODO: journal_obj を JournalEntryWidget に渡して表示する処理に拡張する
        else:
            logger.warning(f"[WARNING] {label} '{journal_id}' は journal_dict に存在しません。")
            return

        # ---------------------------------------------------------
        #   ここから UI 表示処理
        # ---------------------------------------------------------

        # === すでに表示中なら非表示 ===
        if journal_obj.isVisible():
            journal_obj.hide()
            logger.debug(f"[BS] {journal_id} → 非表示")
            return

        # === 表示するので位置合わせ ===
        table = entry_widget.table
        item = table.item(row, col)
        if not item:
            logger.warning("空セル → 位置移動スキップ")
            return

        cell_rect = table.visualItemRect(item)
        local_pos = cell_rect.bottomLeft()

        # テーブル座標 → グローバル（物理）
        global_pos = table.mapToGlobal(local_pos)

        # DPI補正
        dpr = self.window().devicePixelRatio()
        logical_pos = QPoint(
            int(global_pos.x() / dpr),
            int(global_pos.y() / dpr)
        )

        # 最終配置
        journal_obj.move(logical_pos)
        journal_obj.show()
        journal_obj.raise_()


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

    logger.debug("--- AccountEntryWidget Test ---")
    logger.debug(f"w1 (資産) 合計: {w1.get_total_amount():,.0f}")
    logger.debug(f"w2 (負債) 合計: {w2.get_total_amount():,.0f}")
    logger.debug(f"w3 (純資産) 合計: {w3.get_total_amount():,.0f}")
    logger.debug("-------------------------------")
    
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