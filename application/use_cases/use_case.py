class UseCase:
    @property
    def tag(self) -> str:
        return self.__class__.__name__