"""
SmartBell Manager — UI Styles and Colors
"""

COLORS = {
    "bg_dark":       "#0f0f1e",
    "bg_card":       "#16213e",
    "bg_input":      "#1a1a3e",
    "border":        "#2a2a5e",
    "accent":        "#ffd700",
    "accent_hover":  "#e6c200",
    "text_white":    "#ffffff",
    "text_gray":     "#888888",
    "text_light":    "#cccccc",
    "green":         "#4caf50",
    "green_dark":    "#388e3c",
    "red":           "#f44336",
    "red_dark":      "#d32f2f",
    "blue":          "#2196F3",
    "blue_dark":     "#1565C0",
    "orange":        "#ff9800",
    "purple":        "#9c27b0",
    "select_bg":     "#3d3500",
    "select_text":   "#ffd700",
}

APP_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text_white']};
}}

QGroupBox {{
    color: {COLORS['accent']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px 10px 10px 10px;
    font-weight: bold;
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
}}

QPushButton {{
    background-color: {COLORS['blue']};
    color: white;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    border: none;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['blue_dark']};
}}

QPushButton:pressed {{
    background-color: #0d47a1;
}}

QPushButton:disabled {{
    background-color: #333;
    color: #666;
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['red']};
}}

QPushButton[class="danger"]:hover {{
    background-color: {COLORS['red_dark']};
}}

QPushButton[class="success"] {{
    background-color: {COLORS['green']};
}}

QPushButton[class="success"]:hover {{
    background-color: {COLORS['green_dark']};
}}

QPushButton[class="accent"] {{
    background-color: {COLORS['accent']};
    color: #000;
}}

QPushButton[class="accent"]:hover {{
    background-color: {COLORS['accent_hover']};
}}

QLineEdit {{
    padding: 8px 12px;
    font-size: 13px;
    background: {COLORS['bg_input']};
    color: {COLORS['text_white']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}

QLineEdit[readOnly="true"] {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text_gray']};
}}

QTableWidget {{
    background-color: {COLORS['bg_dark']};
    alternate-background-color: {COLORS['bg_card']};
    color: {COLORS['text_white']};
    font-size: 13px;
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    selection-background-color: {COLORS['select_bg']};
    selection-color: {COLORS['select_text']};
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['select_bg']};
    color: {COLORS['select_text']};
    border: 1px solid {COLORS['accent']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['accent']};
    padding: 8px;
    border: 1px solid {COLORS['border']};
    font-weight: bold;
    font-size: 12px;
}}

QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QLabel {{
    color: {COLORS['text_light']};
    font-size: 13px;
}}

QLabel[class="status"] {{
    color: {COLORS['text_gray']};
    font-size: 12px;
    padding: 4px;
}}

QLabel[class="title"] {{
    color: {COLORS['accent']};
    font-size: 18px;
    font-weight: bold;
}}

QProgressBar {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: white;
    font-size: 11px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 3px;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {COLORS['border']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 3px;
}}
"""