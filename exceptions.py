

class TimeConvertError(Exception):

    """
    Ошибка конвекции времени
    """

    pass


class TimeError(Exception):

    """
    Ошибка с Time
    """
    
    pass


class TimeFormatError(Exception):

    """
    Ошибка формата времени
    """
    
    pass


class ChannelNotFound(Exception):

    """
    Канал не найден
    """

    pass


class EpgError(Exception):

    """
    Ошибка в работе EPG
    """

    pass


class ChannelAlreadyExists(Exception):

    """
    Канал уже создан
    """

    pass


class ProgrammeNotFound(Exception):

    """
    
    """
    
    pass