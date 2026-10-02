from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        actor_id: int | None,
        action: str,
        entity: str | None = None,
        entity_id: object = None,
        before: Any = None,
        after: Any = None,
        source: str = "bot",
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                entity=entity,
                entity_id=str(entity_id) if entity_id is not None else None,
                before=before,
                after=after,
                source=source,
            )
        )
