from pathlib import Path
from nicegui import app, ui

from staff_portal.config import (
    NAV_ITEMS,
    PRIMARY,
    SECONDARY,
    ACCENT,
    BACKGROUND,
    SIDEBAR,
    WHITE,
    SUCCESS,
    ERROR,
    WARNING
)


# Website logo
PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_DIR / 'assets'
LOGO = ASSETS / 'logo.jpeg'

if ASSETS.is_dir():
    app.add_static_files('/assets', str(ASSETS))


# Website layout
def page_layout(page_title, active_path):

    # Website colours
    ui.colors(
        primary=PRIMARY,
        secondary=SECONDARY,
        accent=ACCENT,
        positive=SUCCESS,
        negative=ERROR,
        warning=WARNING
    )

    ui.add_head_html(f'''
        <style>
            body {{
                background-color: {BACKGROUND};
                font-family: Arial, sans-serif;
            }}
        </style>
    ''')

    # Navigation sidebar
    with ui.left_drawer(
        value=True,
        top_corner=False
    ).props('width=260').classes('p-3').style(
        f'background-color: {SIDEBAR};'
    ) as drawer:

        ui.label('NAVIGATION').classes(
            'text-xs font-semibold text-slate-400 px-3 py-4'
        )

        for name, icon, path in NAV_ITEMS:
            is_active = path == active_path
            background = PRIMARY if is_active else 'transparent'

            ui.button(
                name,
                icon=icon,
                on_click=lambda destination=path: ui.navigate.to(destination)
            ).props(
                'flat no-caps align=left text-color=white'
            ).classes('w-full mb-1').style(
                f'background-color: {background}; color: white !important;'
            )

    # Top header
    with ui.header().classes(
        'items-center justify-between px-5 py-3'
    ).style(
        f'background-color: {WHITE}; color: #0F172A;'
    ):

        with ui.row().classes('items-center gap-3'):

            ui.button(
                icon='menu',
                on_click=lambda: drawer.toggle()
            ).props('flat round dense')

            if LOGO.is_file():
                ui.image('/assets/logo.jpeg').classes(
                    'h-16 w-auto'
                ).props('fit=contain')
            else:
                ui.label('BluSend').classes(
                    'text-xl font-bold text-blue-600'
                )

        ui.label('Mailroom Operations').classes(
            'text-sm text-slate-500'
        )

    # Main content
    content = ui.column().classes(
        'w-full max-w-7xl mx-auto px-6 py-6 gap-5'
    )

    with content:
        ui.label(page_title).classes(
            'text-3xl font-bold text-slate-900'
        )

    return content
