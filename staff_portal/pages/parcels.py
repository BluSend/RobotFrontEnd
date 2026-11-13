from nicegui import ui

from staff_portal.api_client import (
    APIError,
    get_users,
    get_parcels,
    add_parcel,
    update_parcel,
    remove_parcel,
    get_due_parcels,
    generate_delivery_otp
)

from staff_portal.layout import page_layout


# OTP response
def otp_rejected(result):
    if result is False:
        return True

    if isinstance(result, str):
        return any(
            word in result.lower()
            for word in ('failed', 'failure', 'error', 'invalid', 'not found')
        )

    if isinstance(result, dict):
        if result.get('success') is False or result.get('sent') is False:
            return True

        return any(
            word in str(result.get(field, '')).lower()
            for field in ('status', 'message', 'detail')
            for word in ('failed', 'failure', 'error', 'invalid', 'not found')
        )

    return False


# Parcel management
@ui.page('/parcels')
async def parcels_page():

    with page_layout('Parcel Management', '/parcels'):

        ui.label(
            'Add, update and manage parcels.'
        ).classes('text-slate-500')

        # Add parcel
        with ui.card().classes('w-full p-5 gap-3'):

            ui.label('Add Parcel').classes(
                'text-xl font-semibold'
            )

            try:
                users = await get_users()
            except APIError as error:
                users = []
                ui.notify(
                    f'Unable to load recipients: {error}',
                    type='negative'
                )

            recipients = {}

            for user in users:
                user_id = user.get('userID', user.get('id'))

                if user_id is not None:
                    recipients[int(user_id)] = (
                        f"{user.get('name', 'Unknown')} "
                        f"({user.get('email', '')})"
                    )

            selected_recipient = ui.select(
                options=recipients,
                label='Select Recipient'
            ).props('outlined').classes('w-full')

            async def create_parcel():

                if selected_recipient.value is None:
                    ui.notify(
                        'Please select a recipient.',
                        type='warning'
                    )
                    return

                try:
                    await add_parcel(
                        int(selected_recipient.value)
                    )

                except APIError as error:
                    ui.notify(str(error), type='negative')
                    return

                ui.notify(
                    'Parcel added successfully.',
                    type='positive'
                )

                ui.navigate.reload()

            ui.button(
                'Add Parcel',
                icon='add_box',
                on_click=create_parcel
            ).props('no-caps')

        # Load parcels
        try:
            raw_parcels = await get_parcels()

        except APIError as error:
            raw_parcels = []
            ui.label(
                f'Unable to load parcels: {error}'
            ).classes('text-red-700')

        rows = [
            {
                'row_id': idx,
                'id': parcel.get('id'),
                'tracking_id': parcel.get('tracking_id'),
                'userID': parcel.get('userID'),
                'status': parcel.get('status', ''),
                'nDelivery': parcel.get('nDelivery')
            }
            for idx, parcel in enumerate(raw_parcels)
        ]

        # Parcel table
        ui.label('Registered Parcels').classes(
            'text-xl font-semibold mt-4'
        )

        search = ui.input(
            'Search Parcels'
        ).props('outlined clearable').classes('w-80')

        columns = [
            {
                'name': key,
                'field': key,
                'label': label,
                'sortable': True,
                'align': 'left'
            }
            for key, label in [
                ('id', 'ID'),
                ('tracking_id', 'Tracking ID'),
                ('userID', 'User ID'),
                ('status', 'Status'),
                ('nDelivery', 'Deliveries')
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

        # Select parcel
        def selected_parcel():

            if not table.selected:
                ui.notify(
                    'Select a parcel first.',
                    type='warning'
                )
                return None

            return table.selected[0]

        # Edit parcel
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
                    'Status'
                ).classes('w-full')

                edit_count = ui.number(
                    'Number of Deliveries',
                    precision=0
                ).classes('w-full')

                previous = {
                    'status': '',
                    'tracking_id': ''
                }

                async def save_changes():

                    if (
                        any(
                            field.value is None
                            for field in (
                                edit_user_id,
                                edit_tracking_id,
                                edit_count
                            )
                        )
                        or not (edit_status.value or '').strip()
                    ):
                        ui.notify(
                            'Complete all fields.',
                            type='warning'
                        )
                        return

                    status = edit_status.value.strip()
                    tracking_id = str(int(edit_tracking_id.value))

                    newly_due = (
                        status.lower() == 'due'
                        and (
                            previous['status'].strip().lower() != 'due'
                            or previous['tracking_id'] != tracking_id
                        )
                    )

                    try:
                        await update_parcel(
                            int(edit_user_id.value),
                            status,
                            int(edit_tracking_id.value),
                            int(edit_count.value)
                        )

                    except APIError as error:
                        ui.notify(
                            f'Parcel update failed: {error}',
                            type='negative'
                        )
                        return

                    edit_dialog.close()

                    # Email collection code
                    if newly_due:

                        try:
                            response = await generate_delivery_otp(
                                tracking_id
                            )

                            if otp_rejected(response):
                                ui.notify(
                                    'Parcel saved, but the collection code '
                                    'could not be sent.',
                                    type='negative',
                                    timeout=10000
                                )

                            else:
                                ui.notify(
                                    'Parcel set to Due. '
                                    'Collection code requested by email.',
                                    type='positive',
                                    timeout=8000
                                )

                        except APIError as error:
                            ui.notify(
                                f'Parcel saved, but the collection code '
                                f'could not be sent: {error}',
                                type='negative',
                                timeout=10000
                            )

                    else:
                        ui.notify(
                            'Parcel updated.',
                            type='positive'
                        )

                    ui.navigate.reload()

                with ui.row().classes('justify-end w-full'):

                    ui.button(
                        'Cancel',
                        on_click=edit_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Save Changes',
                        on_click=save_changes
                    ).props('no-caps')

        # Open edit dialog
        def open_edit():

            parcel = selected_parcel()

            if parcel is None:
                return

            previous['status'] = str(
                parcel.get('status') or ''
            )

            previous['tracking_id'] = str(
                parcel.get('tracking_id') or ''
            )

            edit_user_id.set_value(
                parcel.get('userID')
            )

            edit_tracking_id.set_value(
                parcel.get('tracking_id')
            )

            edit_status.set_value(
                parcel.get('status', '')
            )

            edit_count.set_value(
                parcel.get('nDelivery')
            )

            edit_dialog.open()

        # Remove parcel
        with ui.dialog() as delete_dialog:

            with ui.card().classes('w-96 max-w-full p-5 gap-3'):

                ui.label('Remove Parcel').classes(
                    'text-lg font-semibold'
                )

                ui.label(
                    'This action cannot be undone.'
                )

                delete_id = ui.number(
                    'Parcel ID',
                    precision=0
                ).classes('w-full')

                async def confirm_remove():

                    if delete_id.value is None:
                        ui.notify(
                            'Enter an ID.',
                            type='warning'
                        )
                        return

                    try:
                        await remove_parcel(
                            int(delete_id.value)
                        )

                    except APIError as error:
                        ui.notify(
                            str(error),
                            type='negative'
                        )
                        return

                    delete_dialog.close()

                    ui.notify(
                        'Parcel removed.',
                        type='positive'
                    )

                    ui.navigate.reload()

                with ui.row().classes('justify-end w-full'):

                    ui.button(
                        'Cancel',
                        on_click=delete_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Confirm Removal',
                        color='negative',
                        on_click=confirm_remove
                    ).props('no-caps')

        # Send collection code
        async def send_code_to_selected():

            parcel = selected_parcel()

            if parcel is None:
                return

            if str(parcel.get('status', '')).strip().lower() != 'due':
                ui.notify(
                    'Only Due parcels can receive a collection code.',
                    type='warning'
                )
                return

            tracking_id = parcel.get('tracking_id')

            if tracking_id is None or not str(tracking_id).strip():
                ui.notify(
                    'The selected parcel has no tracking ID.',
                    type='negative'
                )
                return

            try:
                result = await generate_delivery_otp(
                    str(tracking_id)
                )

                if otp_rejected(result):
                    ui.notify(
                        'Could not send the collection code.',
                        type='negative'
                    )

                else:
                    ui.notify(
                        'Collection code requested by email.',
                        type='positive'
                    )

            except APIError as error:
                ui.notify(
                    f'Could not send collection code: {error}',
                    type='negative'
                )

        # Management buttons
        with ui.row().classes('gap-3'):

            ui.button(
                'Modify Selected Parcel',
                icon='edit',
                on_click=open_edit
            ).props('outline no-caps')

            ui.button(
                'Remove Parcel',
                icon='delete',
                color='negative',
                on_click=delete_dialog.open
            ).props('outline no-caps')

            ui.button(
                'Send Collection Code',
                icon='mail',
                on_click=send_code_to_selected
            ).props('outline no-caps')

        # Due parcels
        ui.label('Parcels Due').classes(
            'text-xl font-semibold mt-4'
        )

        try:
            due_rows = await get_due_parcels()

            if due_rows:

                # Due parcel columns
                column_labels = {
                    'roomNumber': 'Room Number',
                    'status': 'Status',
                    'tracking_id': 'Tracking ID',
                    'compartment_number': 'Compartment Number'
                }

                keys = list(due_rows[0].keys())

                due_columns = [
                    {
                        'name': key,
                        'field': key,
                        'label': column_labels.get(key, key),
                        'align': 'left'
                    }
                    for key in keys
                ]

                simple_rows = [
                    {
                        key: (
                            str(row.get(key))
                            if isinstance(row.get(key), (dict, list))
                            else row.get(key)
                        )
                        for key in keys
                    }
                    for row in due_rows
                ]

                ui.table(
                    columns=due_columns,
                    rows=simple_rows,
                    pagination=10
                ).classes('w-full')

            else:
                ui.label(
                    'No parcels currently due.'
                ).classes('text-slate-500')

        except APIError as error:
            ui.label(
                f'Unable to load parcels due: {error}'
            ).classes('text-red-700')
