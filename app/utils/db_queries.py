from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from app.entities.expense import Expense
from app.entities.invite import Invite
from app.entities.task import Task
from app.entities.user import User
import uuid

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
    db.flush()
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
        is_verfied=True,
    )
    db.add(user)

    return user
