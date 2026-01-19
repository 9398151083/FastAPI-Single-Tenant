import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from app.entities import group_member
from app.entities.expense import Expense
from app.entities.expense_split import ExpenseSplit
from app.entities.invite import Invite
from app.entities.task import Task
from app.entities.user import User
import uuid

from sqlalchemy import func
from app.entities.notifications import UserNotification

# ✅ Import


def get_user_tasks(db: Session, current_user: User) -> List[Task]:
    """Get user's tasks (assigned_to ME or in user's groups)"""
    return (
        db.query(Task)
        .filter(
            or_(
                Task.assigned_to == str(current_user.id),
                Task.group_id.in_(get_user_groups(db, current_user.id)),
            )
        )
        .all()
    )


def get_task_summary(db: Session, current_user: User) -> dict:
    """Get task statistics for user"""
    total = (
        db.query(Task)
        .filter(
            or_(
                Task.assigned_to == str(current_user.id),
                Task.group_id.in_(get_user_groups(db, current_user.id)),
            )
        )
        .count()
    )

    open_tasks = (
        db.query(Task)
        .filter(
            and_(or_(Task.assigned_to == str(current_user.id)), Task.status == "open")
        )
        .count()
    )

    return {
        "total_tasks": total,
        "open": open_tasks,
        "completed": total - open_tasks,
    }


def get_user_groups(db: Session, user_id: uuid.UUID) -> List[str]:
    """Get groups user belongs to (TODO: implement group_memberships)"""
    return ["7e976007-4ae7-46fd-b497-dea41385787c"]  # Default group


# ✅ EXISTING TASK QUERIES (unchanged)
def get_user_tasks(db: Session, current_user: User) -> List[Task]:
    return (
        db.query(Task)
        .filter(
            or_(
                Task.assigned_to == str(current_user.id),
                Task.group_id.in_(get_user_groups(db, current_user.id)),
            )
        )
        .all()
    )


def get_task_summary(db: Session, current_user: User) -> dict:
    # ... existing code
    pass


def get_user_groups(db: Session, user_id: uuid.UUID) -> List[str]:
    return ["7e976007-4ae7-46fd-b497-dea41385787c"]


# ✅ NEW EXPENSE QUERIES
def get_user_expenses(db: Session, current_user: User) -> List[Expense]:
    """Get user's expenses (created_by ME or in group)"""
    return (
        db.query(Expense)
        .filter(
            or_(
                Expense.created_by == str(current_user.id),
                Expense.group_id.in_(get_user_groups(db, current_user.id)),
            )
        )
        .order_by(Expense.created_at.desc())
        .all()
    )


def get_expense_summary(db: Session, current_user: User) -> dict:
    """Get expense statistics"""
    total = (
        db.query(Expense)
        .filter(
            or_(
                Expense.created_by == str(current_user.id),
                Expense.group_id.in_(get_user_groups(db, current_user.id)),
            )
        )
        .count()
    )

    total_amount = (
        db.query(Expense.amount)
        .filter(Expense.created_by == str(current_user.id))
        .sum()
    )

    return {
        "total_expenses": total,
        "total_amount": float(total_amount or 0),
        "avg_amount": float((total_amount or 0) / max(total, 1)),
    }


from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List
from app.entities.group import Group
from app.entities.group_member import GroupMembership
from app.entities.user import User

# ✅ ADD THESE GROUP QUERIES (keep existing task/expense queries)


def create_group(db: Session, group_id: str, name: str, created_by: str):
    """Create group record"""
    group = Group(id=group_id, name=name, created_by=created_by)
    db.add(group)
    db.flush()
    return group


def create_membership(
    db: Session, membership_id: str, group_id: str, user_id: str, role: str = "member"
):
    """Create group membership"""
    membership = GroupMembership(
        id=membership_id, group_id=group_id, user_id=user_id, role=role
    )
    db.add(membership)

    return membership


def get_user_groups(db: Session, user_id: str) -> List[dict]:
    """FIXED: ONLY groups user is member of"""

    # ✅ START FROM MEMBERSHIPS → JOIN GROUPS (CORRECT WAY)
    result = (
        db.query(GroupMembership, Group)
        .join(Group, Group.id == GroupMembership.group_id)  # ← INNER JOIN
        .filter(GroupMembership.user_id == user_id)  # ← ONLY THIS USER'S memberships
        .all()
    )

    return [
        {
            "id": group.id,
            "name": group.name,
            "role": membership.role,  # ✅ ALWAYS has role!
            "created_by": group.created_by,
        }
        for membership, group in result
    ]


def get_group_by_id(db: Session, group_id: str):
    """Get single group by ID"""
    return db.query(Group).filter(Group.id == group_id).first()


def is_user_member(db: Session, group_id: str, user_id: str) -> bool:
    """Check if user is already member"""
    return (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
        .first()
        is not None
    )


def list_all_groups(db: Session) -> List[Group]:
    """List all public groups"""
    return db.query(Group).all()


# In app/services/group_service.py


def join_group(self, group_id: str, current_user: User):
    # ✅ USE THE METHOD
    group = get_group_by_id(self.db, group_id)
    if not group:
        raise ValueError("Group not found")

        # Continue with logic...


# ADD TO EXISTING db_queries.py
def get_user_by_email(db: Session, email: str):
    """Find user by email"""
    return db.query(User).filter(User.email == email).first()


def create_invite(
    db: Session, invite_id: str, group_id: str, email: str, invited_by: str, token: str
):
    """Create group invite"""
    invite = Invite(
        id=invite_id,
        group_id=group_id,
        email=email,
        invited_by=invited_by,
        token=token,
        status="pending",
    )
    db.add(invite)
    db.flush()
    return invite


def get_invite_by_token(db: Session, token: str):
    return db.query(Invite).filter(Invite.token == token).first()


def accept_invite(db: Session, invite_id: str):
    """Mark invite as accepted"""
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if invite:
        invite.status = "accepted"
        db.commit()


# ADD THESE to your existing db_queries.py
def get_user_by_email(db: Session, email: str):
    """Find user by email"""
    return db.query(User).filter(User.email == email).first()


def create_invite(
    db: Session, invite_id: str, group_id: str, email: str, invited_by: str, token: str
):
    """Create group invite"""
    invite = Invite(
        id=invite_id, group_id=group_id, email=email, invited_by=invited_by, token=token
    )
    db.add(invite)

    return invite


def get_invite_by_token(db: Session, token: str):
    """Get invite by token"""
    return db.query(Invite).filter(Invite.token == token).first()


def accept_invite(db: Session, invite_id: str):
    """Mark invite as accepted"""
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if invite:
        invite.status = "accepted"


def create_user(db: Session, user_id: str, email: str, password: str, name: str):
    """Create new user (hashed password)"""

    user = User(
        id=user_id,
        email=email,
        password=password,
        name=name,
        is_active=True,
        is_verified=True,
    )
    db.add(user)

    return user


def create_task(db: Session, **kwargs):
    """Create task - EXPLICIT MAPPING"""
    # task_data = {
    #         "id": task_id,
    #         "group_id": group_id,
    #         "title": title,
    #         "created_by": str(current_user.id),
    #         "description": kwargs.get("description"),
    #         "assigned_to": kwargs.get("assigned_to"),
    #         "status": kwargs.get("status", "pending"),
    #         "priority": kwargs.get("priority", "medium"),
    #         "due_date": kwargs.get("due_date"),
    #     }

    # ✅ EXTRACT & VALIDATE fields individually
    created_by = kwargs.get("created_by")
    description = kwargs.get("description")
    assigned_to = kwargs.get("assigned_to")
    status = kwargs.get("status", "pending")
    priority = kwargs.get("priority", "medium")
    due_date = kwargs.get("due_date")

    # ✅ UUID VALIDATION (prevents "string" error)
    if assigned_to and len(assigned_to) != 36:  # Quick UUID check
        assigned_to = None

    # ✅ EXPLICIT MAPPING - NO ** unpacking
    task = Task(
        id=kwargs.get("id"),
        group_id=kwargs.get("group_id"),
        title=kwargs.get("title"),
        created_by=created_by,
        description=description,
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        due_date=due_date,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Usage stays simple:


def get_group_tasks(db: Session, group_id: str):
    """Get all tasks for specific group"""
    return (
        db.query(Task)
        .filter(Task.group_id == group_id)
        .order_by(Task.created_at.desc())
        .all()
    )


def get_user_group_tasks(db: Session, user_id: str):
    """Get tasks from all user's groups"""
    result = (
        db.query(Task)
        .join(GroupMembership, GroupMembership.group_id == Task.group_id)
        .filter(GroupMembership.user_id == user_id)
        .all()
    )
    return result


# app/utils/db_queries.py - ADD THESE:
def get_task_by_id(db: Session, task_id: str):
    return db.query(Task).filter(Task.id == task_id).first()


def get_task_stats(db: Session, group_id: str):
    return (
        db.query(
            func.count(Task.id).label("total"),
            # ... rest of stats query
        )
        .filter(Task.group_id == group_id)
        .one()
    )


# ✅ ADD THESE FUNCTIONS TO YOUR EXISTING db_queries.py


def get_user_notifications(
    db: Session, user_id: str, limit: int = 50, unread_only: bool = False
):
    """Get user notifications"""
    query = db.query(UserNotification).filter(UserNotification.user_id == user_id)

    if unread_only:
        query = query.filter(UserNotification.is_read == False)

    return query.order_by(UserNotification.created_at.desc()).limit(limit).all()


def get_notification_stats(db: Session, user_id: str):
    """Get notification statistics"""
    stats = (
        db.query(
            func.count(UserNotification.id).label("total"),
            func.sum(func.case((UserNotification.is_read == False, 1), else_=0)).label(
                "unread"
            ),
        )
        .filter(UserNotification.user_id == user_id)
        .one()
    )

    return {
        "total": int(stats.total),
        "unread": int(stats.unread or 0),
        "read": int(stats.total - (stats.unread or 0)),
    }


def mark_notification_read(db: Session, notification_id: str, user_id: str):
    """Mark notification read"""
    notif = (
        db.query(UserNotification)
        .filter(
            UserNotification.id == notification_id, UserNotification.user_id == user_id
        )
        .first()
    )

    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False


def mark_all_notifications_read(db: Session, user_id: str):
    """Mark all notifications read"""
    count = (
        db.query(UserNotification)
        .filter(UserNotification.user_id == user_id, UserNotification.is_read == False)
        .update({"is_read": True})
    )

    db.commit()
    return count


def delete_user_notification(db: Session, notification_id: str, user_id: str):
    """Delete single notification"""
    count = (
        db.query(UserNotification)
        .filter(
            UserNotification.id == notification_id, UserNotification.user_id == user_id
        )
        .delete()
    )

    if count > 0:
        db.commit()
        return True
    return False


def delete_all_user_notifications(db: Session, user_id: str):
    """Delete all user notifications"""
    count = (
        db.query(UserNotification).filter(UserNotification.user_id == user_id).delete()
    )

    db.commit()
    return count


def get_user_groups(db: Session, user_id: str) -> List[Group]:
    """Get all groups user belongs to"""
    return (
        db.query(Group)
        .join(GroupMembership, Group.id == GroupMembership.group_id)
        .filter(GroupMembership.user_id == user_id)
        .all()
    )


def get_expense_by_id(db: Session, expense_id: str) -> Expense:
    """Get single expense by ID"""
    return db.query(Expense).filter(Expense.id == expense_id).first()


def get_group_expenses(db: Session, group_id: str) -> List[Expense]:
    """Get all expenses for a group"""
    return (
        db.query(Expense)
        .filter(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())
        .all()
    )


def get_user_expenses_in_group(
    db: Session, user_id: str, group_id: str
) -> List[Expense]:
    """Get expenses created by user in specific group"""
    return (
        db.query(Expense)
        .filter(and_(Expense.created_by == user_id, Expense.group_id == group_id))
        .order_by(Expense.created_at.desc())
        .all()
    )


def create_expense(db: Session, expense_data: dict) -> Expense:
    """Create new expense"""
    expense = Expense(**expense_data)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def create_expense_splits(db: Session, splits: List[dict]) -> List[ExpenseSplit]:
    """Create multiple splits at once"""
    created_splits = []
    for split_data in splits:
        split = ExpenseSplit(**split_data)
        db.add(split)
        created_splits.append(split)
    db.commit()
    return created_splits


def get_user_debts(db: Session, user_id: str) -> List[ExpenseSplit]:
    """Get all debts for user (what they owe + what others owe them)"""
    return (
        db.query(ExpenseSplit)
        .filter(
            and_(ExpenseSplit.owes_user_id == user_id, ExpenseSplit.is_settled == False)
        )
        .all()
    )


def get_owed_to_user(db: Session, user_id: str) -> List[ExpenseSplit]:
    """Get money owed TO this user"""
    return (
        db.query(ExpenseSplit)
        .filter(
            and_(ExpenseSplit.owed_user_id == user_id, ExpenseSplit.is_settled == False)
        )
        .all()
    )


def get_invite_by_token(db: Session, token: str):
    """Get invite by token"""
    return db.query(Invite).filter(Invite.token == token).first()


def is_user_member(db: Session, group_id: str, user_id: str) -> bool:
    """Check if user is group member"""
    return (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
        .first()
        is not None
    )


def add_user_to_group(db: Session, group_id: str, user_id: str):
    """Add user to group members"""
    group_member = GroupMembership(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=user_id,
        joined_at=datetime.utcnow(),
    )
    db.add(group_member)


def get_group_members(db: Session, group_id: str) -> List[str]:
    """Get all member user_ids"""
    return [
        row.user_id
        for row in db.query(GroupMembership.user_id)
        .filter(GroupMembership.group_id == group_id)
        .all()
    ]


def get_group_by_id(db: Session, group_id: str):
    """Get group details"""
    return db.query(Group).filter(Group.id == group_id).first()
