
class UIStyles:
    # Colors
    ACCENT_GREEN = "#00E676"  # Bright Green like TRAE
    ACCENT_HOVER = "#00C853"
    TEXT_BLACK = "#000000"
    TEXT_WHITE = "#FFFFFF"
    TEXT_GRAY = "#B0B0B0"
    
    BG_DARK = "#111111"
    BG_CARD = "#1E1E1E" # Dark card background
    
    # Fonts
    FONT_FAMILY = "Segoe UI, Microsoft YaHei, sans-serif"
    
    # Button Styles
    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {ACCENT_GREEN};
            color: {TEXT_BLACK};
            border: none;
            border-radius: 6px;
            font-family: "{FONT_FAMILY}";
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {ACCENT_GREEN};
            padding: 11px 19px; /* Slight press effect */
        }}
        QPushButton:disabled {{
            background-color: #333333;
            color: #666666;
        }}
    """
    
    BTN_SECONDARY = f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_WHITE};
            border: 2px solid #444444;
            border-radius: 6px;
            font-family: "{FONT_FAMILY}";
            font-size: 14px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            border-color: {ACCENT_GREEN};
            color: {ACCENT_GREEN};
        }}
    """
    
    BTN_NAV = f"""
        QPushButton {{
            background-color: rgba(20, 20, 20, 0.9);
            color: {TEXT_WHITE};
            border: 1px solid #333;
            border-radius: 4px;
            font-family: "{FONT_FAMILY}";
            font-size: 14px;
            font-weight: bold;
            padding: 12px 30px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_GREEN};
            color: {TEXT_BLACK};
            border-color: {ACCENT_GREEN};
        }}
    """

    # Label Styles
    LBL_TITLE = f"""
        QLabel {{
            color: {TEXT_WHITE};
            font-family: "{FONT_FAMILY}";
            font-size: 32px;
            font-weight: bold;
        }}
    """
    
    LBL_SUBTITLE = f"""
        QLabel {{
            color: {TEXT_GRAY};
            font-family: "{FONT_FAMILY}";
            font-size: 16px;
        }}
    """
    
    LBL_NORMAL = f"""
        QLabel {{
            color: {TEXT_WHITE};
            font-family: "{FONT_FAMILY}";
            font-size: 14px;
        }}
    """

    # Container/Card Styles
    CARD_CONTAINER = f"""
        QWidget#CardContainer {{
            background-color: rgba(18, 18, 18, 0.95); /* Nearly opaque dark background */
            border: 1px solid #333;
            border-radius: 12px;
        }}
    """
    
    GROUP_BOX = f"""
        QGroupBox {{
            color: {TEXT_WHITE};
            font-weight: bold;
            border: 1px solid #444;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 20px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
        }}
    """
