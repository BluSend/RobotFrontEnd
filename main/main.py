
from pathlib import Path

from nicegui import app, ui
from staff_portal.api_client import APIError, get_due_parcels, verify_delivery


# Project settings
PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_DIR / 'assets'
LOGO = ASSETS / 'logo.jpeg'

if ASSETS.is_dir():
    app.add_static_files('/assets', str(ASSETS))

MIN_CODE_LENGTH = 4
MAX_CODE_LENGTH = 8


class NoDueParcelsError(Exception):
    pass


# Due parcels
async def get_due_tracking_ids():
    parcels = await get_due_parcels()
    tracking_ids = []

    for parcel in parcels:
        if not isinstance(parcel, dict):
            continue

        if str(parcel.get('status', 'Due')).strip().lower() != 'due':
            continue

        for field in ('tracking_id', 'trackingID', 'trackingId'):
            value = parcel.get(field)

            if value is not None and str(value).strip():
                tracking_id = str(value).strip()

                if tracking_id not in tracking_ids:
                    tracking_ids.append(tracking_id)
                break

    if not tracking_ids:
        raise NoDueParcelsError(
            'There are no Due parcels available for verification.'
        )

    return tracking_ids


# Backend responses
def read_status(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return None

    message = str(value).strip().lower()

    if message in ('true', 'false'):
        return message == 'true'

    failed_words = (
        'invalid', 'incorrect', 'expired', 'failed', 'failure', 'fail',
        'unsuccessful', 'not successful', 'rejected', 'wrong',
        'unauthorised', 'unauthorized', 'not verified', 'not valid',
        'not found', 'not accepted', 'denied', 'error', 'unable to'
    )

    success_words = (
        'verified', 'valid', 'correct', 'success',
        'accepted', 'authenticated'
    )

    if any(word in message for word in failed_words):
        return False

    if any(word in message for word in success_words):
        return True

    return None


def check_response(response):
    if isinstance(response, dict):

        for key in ('verified', 'valid', 'authenticated', 'success'):
            value = response.get(key)

            if isinstance(value, bool):
                return value

        for key in ('status', 'message', 'detail', 'result'):
            result = read_status(response.get(key))

            if result is not None:
                return result

        return None

    return read_status(response)


def incorrect_code_error(error):
    message = str(error).lower()

    client_error = any(
        f'http {code}' in message
        for code in (400, 401, 403)
    )

    return client_error and read_status(message) is False


def connection_error_message(error):
    message = str(error).lower()

    if 'backend address' in message or 'blusend_api_url' in message:
        return 'Connection settings are missing. Please contact staff.'

    if any(f'http {code}' in message for code in (400, 401, 403, 404, 422)):
        return 'Your request could not be completed. Please contact staff.'

    return 'Connection unavailable. Please try again.'


# Code verification
async def verify_collection_code(code):
    tracking_ids = await get_due_tracking_ids()
    unknown_result = False

    for tracking_id in tracking_ids:
        try:
            response = await verify_delivery(str(tracking_id), code)
            result = check_response(response)

        except APIError as error:
            if incorrect_code_error(error):
                continue

            unknown_result = True
            continue

        if result is True:
            return True

        if result is None:
            unknown_result = True

    if unknown_result:
        return None

    return False


# Touchscreen styling
STYLE = '''
<style>
html, body {
    width: 100%;
    height: 100%;
    margin: 0;
    background: white;
    overflow: hidden;
}

.nicegui-content {
    width: 100%;
    height: 100dvh;
    padding: 0 !important;
}

.screen {
    width: 100%;
    height: 100dvh;
    box-sizing: border-box;
    padding: 20px;
    gap: 12px;
    background: white;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.header {
    width: 100%;
    min-height: 100px;
    flex-shrink: 0;
}

.logo {
    width: 230px;
    height: 100px;
}

.title {
    font-size: 28px;
    font-weight: 700;
    line-height: 1.2;
}

.instructions {
    font-size: 17px;
    line-height: 1.4;
}

.pin {
    font-size: 36px;
    color: #2563eb;
    letter-spacing: 5px;
    min-height: 44px;
}

.message {
    font-size: 16px;
    min-height: 44px;
    max-height: 90px;
    overflow-y: auto;
}

.home {
    width: 100%;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
}

.home .q-btn {
    width: 270px;
    min-height: 54px;
    font-size: 17px;
}

.code-layout {
    flex: 1;
    min-height: 0;
    width: 100%;
    max-width: 1060px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
}

.code-details {
    flex: 1;
    min-width: 0;
    max-width: 560px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 14px;
}

.keypad {
    display: grid;
    grid-template-columns: repeat(3, 100px);
    gap: 10px;
    flex-shrink: 0;
}

.keypad .q-btn {
    height: 68px;
    min-height: 68px;
    font-size: 23px;
}

.help {
    flex: 1;
    min-height: 0;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.help-content {
    width: 100%;
    max-width: 720px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.help-line {
    font-size: 16px;
    line-height: 1.5;
}

@media (max-width: 950px), (max-height: 550px) {
    .screen {
        padding: 10px;
        gap: 6px;
    }

    .header {
        min-height: 62px;
    }

    .logo {
        width: 160px;
        height: 62px;
    }

    .title {
        font-size: 21px;
    }

    .instructions, .message, .help-line {
        font-size: 13px;
    }

    .pin {
        font-size: 28px;
        min-height: 32px;
    }

    .message {
        min-height: 30px;
        max-height: 55px;
    }

    .home {
        gap: 10px;
    }

    .home .q-btn {
        width: 240px;
        min-height: 44px;
        font-size: 15px;
    }

    .code-layout {
        max-width: 800px;
        gap: 18px;
    }

    .code-details {
        gap: 7px;
    }

    .keypad {
        grid-template-columns: repeat(3, 78px);
        gap: 6px;
    }

    .keypad .q-btn {
        height: 48px;
        min-height: 48px;
        font-size: 19px;
    }

    .help-content {
        max-width: 620px;
        gap: 8px;
    }
}

@media (max-width: 620px) {
    html, body {
        overflow-y: auto;
    }

    .screen {
        height: auto;
        min-height: 100dvh;
        overflow: visible;
    }

    .code-layout {
        flex-direction: column;
        justify-content: center;
    }

    .code-details {
        width: 100%;
        align-items: center;
        text-align: center;
    }
}
</style>
'''


# Screen layout
def base_screen():
    ui.add_head_html(STYLE)
    ui.colors(primary='#2563EB')

    return ui.column().classes('screen')


def screen_header():
    with ui.row().classes('header items-center justify-between no-wrap'):

        if LOGO.is_file():
            ui.image('/assets/logo.jpeg').classes('logo').props('fit=contain')
        else:
            ui.label('BluSend').classes('text-xl font-bold text-blue-600')

        ui.label('MAIL DELIVERY ROBOT').classes('text-xs text-gray-500')

    ui.separator()


# Home page
@ui.page('/')
def home_page():
    with base_screen():
        screen_header()

        with ui.element('div').classes('home'):
            ui.label('Welcome to BluSend').classes('title text-gray-900')

            ui.label(
                'Your collection code has been sent to your email.'
            ).classes('instructions text-gray-500')

            ui.button(
                'Collect Mail',
                icon='mail',
                on_click=lambda: ui.navigate.to('/pin_entry')
            ).props('no-caps')

            ui.button(
                'Help',
                icon='help_outline',
                on_click=lambda: ui.navigate.to('/help')
            ).props('outline no-caps')


# Code entry page
@ui.page('/pin_entry')
def pin_page():
    state = {'code': '', 'busy': False}

    with base_screen():
        screen_header()

        with ui.element('div').classes('code-layout'):
            with ui.element('div').classes('code-details'):

                ui.icon('lock_outline', size='31px', color='primary')

                ui.label(
                    'Enter your collection code'
                ).classes('title text-gray-900')

                ui.label(
                    'Use the keypad to enter the code from your email.'
                ).classes('instructions text-gray-500')

                digits = ui.label('—').classes('pin')

                status = ui.label(
                    'Check your email for the collection code.'
                ).classes('message text-gray-700')

                # Keypad input
                def update_display():
                    digits.set_text('●' * len(state['code']) or '—')

                def press_key(key):
                    if state['busy']:
                        return

                    if key == 'Clear':
                        state['code'] = ''

                    elif key == '⌫':
                        state['code'] = state['code'][:-1]

                    elif len(state['code']) < MAX_CODE_LENGTH:
                        state['code'] += key

                    status.set_text('')
                    update_display()

                # Verify code
                async def verify_code():
                    if state['busy']:
                        return

                    if not MIN_CODE_LENGTH <= len(state['code']) <= MAX_CODE_LENGTH:
                        status.set_text(
                            'Please enter the complete code from your email.'
                        )
                        return

                    state['busy'] = True
                    verify_button.disable()
                    status.set_text('Checking your code...')

                    try:
                        result = await verify_collection_code(state['code'])

                        if result is True:
                            status.set_text(
                                'Authentication Successful! Your code is correct.'
                            )

                        elif result is False:
                            status.set_text(
                                'Authentication Failed. Incorrect or expired code.'
                            )

                        else:
                            status.set_text(
                                'Unable to verify your code. '
                                'Please try again or contact staff.'
                            )

                    except NoDueParcelsError as error:
                        status.set_text(str(error))

                    except APIError as error:
                        status.set_text(connection_error_message(error))

                    finally:
                        state['code'] = ''
                        update_display()
                        state['busy'] = False
                        verify_button.enable()

                verify_button = ui.button(
                    'Verify Code',
                    on_click=verify_code
                ).props('no-caps')

                ui.button(
                    'Back to Home',
                    icon='arrow_back',
                    on_click=lambda: ui.navigate.to('/')
                ).props('flat no-caps dense')

            with ui.element('div').classes('keypad'):
                for key in (
                    '1', '2', '3',
                    '4', '5', '6',
                    '7', '8', '9',
                    'Clear', '0', '⌫'
                ):
                    ui.button(
                        key,
                        on_click=lambda value=key: press_key(value)
                    ).props('no-caps')


# Help page
@ui.page('/help')
def help_page():
    with base_screen():
        screen_header()

        with ui.element('div').classes('help'):
            with ui.element('div').classes('help-content'):

                ui.label('How can we help?').classes('title text-gray-900')

                steps = (
                    '1. Staff mark your parcel Due and send a code to your email.',
                    '2. Check your inbox and enter the emailed code.',
                    '3. Press Verify Code to check your code.',
                    '4. The screen shows Authentication Successful or Failed.'
                )

                for step in steps:
                    ui.label(step).classes('help-line text-gray-900')

                ui.label(
                    'If your code is rejected, contact mailroom staff.'
                ).classes('text-sm text-gray-600')

                ui.button(
                    'Back to Home',
                    icon='arrow_back',
                    on_click=lambda: ui.navigate.to('/')
                ).props('outline no-caps')


# Run application
if __name__ in ('__main__', '__mp_main__'):
    settings = {
        'title': 'BluSend',
        'host': '127.0.0.1',
        'port': 8080
    }

    if LOGO.is_file():
        settings['favicon'] = str(LOGO)

    ui.run(**settings)
