from pathlib import Path

from nicegui import app, ui
from staff_portal.api_client import APIError, verify_delivery


# Robot config

ASSETS = Path(__file__).resolve().parent / 'assets'
app.add_static_files('/assets', str(ASSETS))

# Testing: enter the delivery reference before the PIN.
# Later this ID should come from the robot's assigned delivery job.
ACTIVE_DELIVERY_ID = None

MIN_PIN_LENGTH = 4
MAX_PIN_LENGTH = 8


# Main screen design

def base_screen():

    ui.colors(primary='#2563EB')

    ui.query('body').style(
        'margin: 0; background: #EAF2FF;'
    )

    ui.query('.nicegui-content').classes('w-full p-0')

    with ui.element('div').classes(
        'w-full flex items-center justify-center p-2'
    ).style('min-height: 100dvh;'):

        return ui.card().classes(
            'w-full flex flex-col rounded-2xl shadow-lg p-4 gap-3'
        ).style(
            'max-width: 800px; min-height: 450px;'
        )


# Main header

def screen_header():

    with ui.row().classes(
        'w-full items-center justify-between'
    ):

        ui.image('/assets/logo.jpeg').classes(
            'w-28 h-12'
        ).props('fit-contain')

        ui.label('MAIL DELIVERY ROBOT').classes(
            'text-xs text-gray-500'
        )

    ui.separator()


# Verifying backend response

def interpret_verification(result):
    """
    Returns: (verified, unlocked, compartment)

    verified can be True, False or None.
    None means the backend response format is unknown.
    """

    if isinstance(result, bool):
        return result, False, None

    if isinstance(result, str):

        value = result.strip().lower()

        if value in ('true', 'verified'):
            return True, False, None

        if value in ('false', 'invalid', 'incorrect'):
            return False, False, None

    if isinstance(result, dict):

        verified = next(
            (
                result[key]
                for key in (
                    'verified',
                    'valid',
                    'authenticated',
                    'success'
                )
                if type(result.get(key)) is bool
            ),
            None
        )

        unlocked = result.get('unlocked') is True

        compartment = (
            result.get('compartment_id')
            or result.get('compartmentID')
            or result.get('compartment')
        )

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

            ui.label('How can we help you today?').classes(
                'text-gray-500'
            )

            ui.button(
                'Collect Mail',
                icon='mail',
                on_click=lambda: ui.navigate.to('/pin_entry')
            ).classes('w-64 h-14 text-lg')

            ui.button(
                'Help',
                icon='help_outline',
                on_click=lambda: ui.navigate.to('/help')
            ).classes(
                'w-64 h-12'
            ).props('outline')


# Pin entry

@ui.page('/pin_entry')
def pin_page():

    state = {
        'stage': (
            'pin' if ACTIVE_DELIVERY_ID is not None
            else 'reference'
        ),
        'reference': (
            str(ACTIVE_DELIVERY_ID)
            if ACTIVE_DELIVERY_ID is not None
            else ''
        ),
        'pin': '',
        'busy': False
    }

    with base_screen():

        screen_header()

        with ui.row().classes(
            'w-full flex-1 items-start justify-between gap-4 flex-nowrap'
        ):

            # Pin info

            with ui.column().classes('flex-1 gap-3'):

                ui.icon(
                    'lock_outline',
                    size='38px',
                    color='primary'
                )

                title = ui.label(
                    'Enter delivery reference'
                ).classes(
                    'text-xl font-bold text-gray-900'
                )

                instructions = ui.label(
                    'Enter the delivery reference provided with your email.'
                ).classes('text-sm text-gray-500')

                digits = ui.label('—').classes(
                    'text-3xl font-mono tracking-widest text-blue-700'
                )

                status = ui.label('').classes(
                    'text-sm text-gray-700'
                )


                # Refreshing display

                def refresh_display():

                    if state['stage'] == 'reference':

                        digits.set_text(
                            state['reference'] or '—'
                        )

                    else:

                        digits.set_text(
                            '●' * len(state['pin']) or '—'
                        )


                # Numpad input

                def press_key(key):

                    if state['busy']:
                        return

                    field = (
                        'reference'
                        if state['stage'] == 'reference'
                        else 'pin'
                    )

                    maximum = (
                        10 if field == 'reference'
                        else MAX_PIN_LENGTH
                    )

                    if key == 'Clear':

                        state[field] = ''

                    elif key == '⌫':

                        state[field] = state[field][:-1]

                    elif len(state[field]) < maximum:

                        state[field] += key

                    status.set_text('')

                    refresh_display()


                # Input submission

                async def submit():

                    if state['busy']:
                        return

                    # Step 1: identify the delivery
                    if state['stage'] == 'reference':

                        if (
                            not state['reference']
                            or int(state['reference']) <= 0
                        ):

                            status.set_text(
                                'Enter a valid delivery reference.'
                            )
                            return

                        state['stage'] = 'pin'

                        title.set_text(
                            'Enter your delivery PIN'
                        )

                        instructions.set_text(
                            'Use the keypad to enter the PIN sent to your email.'
                        )

                        action.set_text('Verify PIN')

                        status.set_text('')

                        refresh_display()

                        return

                    # Step 2: validating the entered PIN length
                    if not (
                        MIN_PIN_LENGTH
                        <= len(state['pin'])
                        <= MAX_PIN_LENGTH
                    ):

                        status.set_text(
                            'Enter the complete PIN from your email.'
                        )
                        return

                    # Step 3: contacting the backend
                    state['busy'] = True
                    action.disable()

                    status.set_text('Checking your PIN...')

                    try:

                        result = await verify_delivery(
                            int(state['reference']),
                            state['pin']
                        )

                        verified, unlocked, compartment = (
                            interpret_verification(result)
                        )

                        if verified is False:

                            status.set_text(
                                'PIN not accepted. Please try again.'
                            )

                        elif verified is None:

                            status.set_text(
                                'The server response could not confirm '
                                'verification. Please contact mailroom staff.'
                            )

                        elif unlocked:

                            location = (
                                f'Compartment {compartment}'
                                if compartment is not None
                                else 'Your compartment'
                            )

                            status.set_text(
                                f'{location} is unlocked. '
                                'Please collect your mail.'
                            )

                        else:

                            status.set_text(
                                'PIN verified. Compartment opening is '
                                'not yet confirmed. Please contact '
                                'mailroom staff.'
                            )

                    except APIError:

                        status.set_text(
                            'Unable to verify the PIN with the server. '
                            'Please contact mailroom staff.'
                        )

                    finally:

                        state['pin'] = ''

                        refresh_display()

                        state['busy'] = False
                        action.enable()


                # Buttons

                action = ui.button(
                    'Continue',
                    on_click=submit
                ).classes('w-52 h-11')

                ui.button(
                    'Back to Home',
                    icon='arrow_back',
                    on_click=lambda: ui.navigate.to('/')
                ).props('flat no-caps')


            # Numeric Keypad setup

            with ui.grid(columns=3).classes('gap-2'):

                for key in (
                    '1', '2', '3',
                    '4', '5', '6',
                    '7', '8', '9',
                    'Clear', '0', '⌫'
                ):

                    ui.button(
                        key,
                        on_click=lambda value=key: press_key(value)
                    ).props('no-caps').style(
                        'width: 75px; height: 54px; font-size: 19px;'
                    )


# Help page

@ui.page('/help')
def help_page():

    with base_screen():

        screen_header()

        with ui.column().classes(
            'w-full flex-1 justify-center gap-3'
        ):

            ui.label('How can we help?').classes(
                'text-2xl font-bold'
            )

            ui.label(
                '1. Select Collect Mail on the home screen.'
            )

            ui.label(
                '2. Enter your delivery reference, if requested.'
            )

            ui.label(
                '3. Enter the PIN sent to your email.'
            )

            ui.label(
                '4. Collect your mail only when the compartment opens.'
            )

            ui.separator()

            ui.label(
                'If your PIN is rejected or the compartment does not '
                'open, contact mailroom staff.'
            ).classes('text-gray-600')

            ui.button(
                'Back to Home',
                icon='arrow_back',
                on_click=lambda: ui.navigate.to('/')
            ).props('outline no-caps').classes('w-48 h-11')


# Main interface run:

if __name__ in ('__main__', '__mp_main__'):

    ui.run(
        title='BluSend',
        favicon=str(ASSETS / 'logo.jpeg'),
        host='127.0.0.1',
        port=8080
    )
