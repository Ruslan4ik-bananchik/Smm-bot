from abc import ABC, abstractmethod

class LoggerPort(ABC):
    @abstractmethod
    def info(self, msg: str): ...
    
    @abstractmethod
    def warning(self, msg: str): ...
    
    @abstractmethod
    def error(self, msg: str): ...
    
    @abstractmethod
    def exception(self, msg: str): ...
