def __get_last_layer():
    from os.path import dirname, basename, isfile, join
    from glob import glob

    modules = glob(join(dirname(__file__), "*.py"))
    files = [basename(f)[:-3] for f in modules if isfile(f)
             and not f.endswith('__init__.py')
             and not basename(f).startswith('_')]
    layers = []
    for i, layer in enumerate(files):
        layer = layer.split('_', 1)
        if len(layer) == 2:
            level, name = layer
            if level[0] == 'l':
                layers.append(f'{level}_{name}')
    layers.sort()
    return layers[-1]


bot, dp = None, None
exec(f'from .{__get_last_layer()} import bot, dp')
