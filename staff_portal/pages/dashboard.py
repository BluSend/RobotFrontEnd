import asyncio

from nicegui import ui

from staff_portal.layout import page_layout

from staff_portal.api_client import(
    get_users,
    get_parcels,
    get_due_parcels
)

# Dashboard Page
@ui.page('/')
async def dashboard_page():

    with page_layout('Dashboard', '/'):

        ui.label(
            'Overview of mailroom operations and delivery activity.'
        ).classes('text-slate-500')

        # Backend Data

        results = await asyncio.gather(
            get_users(),
            get_parcels(),
            get_due_parcels(),
            return_exceptions=True
        )

        labels = [
            'Registered Recipients',
            'Registered Parcels',
            'Parcels Due'
        ]

        # Statistics
        with ui.row().classes('w-full gap-4 flex-wrap'):
            for label, result in zip(labels, results):

                with ui.card().classes(
                    'flex-1 min-w-52 p-5 gap-3 shadow-sm'
                ):
                    ui.label(label).classes(
                        'text-sm text-slate-500'
                    )

                    if isinstance(result, list):
                        value = str(len(result))
                    else:
                        value = 'Unavailable'

                    ui.label(value).classes(
                        'text-3xl font-bold text-blue-600'
                    )

            # Connection Errors
            for label, result in zip(labels, results):

                if isinstance(result, Exception):

                    ui.label(
                        f'{label}:{result}'
                    ).classes('text-sm text-red-700')

            # Quick Actions
            ui.label('Quick Actions').classes(
                'text-xl font-semibold text-slate-800 mt-4'
            )

            with ui.row().classes('gap-3 flex-wrap'):

                ui.button(
                    'Manage Recipients',
                    icon='people',
                    on_click=lambda: ui.navigate.to('/recipients')
                ).props('no-caps')

                ui.button(
                    'Manage Parcels',
                    icon='inventory_2',
                    on_click=lambda: ui.navigate.to('/parcels')
                ).props('no-caps')
