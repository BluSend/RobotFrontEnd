import json
from urllib.parse import quote

import httpx
from staff_portal.config import API_BASE_URL


class APIError(Exception):
    pass


# API requests
async def api_request(method: str, endpoint: str, **kwargs):
    if not API_BASE_URL:
        raise APIError('The backend address has not been set.')
    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        details = error.response.text[:250]
        raise APIError(f'HTTP {error.response.status_code}: {details}') from error
    except httpx.RequestError as error:
        raise APIError(f'Could not connect to the backend: {error}') from error
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
            pass

    return result


def records_from(response, kind: str):
    if isinstance(response, list) and all(isinstance(item, dict) for item in response):
        return response
    if isinstance(response, dict):
        for key in (kind, 'data', 'items', 'results'):
            items = response.get(key)
            if isinstance(items, list) and all(isinstance(item, dict) for item in items):
                return items
    raise APIError(
        f'Unexpected response while loading {kind}.'
    )


# User endpoints
async def get_users():
    return records_from(await api_request('GET', '/admin/users/all'), 'users')


async def get_user(user_id: int):
    return await api_request('GET', f'/admin/users/{user_id}')


async def add_user(name: str, room_number: str, email: str):
    return await api_request('POST', '/admin/users/add', json={
        'name': name, 'roomNumber': room_number, 'email': email,
    })


async def update_user(user_id: int, name: str, room_number: str, email: str):
    return await api_request('PUT', '/admin/users/modify', json={
        'userID': user_id,
        'name': name, 'roomNumber': room_number, 'email': email,
    })


async def remove_user(user_id: int):
    return await api_request('DELETE', f'/admin/users/remove/{user_id}')


# Parcel endpoints
async def get_parcels():
    return records_from(await api_request('GET', '/admin/parcels/all'), 'parcels')


async def add_parcel(backend_id: int):
    return await api_request('POST', '/admin/parcels/add', json={'id': backend_id})


async def update_parcel(user_id: int, status: str, tracking_id: int, n_delivery: int):
    return await api_request('PUT', '/admin/parcels/modify', json={
        'userID': user_id, 'status': status,
        'tracking_id': tracking_id, 'nDelivery': n_delivery,
    })


async def remove_parcel(backend_id: int):
    return await api_request('DELETE', '/admin/parcels/remove', json={'id': backend_id})


# Delivery endpoints
async def get_due_parcels():
    return records_from(await api_request('GET', '/mail/list/'), 'parcels')


async def generate_delivery_otp(tracking_id: str):
    safe_id = quote(str(tracking_id), safe='')
    return await api_request('PUT', f'/mail/delivery/{safe_id}')


async def verify_delivery(tracking_id: str, value: str):
    safe_id = quote(str(tracking_id), safe='')
    return await api_request('PUT', f'/mail/verify/{safe_id}', json={'value': value})
