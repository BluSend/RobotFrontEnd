
from nicegui import ui

from staff_portal.layout import page_layout
from staff_portal.api_client import (
    APIError,
    get_users,
    add_user,
    update_user,
    remove_user,
)


# -------------------- INPUT VALIDATION --------------------

def validate_recipient(name, email, room):

    if not name or not email or not room:
        return 'Complete all recipient fields.'

    if '@' not in email or '.' not in email.split('@')[-1]:
        return 'Enter a valid email address.'

    return None


# -------------------- RECIPIENT DIRECTORY PAGE --------------------

@ui.page('/recipients')
async def recipients_page():

    with page_layout('Recipient Directory', '/recipients'):

        ui.label(
            'Register and manage recipients in the shared system.'
        ).classes('text-slate-500')


        # -------------------- REGISTER RECIPIENT --------------------

        with ui.card().classes('w-full p-5 gap-4'):

            ui.label('Register New Recipient').classes(
                'text-xl font-semibold'
            )

            name = ui.input(
                'Full Name'
            ).props('outlined').classes('w-full')

            email = ui.input(
                'University Email Address'
            ).props('outlined').classes('w-full')

            room = ui.input(
                'Room Number'
            ).props('outlined').classes('w-full')


            async def register_recipient():

                full_name = (name.value or '').strip()
                email_address = (email.value or '').strip()
                room_number = (room.value or '').strip()

                error = validate_recipient(
                    full_name,
                    email_address,
                    room_number
                )

                if error:
                    ui.notify(error, type='warning')
                    return

                try:
                    await add_user(
                        full_name,
                        room_number,
                        email_address
                    )

                except APIError as error:
                    ui.notify(str(error), type='negative')
                    return

                ui.notify(
                    'Recipient registered successfully.',
                    type='positive'
                )

                ui.navigate.reload()


            ui.button(
                'Register Recipient',
                icon='person_add',
                on_click=register_recipient
            ).props('no-caps')


        # -------------------- LOAD RECIPIENTS --------------------

        ui.label('Registered Recipients').classes(
            'text-xl font-semibold mt-4'
        )

        try:
            users = await get_users()

        except APIError as error:
            users = []

            ui.label(
                f'Unable to load recipients: {error}'
            ).classes('text-red-700')

        rows = [
            {
                'userID': user.get('userID', user.get('id')),
                'name': user.get('name', ''),
                'roomNumber': user.get('roomNumber', ''),
                'email': user.get('email', '')
            }
            for user in users
        ]


        # -------------------- RECIPIENT TABLE --------------------

        search = ui.input(
            'Search Recipients'
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
                ('userID', 'User ID'),
                ('name', 'Full Name'),
                ('roomNumber', 'Room Number'),
                ('email', 'Email Address')
            ]
        ]

        table = ui.table(
            columns=columns,
            rows=rows,
            row_key='userID',
            selection='single',
            pagination=10
        ).classes('w-full').props('flat bordered')

        search.bind_value(table, 'filter')


        # -------------------- SELECT RECIPIENT --------------------

        def selected_user():

            if not table.selected:
                ui.notify(
                    'Select a recipient first.',
                    type='warning'
                )
                return None

            user = table.selected[0]

            if user['userID'] is None:
                ui.notify(
                    'The backend did not provide a user ID.',
                    type='negative'
                )
                return None

            return user


        # -------------------- EDIT RECIPIENT DIALOG --------------------

        selected_id = {'value': None}

        with ui.dialog() as edit_dialog:

            with ui.card().classes('w-96 max-w-full p-5 gap-3'):

                ui.label('Edit Recipient').classes(
                    'text-lg font-semibold'
                )

                edit_name = ui.input(
                    'Full Name'
                ).classes('w-full')

                edit_email = ui.input(
                    'Email Address'
                ).classes('w-full')

                edit_room = ui.input(
                    'Room Number'
                ).classes('w-full')


                async def save_changes():

                    full_name = (edit_name.value or '').strip()
                    email_address = (edit_email.value or '').strip()
                    room_number = (edit_room.value or '').strip()

                    error = validate_recipient(
                        full_name,
                        email_address,
                        room_number
                    )

                    if error:
                        ui.notify(error, type='warning')
                        return

                    try:
                        await update_user(
                            int(selected_id['value']),
                            full_name,
                            room_number,
                            email_address
                        )

                    except (APIError, ValueError, TypeError) as error:
                        ui.notify(str(error), type='negative')
                        return

                    edit_dialog.close()

                    ui.notify(
                        'Recipient updated successfully.',
                        type='positive'
                    )

                    ui.navigate.reload()


                with ui.row().classes('w-full justify-end gap-2'):

                    ui.button(
                        'Cancel',
                        on_click=edit_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Save Changes',
                        icon='save',
                        on_click=save_changes
                    ).props('no-caps')


        # -------------------- OPEN EDIT DIALOG --------------------

        def open_edit_dialog():

            user = selected_user()

            if user is None:
                return

            selected_id['value'] = user['userID']

            edit_name.set_value(user['name'])
            edit_email.set_value(user['email'])
            edit_room.set_value(user['roomNumber'])

            edit_dialog.open()


        # -------------------- REMOVE RECIPIENT DIALOG --------------------

        delete_id = {'value': None}

        with ui.dialog() as delete_dialog:

            with ui.card().classes('w-96 max-w-full p-5 gap-3'):

                ui.label('Remove Recipient').classes(
                    'text-lg font-semibold'
                )

                ui.label(
                    'Are you sure you want to remove this recipient? '
                    'This action cannot be undone.'
                )


                async def confirm_removal():

                    try:
                        await remove_user(int(delete_id['value']))

                    except (APIError, ValueError, TypeError) as error:
                        ui.notify(str(error), type='negative')
                        return

                    delete_dialog.close()

                    ui.notify(
                        'Recipient removed successfully.',
                        type='positive'
                    )

                    ui.navigate.reload()


                with ui.row().classes('w-full justify-end gap-2'):

                    ui.button(
                        'Cancel',
                        on_click=delete_dialog.close
                    ).props('flat no-caps')

                    ui.button(
                        'Remove Recipient',
                        color='negative',
                        on_click=confirm_removal
                    ).props('no-caps')


        # -------------------- OPEN DELETE DIALOG --------------------

        def open_delete_dialog():

            user = selected_user()

            if user is None:
                return

            delete_id['value'] = user['userID']

            delete_dialog.open()


        # -------------------- MANAGEMENT BUTTONS --------------------

        with ui.row().classes('gap-3'):

            ui.button(
                'Edit Selected Recipient',
                icon='edit',
                on_click=open_edit_dialog
            ).props('outline no-caps')

            ui.button(
                'Remove Selected Recipient',
                icon='delete',
                color='negative',
                on_click=open_delete_dialog
            ).props('outline no-caps')
