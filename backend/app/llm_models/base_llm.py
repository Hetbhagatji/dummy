from abc import ABC,abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def parse(self,prompt:str)->str:
        pass
        
    