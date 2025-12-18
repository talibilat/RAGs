import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, init_db
from app.db.models import TeamMember, Project, Task
from datetime import datetime, timedelta

async def seed_data():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Check if data exists
        result = await session.execute(select(TeamMember))
        if result.scalars().first():
            print("Data already seeded.")
            return

        # Users
        admin = TeamMember(name="Alice Admin", email="alice@example.com", role="admin")
        pm = TeamMember(name="Bob PM", email="bob@example.com", role="pm")
        dev = TeamMember(name="Charlie Dev", email="charlie@example.com", role="member")
        session.add_all([admin, pm, dev])
        await session.flush()

        # Projects
        p1 = Project(name="Website Redesign", status="active", owner_id=pm.id, description="Revamp the corporate website.")
        p2 = Project(name="Mobile App", status="planning", owner_id=pm.id, description="iOS and Android app.")
        session.add_all([p1, p2])
        await session.flush()

        # Tasks
        t1 = Task(project_id=p1.id, title="Design Home Page", status="done", assignee_id=dev.id, due_date=datetime.utcnow() - timedelta(days=1))
        t2 = Task(project_id=p1.id, title="Implement Backend API", status="in_progress", assignee_id=dev.id, due_date=datetime.utcnow() + timedelta(days=5))
        t3 = Task(project_id=p2.id, title="Requirements Gathering", status="todo", assignee_id=pm.id, due_date=datetime.utcnow() + timedelta(days=2))
        session.add_all([t1, t2, t3])

        await session.commit()
        print("Seeded data successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
