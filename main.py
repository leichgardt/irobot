from uvicorn.workers import UvicornWorker


class IrobotWebUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        'host': '0.0.0.0',
        'port': 8000,
        'loop': 'uvloop',
        'http': 'auto',
        'ws': 'websockets',
        # 'ws_max_size': 32768,
        'limit_max_requests': 1000,
        'timeout_keep_alive': 5,
    }
