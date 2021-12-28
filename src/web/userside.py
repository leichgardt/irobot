from src.utils import config, post_request


class USPipe:
    def __init__(self):
        self.url = 'https://{}/api.php'.format(config['paladin']['userside'])
        self.__key = config['paladin']['userside-token']

    def __new__(cls, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(USPipe, cls).__new__(cls, **kwargs)
        return cls.instance

    async def _api(self, category, action, **kwargs):
        payload = {'cat': category, 'action': action, 'key': self.__key, **kwargs}
        return await post_request(self.url, data=payload)

    async def get_feedback_task(self, task_id):
        output = {}
        task_list = await self._api('task', 'get_related_task_id', id=task_id)
        task_list = task_list.get('Data', '')
        if isinstance(task_list, int):
            if task_list == -1:
                return output
            task_list = [str(task_list)]
        elif isinstance(task_list, str):
            task_list = task_list.split(',')
        else:
            return output
        task_list.sort()
        task_list.reverse()
        for task_id in task_list:
            data = await self._api('task', 'show', id=task_id)
            data = data.get('Data', {})
            if data.get('type', {}).get('id', -1) == 58:  # 58 - ID задания типа "Обзон: Контроль качества"
                output = data
                break
        return output
