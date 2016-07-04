from ruamel import yaml
from ruamel.yaml.representer import SafeRepresenter

from formats.bms import BmsEvent, BmsTrack, BmsFile, BmsSeekMode
from util import without, no_underscore
from utils.classes import CC


def represents(cls):
    def _represents(func):
        yaml.add_representer(cls, func)
        return func
    return _represents

@represents(BmsEvent)
def event_pres(dumper: SafeRepresenter, data):

    data = dict(data)
    for k in ['addr', 'next']:
        if k in data:
            data[k] = hex(data[k])

    tag = data['type']
    # print(tag)
    # print(without(data, 'type'))

    rep = dumper.represent_mapping(
        tag,
        without(data, 'type')
    )

    # print(type(rep))
    return rep


@represents(BmsTrack)
def track_pres(dumper: SafeRepresenter, data: BmsTrack):
    data = no_underscore(data)

    k = 'addr'
    if k in data:
        data[k] = hex(data[k])

    return dumper.represent_dict(data)

@represents(BmsFile)
def file_pres(dumper: SafeRepresenter, data: BmsFile):
    data = no_underscore(data)

    k = 'at'
    if k in data:
        v = data[k]
        data[k] = {'$%04X'%addr: event for addr,event in v.items()}

    return dumper.represent_dict(data)


@represents(CC)
@represents(BmsSeekMode)
def track_pres(dumper: SafeRepresenter, data):
    return dumper.represent_str(str(data))


yaml.Dumper.ignore_aliases = lambda self, data: True

def get_tree(tree: dict) -> str:
    return yaml.dump(tree, indent=2)



# from utils.fluid import SeqSynth
