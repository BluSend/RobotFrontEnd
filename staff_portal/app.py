from nicegui import ui

from staff_portal.config import (
    APP_TITLE,
    APP_PORT
)

# Register Website Pages
from staff_portal.pages import (
    dashboard,
    recipients,
    parcels
)

# Start Website
if __name__ in ('__main__', '__mp_main__'):

    ui.run(
        title=APP_TITLE,
        port=APP_PORT,
        reload=True
    )
