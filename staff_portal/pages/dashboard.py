import asyncio

from nicegui import ui

from staff_portal.layout import page_layout
from staff_portal.api_client import (
    get_users,
    get_parcels,
    get_due_parcels
)


# Dashboard page
@ui.page('/')
async def dashboard_page():

    with page_layout('Dashboard', '/'):

        ui.label(
            'Overview of mailroom operations and delivery activity.'
        ).classes('text-slate-500')

        labels = [
            'Registered Recipients',
            'Registered Parcels',
            'Parcels Due'
        ]

        values = []
        errors = []

        with ui.row().classes('w-full gap-4 flex-wrap'):
            for label in labels:
                with ui.card().classes(
                    'flex-1 min-w-52 p-5 gap-3 shadow-sm'
                ):
                    ui.label(label).classes('text-sm text-slate-500')

                    value = ui.label('Loading...').classes(
                        'text-3xl font-bold text-blue-600'
                    )

                    values.append(value)

        for label in labels:
            errors.append(
                ui.label('').classes('text-sm text-red-700')
            )

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

    # Load backend data after the page connects
    await ui.context.client.connected()

    results = await asyncio.gather(
        get_users(),
        get_parcels(),
        get_due_parcels(),
        return_exceptions=True
    )

    for i, result in enumerate(results):

        if isinstance(result, Exception):
            values[i].set_text('Unavailable')
            errors[i].set_text(f'{labels[i]}: {result}')

        elif isinstance(result, list):
            values[i].set_text(str(len(result)))

        else:
            values[i].set_text('Unavailable')
