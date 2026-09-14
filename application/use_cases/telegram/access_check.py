from domain.services.check_manager import CheckManager


class AccessCheck:
    def __init__(self, manager_user_id: int):
        self.manager = manager_user_id
    
    async def execute(self, target_id: int) -> None:
        CheckManager.is_manager(manager_id=self.manager, target_id=target_id)
