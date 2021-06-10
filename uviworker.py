from uvicorn.workers import UvicornWorker


class IrobotUviWorker(UvicornWorker):
    CONFIG_KWARGS = {
        'loop': 'uvloop',
        'http': 'auto',
        'ws': 'websockets',
    }
