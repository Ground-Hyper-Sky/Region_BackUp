from mcdreforged.api.utils.serializer import Serializable


class rb_info(Serializable):
    time: str = ""
    backup_dimension: str = ""
    user_dimension: str = ""
    user: str = ""
    user_pos: float = ""
    command: str = ""
    comment: str = ""

