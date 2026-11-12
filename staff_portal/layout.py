
from nicegui import ui

from staff_portal.config import (
    APP_NAME,
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


# -------------------- SHARED WEBSITE LAYOUT --------------------

def page_layout(page_title, active_path):

    # -------------------- WEBSITE THEME --------------------

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


    # -------------------- NAVIGATION SIDEBAR --------------------

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

            if is_active:
                background = PRIMARY
            else:
                background = 'transparent'

            ui.button(
                name,
                icon=icon,
                on_click=lambda destination=path: ui.navigate.to(destination)
            ).props(
                'flat no-caps align=left text-color=white'
            ).classes(
                'w-full mb-1'
            ).style(
                f'background-color: {background};'
                'color: white !important;'
            )

    # -------------------- TOP HEADER --------------------

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

            ui.icon('local_shipping').classes(
                'text-3xl'
            ).style(f'color: {PRIMARY};')

            with ui.column().classes('gap-0'):

                ui.label(APP_NAME).classes(
                    'text-xl font-bold'
                ).style(f'color: {PRIMARY};')

                ui.label('Staff Portal').classes(
                    'text-xs text-slate-500'
                )

        ui.label('Mailroom Operations').classes(
            'text-sm text-slate-500'
        )


    # -------------------- MAIN CONTENT AREA --------------------

    content = ui.column().classes(
        'w-full max-w-7xl mx-auto px-6 py-6 gap-5'
    )

    with content:

        ui.label(page_title).classes(
            'text-3xl font-bold text-slate-900'
        )

    return content
