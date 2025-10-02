"""
Библиотека для работы с НСПД (Национальная система пространственных данных)
Предоставляет упрощенные функции для получения данных по кадастровым номерам и геометриям.
"""

from .nspd_request import NSPD
from .version import __version__

__author__ = "Logar1t"
__email__ = "logar1t.official@gmail.com"
__description__ = "Python-библиотека для работы с НСПД"

__all__ = ["NSPD", "__version__"]