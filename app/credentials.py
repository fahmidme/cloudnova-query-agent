"""OS-protected credentials; no plaintext fallback, dependencies, or secret argv."""

import ctypes as ct
import json
import shutil
import subprocess
import sys

SERVICE = 'cloudnova-query-agent.v1'


class CredentialStoreError(ValueError):
    pass


def _macos(operation: str, provider: str, payload: bytes | None):
    security = ct.CDLL('/System/Library/Frameworks/Security.framework/Security')
    core = ct.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    ptr, u32 = ct.c_void_p, ct.c_uint32
    signatures = {
        'SecKeychainFindGenericPassword': [ptr, u32, ct.c_char_p, u32, ct.c_char_p, ct.POINTER(u32), ct.POINTER(ptr), ct.POINTER(ptr)],
        'SecKeychainAddGenericPassword': [ptr, u32, ct.c_char_p, u32, ct.c_char_p, u32, ptr, ct.POINTER(ptr)],
        'SecKeychainItemModifyAttributesAndData': [ptr, ptr, u32, ptr],
        'SecKeychainItemDelete': [ptr], 'SecKeychainItemFreeContent': [ptr, ptr],
    }
    for name, args in signatures.items():
        function = getattr(security, name)
        function.argtypes, function.restype = args, ct.c_int32
    core.CFRelease.argtypes, core.CFRelease.restype = [ptr], None
    service, account = SERVICE.encode(), provider.encode()
    size, data, item = u32(), ptr(), ptr()
    status = security.SecKeychainFindGenericPassword(None, len(service), service, len(account), account,
                                                   ct.byref(size), ct.byref(data), ct.byref(item))
    try:
        if status not in (0, -25300):  # errSecItemNotFound
            raise CredentialStoreError(f'macOS Keychain unavailable (status {status})')
        if operation == 'get':
            return ct.string_at(data, size.value) if status == 0 else None
        if operation == 'delete':
            status = security.SecKeychainItemDelete(item) if item else 0
        else:
            buffer = ct.create_string_buffer(payload)
            if item:
                status = security.SecKeychainItemModifyAttributesAndData(item, None, len(payload), buffer)
            else:
                status = security.SecKeychainAddGenericPassword(None, len(service), service, len(account), account,
                                                              len(payload), buffer, ct.byref(item))
        if status:
            raise CredentialStoreError(f'macOS Keychain operation failed (status {status})')
    finally:
        if data:
            security.SecKeychainItemFreeContent(None, data)
        if item:
            core.CFRelease(item)


def _windows(operation: str, provider: str, payload: bytes | None):
    from ctypes import wintypes as wt

    class Credential(ct.Structure):
        _fields_ = [('Flags', wt.DWORD), ('Type', wt.DWORD), ('TargetName', wt.LPWSTR),
                    ('Comment', wt.LPWSTR), ('LastWritten', wt.FILETIME), ('CredentialBlobSize', wt.DWORD),
                    ('CredentialBlob', ct.POINTER(ct.c_ubyte)), ('Persist', wt.DWORD),
                    ('AttributeCount', wt.DWORD), ('Attributes', ct.c_void_p),
                    ('TargetAlias', wt.LPWSTR), ('UserName', wt.LPWSTR)]

    api = ct.WinDLL('Advapi32.dll', use_last_error=True)
    pointer = ct.POINTER(Credential)
    api.CredReadW.argtypes, api.CredReadW.restype = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ct.POINTER(pointer)], wt.BOOL
    api.CredWriteW.argtypes, api.CredWriteW.restype = [pointer, wt.DWORD], wt.BOOL
    api.CredDeleteW.argtypes, api.CredDeleteW.restype = [wt.LPCWSTR, wt.DWORD, wt.DWORD], wt.BOOL
    api.CredFree.argtypes, api.CredFree.restype = [ct.c_void_p], None
    target = f'{SERVICE}/{provider}'
    if operation == 'get':
        result = pointer()
        if not api.CredReadW(target, 1, 0, ct.byref(result)):
            if ct.get_last_error() == 1168:
                return None
            raise CredentialStoreError('Windows Credential Manager could not read this entry')
        try:
            return ct.string_at(result.contents.CredentialBlob, result.contents.CredentialBlobSize)
        finally:
            api.CredFree(result)
    if operation == 'delete':
        ok = api.CredDeleteW(target, 1, 0)
        if not ok and ct.get_last_error() == 1168:
            return
    else:
        buffer = (ct.c_ubyte * len(payload)).from_buffer_copy(payload)
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(payload),
                                CredentialBlob=buffer, Persist=2, UserName=provider)
        ok = api.CredWriteW(ct.byref(credential), 0)
    if not ok:
        raise CredentialStoreError('Windows Credential Manager could not change this entry')


def _linux(operation: str, provider: str, payload: bytes | None):
    executable = shutil.which('secret-tool')
    if not executable:
        raise CredentialStoreError('Linux persistence needs secret-tool and an unlocked Secret Service')
    verb = {'get': 'lookup', 'set': 'store', 'delete': 'clear'}[operation]
    command = [executable, verb]
    if operation == 'set':
        command += ['--label=CloudNova Query Agent']
    command += ['service', SERVICE, 'provider', provider]
    result = subprocess.run(command, input=payload, capture_output=True, timeout=10, check=False)
    if result.returncode:
        if operation == 'get' and result.returncode == 1 and not result.stderr:
            return None
        raise CredentialStoreError('Linux Secret Service is unavailable or declined the operation')
    return result.stdout.rstrip(b'\n') if operation == 'get' else None


def _operate(operation: str, provider: str, payload: bytes | None = None):
    if provider not in {'openai', 'anthropic'}:
        raise CredentialStoreError('Unknown credential provider')
    if payload is not None and len(payload) > 2500:
        raise CredentialStoreError('Credential is too large for the OS store')
    try:
        backend = _macos if sys.platform == 'darwin' else _windows if sys.platform == 'win32' else _linux
        return backend(operation, provider, payload)
    except (OSError, subprocess.SubprocessError) as exc:
        # Never return subprocess output or arguments in credential errors.
        raise CredentialStoreError('OS credential store unavailable; nothing was saved to disk') from None


def load_saved(provider: str) -> dict | None:
    value = _operate('get', provider)
    if value is None:
        return None
    try:
        record = json.loads(value)
        if not isinstance(record, dict) or set(record) != {'api_key', 'model'} or any(
                not isinstance(record[key], str) or not record[key].strip() for key in record):
            raise ValueError()
        return record
    except (ValueError, UnicodeDecodeError):
        raise CredentialStoreError('Saved credential is malformed; replace it with /key') from None


def save_credentials(provider: str, api_key: str, model: str):
    _operate('set', provider, json.dumps({'api_key': api_key, 'model': model}).encode())


def forget_credentials(provider: str):
    _operate('delete', provider)
