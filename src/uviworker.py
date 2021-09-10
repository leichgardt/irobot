from uvicorn.workers import UvicornWorker


class CustomUviWorker(UvicornWorker):
    CONFIG_KWARGS = {
        'loop': 'uvloop',
        'http': 'auto',
        'ws': 'websockets',
    }
