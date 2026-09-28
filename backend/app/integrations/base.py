from abc import ABC, abstractmethod


class IntegrationAdapter(ABC):
    @abstractmethod
    def test_connection(self):
        raise NotImplementedError
