from domain.exceptions.errors import NotManagerError

class CheckManager:
    @staticmethod
    def is_manager(manager_id: int, target_id: int) -> None:
        if manager_id == target_id:
            return
        raise NotManagerError