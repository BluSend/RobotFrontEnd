# This is the only module that makes HTTP requests to the backend.
import json
from urllib.parse import quote
import httpx
from staff_portal.config import API_BASE_URL

# API Error Handling
class APIError(Exception):
    pass

# HTTP Request Handling
async def api_request(method, endpoint, **kwargs):

    try:
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=10.0
        ) as client:

            response = await client.request(
                method,
                endpoint,
                **kwargs
            )

            response.raise_for_status()

    except httpx.HTTPStatusError as error:

        raise APIError(
            f'Backend return HTTP {error.response.status_code}: '
            f'{error.response.text[:250]}'
        ) from error

    except httpx.RequestError as error:

        raise APIError(
            f'Unable to connect to the backend: {error}'
        ) from error

    if not response.content:
        return None

    try:
        result = response.json()

    except ValueError:
        return response.text

    if isinstance(result, str):

        try:
            return json.loads(result)

        except (ValueError, TypeError):
            return result

    return result

# Response Processing
def extract_records(response, record_type):

    if isinstance(response, list):

        if all(isinstance(item, dict) for item in response):
            return response

    if isinstance(response, dict):

        for key in (
            record_type,
            'data',
            'items',
            'results',
            'records'
        ):
            records = response.get(key)

            if isinstance(records, list):

                if all(isinstance(item, dict) for item in records):
                    return records

    raise APIError(
        f'Unexpected {record_type} response format.'
        'Check the actual response in Swagger.'
    )


# User management
async def get_users():

    response = await api_request(
        'GET',
        '/admin/users/all'
    )

    return extract_records(response, 'users')

async def get_user(user_id):

    return await api_request(
        'GET',
        f'/admin/users/{user_id}'
    )

async def add_user(name, room_number, email):

    return await api_request(
        'POST',
        '/admin/users/add',
        json={
            'name':name,
            'roomNumber': room_number,
            'email':email
        }
    )

async def update_user(user_id, name, room_number, email):

    return await api_request(
        'PUT',
        '/admin/users/modify',
        json={
            'userID': user_d,
            'name':name,
            'roomNumber':room_number,
            'email':email
        }
    )

async def remove_user(user_id):
    return await api_request(
        'DELETE',
        f'/admin/users/remove/{user_id}'
    )

# Parcel Management

async def get_parcels():

    response = await api_request(
        'GET',
        '/admin/parcels/all'
    )

    return extract_records(response, 'parcels')

async def add_parcel(backend_id):

    return await api_request(
        'POST',
        '/admin/parcels/add',
        json={
            'id':backend_id
        }
    )

async def update_parcel(user_id, status, tracking_id, n_delivery):

    return await api_request(
        'PUT',
        '/admin/parcels/modify',
        json={
            'userID':user_id,
            'status':status,
            'tracking_id':tracking_id,
            'nDelivery':n_delivery
        }
    )

async def remove_parcel(parcel_id):

    return await api_request(
        'DELETE',
        '/admin/parcels/remove',
        json={
            'id':parcel_id
        }
    )

# Delivery Operations
async def get_due_parcels():

    response = await api_request(
        'GET',
        '/mail/list/'
    )

    return extract_records(response, 'parcels')

async def generate_delivery_otp(delivery_id):

    return await api_request(
        'PUT',
        f'/mail/delivery/{delivery_id}'
    )

async def verify_delivery(delivery_id, value):

    safe_id = quote(str(delivery_id), safe='')

    return await api_request(
        'PUT',
        f'/mail/verify/{safe_id}',
        json={
            'value':value
        }
    )
