from nicegui import ui

from staff_portal.layout import page_layout

from staff_portal.api_client import (
    APIError,
    get_users,
    get_parcels,
    add_parcel,
    update_parcel,
    remove_parcel,
    get_due_parcels
)

# -------------------- PARCEL MANAGEMENT --------------------

@ui.page('/parcels')
async def parcels_page():

    with page_layout('Parcel Management', '/parcels'):

        ui.label(
            'Register and manage parcel records stored on the backend.'
        ).classes('text-slate-500')


        # -------------------- ADD PARCEL --------------------


        with ui.card().classes('w-full p-5 gap-4'):

            ui.label('Register New Parcel').classes(
                'text-xl font-semibold'
            )

            ui.label(
                'Select the recipient for the incoming parcel.'
            ).classes('text-slate-500')

            # Retrieve registered users from the backend
            try:
                users = await get_users()

            except APIError as error:
                users = []
                ui.label(
                    f'Unable to load recipients: {error}'
                ).classes('text-red-700')

            # Create recipient dropdown options
            recipient_options = {}

            for user in users:

                user_id = user.get('userID', user.get('id'))

                if user_id is None:
                    continue

                recipient_options[int(user_id)] = (
                    f"{user.get('name', 'Unknown')} — "
                    f"{user.get('roomNumber', 'No room')}"
                )

            if recipient_options:

                recipient_input = ui.select(
                    recipient_options,
                    label='Select Recipient'
                ).props('outlined').classes('w-full')

                # -------------------- REGISTER PARCEL --------------------

                async def create_parcel():

                    if recipient_input.value is None:
                        ui.notify(
                            'Select a recipient first.',
                            type='warning'
                        )
                        return

                    try:
                        await add_parcel(
                            recipient_input.value
                        )

                    except APIError as error:
                        ui.notify(str(error), type='negative')
                        return

                    ui.notify(
                        'Parcel registered successfully.',
                        type='positive'
                    )

                    ui.navigate.reload()

                ui.button(
                    'Register Parcel',
                    icon='add_box',
                    on_click=create_parcel
                ).props('no-caps')

            else:

                ui.label(
                    'No recipients are available for selection.'
                ).classes('text-slate-500')

                ui.button(
                    'Open Recipient Directory',
                    icon='people',
                    on_click=lambda: ui.navigate.to('/recipients')
                ).props('no-caps')

        # -------------------- RETRIEVE PARCELS --------------------

        try:
            parcels = await get_parcels()

        except APIError as error:
            parcels = []

            ui.label(
                f'Unable to load parcels: {error}'
            ).classes('text-red-700')


        rows = [
            {
                'row_id': index,
                'id': parcel.get('id'),
                'tracking_id': parcel.get('tracking_id'),
                'userID': parcel.get('userID'),
                'status': parcel.get('status', ''),
                'nDelivery': parcel.get('nDelivery')
            }
            for index, parcel in enumerate(parcels)
        ]


        # -------------------- PARCEL TABLE --------------------

        ui.label('Registered Parcels').classes(
            'text-xl font-semibold mt-4'
        )

        search = ui.input(
            'Search Parcels'
        ).props(
            'outlined clearable'
        ).classes('w-80 max-w-full')

        columns = [
            {
                'name': key,
                'field': key,
                'label': label,
                'sortable': True,
                'align': 'left'
            }
            for key, label in [
                ('id', 'Parcel ID'),
                ('tracking_id', 'Tracking ID'),
                ('userID', 'User ID'),
                ('status', 'Status'),
                ('nDelivery', 'Delivery Count')
            ]
        ]

        table = ui.table(
            columns=columns,
            rows=rows,
            row_key='row_id',
            selection='single',
            pagination=10
        ).classes('w-full').props('flat bordered')

        search.bind_value(table, 'filter')


        # -------------------- SELECT PARCEL --------------------

        def selected_parcel():

            if not table.selected:
                ui.notify(
                    'Select a parcel first.',
                    type='warning'
                )
                return None

            return table.selected[0]


        # -------------------- EDIT PARCEL --------------------

        with ui.dialog() as edit_dialog:

            with ui.card().classes('w-96 max-w-full p-5 gap-3'):

                ui.label('Modify Parcel').classes(
                    'text-lg font-semibold'
                )

                edit_user_id = ui.number(
                    'User ID',
                    precision=0
                ).classes('w-full')

                edit_tracking_id = ui.number(
                    'Tracking ID',
                    precision=0
                ).classes('w-full')

                edit_status = ui.input(
                    'Parcel Status'
                ).classes('w-full')

                edit_count = ui.number(
                    'Delivery Count (nDelivery)',
                    precision=0
                ).classes('w-full')


                async def save_changes():

                    numeric_fields = (
                        edit_user_id,
                        edit_tracking_id,
                        edit_count
                    )

                    if (
                        any(field.value is None for field in numeric_fields)
                        or not (edit_status.value or '').strip()
                    ):
                        ui.notify(
                            'Complete all parcel fields.',
                            type='warning'
                        )
                        return

                    try:
                        await update_parcel(
                            int(edit_user_id.value),
                            edit_status.value.strip(),
                            int(edit_tracking_id.value),
                            int(edit_count.value)
                        )

                    except APIError as error:
                        ui.notify(str(error), type='negative')
                        return

                    edit_dialog.close()

                    ui.notify(
                        'Parcel update request accepted.',
                        type='positive'
                    )

                    ui.navigate.reload()


                with ui.row().classes(
                    'w-full justify-end gap-2'
                ):

                    ui.button(
                        'Cancel',
                        on_click=edit_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Save Changes',
                        icon='save',
                        on_click=save_changes
                    ).props('no-caps')


        def open_edit_dialog():

            parcel = selected_parcel()

            if parcel is None:
                return

            edit_user_id.set_value(parcel.get('userID'))
            edit_tracking_id.set_value(parcel.get('tracking_id'))
            edit_status.set_value(parcel.get('status', ''))
            edit_count.set_value(parcel.get('nDelivery'))

            edit_dialog.open()


        # -------------------- REMOVE PARCEL --------------------

        with ui.dialog() as delete_dialog:

            with ui.card().classes('w-96 max-w-full p-5 gap-3'):

                ui.label('Remove Parcel').classes(
                    'text-lg font-semibold'
                )

                ui.label(
                    'Enter the parcel ID to remove. '
                    'This action cannot be undone.'
                )

                delete_id = ui.number(
                    'Parcel ID',
                    precision=0
                ).classes('w-full')


                async def confirm_removal():

                    if delete_id.value is None:
                        ui.notify(
                            'Enter a parcel ID.',
                            type='warning'
                        )
                        return

                    try:
                        await remove_parcel(int(delete_id.value))

                    except APIError as error:
                        ui.notify(str(error), type='negative')
                        return

                    delete_dialog.close()

                    ui.notify(
                        'Parcel removal request accepted.',
                        type='positive'
                    )

                    ui.navigate.reload()


                with ui.row().classes(
                    'w-full justify-end gap-2'
                ):

                    ui.button(
                        'Cancel',
                        on_click=delete_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Confirm Removal',
                        color='negative',
                        on_click=confirm_removal
                    ).props('no-caps')


        # -------------------- MANAGEMENT BUTTONS --------------------

        with ui.row().classes('gap-3'):

            ui.button(
                'Modify Selected Parcel',
                icon='edit',
                on_click=open_edit_dialog
            ).props('outline no-caps')

            ui.button(
                'Remove Parcel',
                icon='delete',
                color='negative',
                on_click=delete_dialog.open
            ).props('outline no-caps')


        # -------------------- PARCELS DUE --------------------

        ui.label('Parcels Due').classes(
            'text-xl font-semibold mt-4'
        )

        try:
            due_parcels = await get_due_parcels()

            if due_parcels:

                fields = list(due_parcels[0].keys())

                due_columns = [
                    {
                        'name': field,
                        'field': field,
                        'label': field,
                        'align': 'left'
                    }
                    for field in fields
                ]

                due_rows = [
                    {
                        field: (
                            str(parcel.get(field))
                            if isinstance(parcel.get(field), (dict, list))
                            else parcel.get(field)
                        )
                        for field in fields
                    }
                    for parcel in due_parcels
                ]

                ui.table(
                    columns=due_columns,
                    rows=due_rows,
                    pagination=10
                ).classes('w-full').props('flat bordered')

            else:
                ui.label(
                    'No parcels are currently due for delivery.'
                ).classes('text-slate-500')

        except APIError as error:

            ui.label(
                f'Unable to retrieve parcels due: {error}'
            ).classes('text-red-700')
