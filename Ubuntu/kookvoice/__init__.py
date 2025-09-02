try:
    from .kookvoice import Player, Status, set_ffmpeg, configure_logging, play_list
except ImportError:
    from kookvoice import Player, Status, set_ffmpeg, configure_logging, play_list

__all__ = ['Player', 'Status', 'set_ffmpeg', 'configure_logging', 'play_list']