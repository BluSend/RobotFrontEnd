"""BluSend robot touchscreen connected to the existing team backend.

The emailed collection PIN is checked by the actual verification endpoint.
Recipients enter one code only. We do not fake success or compartment unlocks.
"""

import os
from pathlib import Path

from nicegui import app, ui
from staff_portal.api_client import APIError, get_due_parcels, verify_delivery


# Robot configuration
PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_DIR / 'assets'
LOGO = ASSETS / 'logo.jpeg'

# Prevent a startup crash when the assets directory has not been created yet.
if ASSETS.is_dir():
    app.add_static_files('/assets', str(ASSETS))

# Optional: robot's job-assigned delivery ID can be provided by its controller.
# The recipient never enters or sees this ID. If it is not set, this UI
# checks GET /mail/list/ and only auto-selects a delivery if exactly one is due.
ACTIVE_DELIVERY_ID = os.getenv('BLUSEND_DELIVERY_ID', '').strip() or None


class DeliveryAssignmentError(Exception):
    """The robot cannot unambiguously identify the delivery to verify."""


def get_record_delivery_id(record):
    """Extract an ID from a /mail/list/ item, if exposed by the backend."""
    for key in ('delivery_id', 'deliveryID', 'deliveryId', 'id', 'ID'):
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


async def current_delivery():
    """Return (delivery ID, delivery record); never guess among several jobs."""
    if ACTIVE_DELIVERY_ID:
        return ACTIVE_DELIVERY_ID, {}

    due = await get_due_parcels()
    if len(due) == 0:
        raise DeliveryAssignmentError('No delivery is currently waiting for collection.')
    if len(due) > 1:
        raise DeliveryAssignmentError(
            'Several deliveries are pending. The robot needs its assigned '
            'delivery ID from the backend before a code can be checked.'
        )

    record = due[0]
    delivery_id = get_record_delivery_id(record)
    if delivery_id is None:
        raise DeliveryAssignmentError(
            'The pending delivery has no recognised delivery ID. '
            'Check the fields returned by GET /mail/list/.'
        )
    return delivery_id, record


def extract_compartment(record):
    """Only use a field expressly labelled as a compartment or slot."""
    if not isinstance(record, dict):
        return None
    for key in ('compartment_id', 'compartmentID', 'compartment',
                'compartment_number', 'compartmentNumber', 'slot'):
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None

MIN_PIN_LENGTH = 4
MAX_PIN_LENGTH = 8


# Main screen design
def base_screen():
    ui.colors(primary='#2563EB')
    ui.query('body').style('margin: 0; background: #EAF2FF;')
    ui.query('.nicegui-content').classes('w-full p-0')

    with ui.element('div').classes(
        'w-full flex items-center justify-center p-2'
    ).style('min-height: 100dvh;'):
        return ui.card().classes(
            'w-full flex flex-col rounded-2xl shadow-lg p-4 gap-3'
        ).style('max-width: 800px; min-height: 450px;')


# Main header
def screen_header():
    with ui.row().classes('w-full items-center justify-between'):
        if LOGO.is_file():
            ui.image('/assets/logo.jpeg').classes('w-28 h-12').props('fit-contain')
        else:
            ui.label('BluSend').classes('text-xl font-bold text-blue-700')

        ui.label('MAIL DELIVERY ROBOT').classes('text-xs text-gray-500')

    ui.separator()


# Interpret backend verification response
def interpret_verification(result):
    """Return (verified, unlocked, compartment) without assuming an unlock.

    verified is True, False or None (unknown response format).
    """
    if isinstance(result, bool):
        return result, False, None

    if isinstance(result, str):
        value = result.strip().lower()
        if value in ('true', 'verified', 'success'):
            return True, False, None
        if value in ('false', 'invalid', 'incorrect'):
            return False, False, None

    if isinstance(result, dict):
        verified = next(
            (
                result[key]
                for key in ('verified', 'valid', 'authenticated', 'success')
                if type(result.get(key)) is bool
            ),
            None,
        )
        unlocked = result.get('unlocked') is True
        compartment = extract_compartment(result)
        return verified, unlocked, compartment

    return None, False, None


# Home page
@ui.page('/')
def home_page():
    with base_screen():
        screen_header()

        with ui.column().classes(
            'w-full flex-1 items-center justify-center gap-4'
        ):
            ui.label('Welcome to BluSend').classes(
                'text-3xl font-bold text-gray-900'
            )
            ui.label('How can we help you today?').classes('text-gray-500')

            ui.button(
                'Collect Mail',
                icon='mail',
                on_click=lambda: ui.navigate.to('/pin_entry'),
            ).classes('w-64 h-14 text-lg')

            ui.button(
                'Help',
                icon='help_outline',
                on_click=lambda: ui.navigate.to('/help'),
            ).classes('w-64 h-12').props('outline')


# One-code collection screen
@ui.page('/pin_entry')
def pin_page():
    state = {'pin': '', 'busy': False}

    with base_screen():
        screen_header()

        with ui.row().classes(
            'w-full flex-1 items-start justify-between gap-4 flex-nowrap'
        ):
            with ui.column().classes('flex-1 gap-3'):
                ui.icon('lock_outline', size='38px', color='primary')

                ui.label('Enter your collection PIN').classes(
                    'text-xl font-bold text-gray-900'
                )
                ui.label('Use the keypad to enter the PIN sent to your email.').classes(
                    'text-sm text-gray-500'
                )

                digits = ui.label('—').classes(
                    'text-3xl font-mono tracking-widest text-blue-700'
                )
                status = ui.label('').classes('text-sm text-gray-700')

                def refresh_display():
                    digits.set_text('●' * len(state['pin']) or '—')

                def press_key(key):
                    if state['busy']:
                        return

                    if key == 'Clear':
                        state['pin'] = ''
                    elif key == '⌫':
                        state['pin'] = state['pin'][:-1]
                    elif len(state['pin']) < MAX_PIN_LENGTH:
                        state['pin'] += key

                    status.set_text('')
                    refresh_display()

                async def submit():
                    if state['busy']:
                        return

                    if not MIN_PIN_LENGTH <= len(state['pin']) <= MAX_PIN_LENGTH:
                        status.set_text('Enter the complete PIN from your email.')
                        return

                    state['busy'] = True
                    action.disable()
                    status.set_text('Checking your code with the backend...')

                    try:
                        delivery_id, delivery_record = await current_delivery()

                        # Real API call: PUT /mail/verify/{delivery_id}
                        # with {"value": "<entered code>"}.
                        result = await verify_delivery(delivery_id, state['pin'])
                        verified, unlocked, returned_compartment = interpret_verification(result)
                        compartment = returned_compartment or extract_compartment(delivery_record)

                        if verified is False:
                            status.set_text('Incorrect or expired code. Please try again.')
                        elif verified is None:
                            status.set_text(
                                'Backend replied, but did not explicitly confirm '
                                'whether this code is correct. Check the API response.'
                            )
                        elif compartment is not None and unlocked:
                            status.set_text(
                                f'Code correct! Compartment {compartment} is unlocked. '
                                'Please collect your parcel.'
                            )
                        elif compartment is not None:
                            status.set_text(
                                f'Code correct! Collect your parcel from '
                                f'Compartment {compartment} once it opens.'
                            )
                        else:
                            status.set_text(
                                'Code correct! The backend did not provide a '
                                'compartment number. Please contact mailroom staff.'
                            )
                    except DeliveryAssignmentError as error:
                        status.set_text(str(error))
                    except APIError as error:
                        detail = str(error)
                        if any(f'HTTP {status_code}' in detail for status_code in (400, 401, 403)):
                            status.set_text('Code not accepted. Please check and try again.')
                        else:
                            status.set_text(
                                'Cannot verify with the backend right now. '
                                'Please contact mailroom staff.'
                            )
                    finally:
                        state['pin'] = ''
                        refresh_display()
                        state['busy'] = False
                        action.enable()

                action = ui.button(
                    'Verify PIN', on_click=submit
                ).classes('w-52 h-11')

                ui.button(
                    'Back to Home',
                    icon='arrow_back',
                    on_click=lambda: ui.navigate.to('/'),
                ).props('flat no-caps')

            # On-screen numeric keypad
            with ui.grid(columns=3).classes('gap-2'):
                for key in (
                    '1', '2', '3',
                    '4', '5', '6',
                    '7', '8', '9',
                    'Clear', '0', '⌫',
                ):
                    ui.button(
                        key,
                        on_click=lambda value=key: press_key(value),
                    ).props('no-caps').style(
                        'width: 75px; height: 54px; font-size: 19px;'
                    )


# Help page
@ui.page('/help')
def help_page():
    with base_screen():
        screen_header()

        with ui.column().classes('w-full flex-1 justify-center gap-3'):
            ui.label('How can we help?').classes('text-2xl font-bold')
            ui.label('1. Select Collect Mail on the home screen.')
            ui.label('2. Enter the collection PIN sent to your email.')
            ui.label('3. Collect your mail only when the compartment opens.')

            ui.separator()
            ui.label(
                'If your PIN is rejected or the compartment does not '
                'open, contact mailroom staff.'
            ).classes('text-gray-600')

            ui.button(
                'Back to Home',
                icon='arrow_back',
                on_click=lambda: ui.navigate.to('/'),
            ).props('outline no-caps').classes('w-48 h-11')


# Run the robot interface
if __name__ in ('__main__', '__mp_main__'):
    settings = {
        'title': 'BluSend',
        'host': '127.0.0.1',
        'port': 8080,
    }
    if LOGO.is_file():
        settings['favicon'] = str(LOGO)
    ui.run(**settings)
