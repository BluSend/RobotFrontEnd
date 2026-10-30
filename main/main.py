from nicegui import ui

from nicegui import app,ui

app.add_static_files('/assets', 'assets')

def base_screen():
    ui.colors(primary='#2563EB')

    ui.query('body').style('margin: 0; background: #EAF2FF')

    ui.query('.nicegui-content').classes('w-full p-0')

    with ui.element('div').classes(
        'w-full min-h-screen flex items-center justify-center p-4'
    ):
        return ui.card().classes(
            'w-full flex flex-col rounded-3xl shadow-xl p-8'
        ).style('max-width: 800px; min-height: 480px;')


@ui.page('/')
def home_page():
    with base_screen():
        with ui.row().classes('w-full items-center justify-between'):
            ui.image('/assets/logo.jpeg').classes('w-18 h-10').props('fit-contain')

            ui.label('MAIL DELIVERY ROBOT').classes('text-xs text-gray-500')

            ui.separator()

        with ui.column().classes(
            'w-full flex-1 items-center justify-center gap-5'
        ):
            ui.label('Welcome to BluSend').classes('text-3xl font-bold text-gray-900')

            ui.label('How can we help you today?').classes('text-gray-500')

            ui.button('Collect Mail',
            icon='mail',
            on_click=lambda: ui.navigate.to('/pin_entry')
            ).classes('w-64 h-14 text-lg')

            ui.button('Help',
                icon='help_outline',
                on_click=lambda: ui.navigate.to('/help')
            ).classes('w-64 h-14 text-lg').props('outline')

@ui.page('/pin_entry')
def pin_page():
    with base_screen():
        ui.image('/assets/logo.jpeg').classes('w-18 h-10').props('fit-contain')

        ui.separator()

        with ui.column().classes(
            'w-full flex-1 items-center justify-center gap-4'
        ):
            ui.icon('lock_outline', size='50px', color='primary')

            ui.label('Enter your PIN').classes(' text-3xl font-bold text-gray-900')

            ui.label('Please enter the PIN sent to your email.').classes('text-gray-500')

            pin_input = ui.input(
                label='Delivery PIN',
                password=True
            ).props('outlined inputmode=numeric').classes('w-64')

            ui.button(
                'Verify PIN',
                on_click=lambda: ui.notify(
                    'ERROR: PIN verification is not connected yet.'
                )
            ).classes('w-64 h-12')

            ui.button(
                'Back to Home',
                icon='arrow_back',
                on_click=lambda: ui.navigate.to('/')
            ).props('flat')

@ui.page('/help')
def help_page():
    with base_screen():
        ui.image('/assets/logo.jpeg').classes('w-18 h-10').props('fit-contain')

        ui.separator()

        with ui.column().classes('w-full flex-1 justify-center gap-4'):
            ui.label('How can we help?').classes(
                'text-2xl font-bold text-gray-900'
            )

            ui.label('Follow these steps to collect your mail:').classes(
                'text-gray-500'
            )

            ui.label('1. Select Collect Mail on the home screen.')
            ui.label('2. Enter the PIN sent to your email.')
            ui.label('3. Collect your mail once the compartment unlocks.')

            ui.separator()

            ui.label('Having trouble?').classes('text-lg font-semibold text-gray-900')

            ui.label(
                'If your PIN is incorrect or your compartment does not open, '
                'please contact the mailroom staff for assistance.'
            ).classes('text-gray-600')

            ui.button(
                'Back to Home',
                icon='arrow_back',
                on_click=lambda: ui.navigate.to('/')
            ).props('outline').classes('w-48 h-12')

ui.run(title='BluSend', favicon='assets/logo.jpeg', host='127.0.0.1')
...
