"""Database Seeder for BookEase."""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from src.config import DEFAULT_SETTINGS, ROLE_ADMIN, ROLE_OWNER, ROLE_STAFF
from src.core.security import hash_password
from src.database.models import (
    User,
    Staff,
    Service,
    StaffSchedule,
    StaffLeave,
    Customer,
    Appointment,
    BusinessSetting,
    AuditLog,
)


def seed_initial_data(session: Session):
    """Seed initial settings, users, services, staff, and demo appointments."""
    # Check if settings already seeded
    existing_setting = session.query(BusinessSetting).first()
    if existing_setting:
        return  # Database already seeded

    # 1. Seed Business Settings
    for key, value in DEFAULT_SETTINGS.items():
        session.add(BusinessSetting(key=key, value=value))

    # 2. Seed Default Users
    admin_user = User(
        username="admin",
        email="admin@bookease.local",
        password_hash=hash_password("admin123"),
        full_name="System Administrator",
        role=ROLE_ADMIN,
        is_active=True,
    )
    owner_user = User(
        username="eleanor",
        email="eleanor@lumierewellness.com",
        password_hash=hash_password("owner123"),
        full_name="Eleanor Vance",
        role=ROLE_OWNER,
        is_active=True,
    )
    staff_user = User(
        username="marcus",
        email="marcus@lumierewellness.com",
        password_hash=hash_password("staff123"),
        full_name="Dr. Marcus Reed",
        role=ROLE_STAFF,
        is_active=True,
    )

    session.add_all([admin_user, owner_user, staff_user])
    session.flush()

    # 3. Seed Staff Members
    staff1 = Staff(
        user_id=owner_user.id,
        name="Eleanor Vance",
        email="eleanor@lumierewellness.com",
        phone="+1 (555) 328-9401",
        role_title="Master Aesthetician & Director",
        color_code="#8B5CF6",  # Purple
        bio="Licensed medical aesthetician with 12 years of clinical rejuvenation experience.",
        is_active=True,
    )
    staff2 = Staff(
        user_id=staff_user.id,
        name="Dr. Marcus Reed",
        email="marcus@lumierewellness.com",
        phone="+1 (555) 328-9402",
        role_title="Senior Dermatologist",
        color_code="#3B82F6",  # Blue
        bio="Board-certified dermatologist specializing in skin health and diagnostic consults.",
        is_active=True,
    )
    staff3 = Staff(
        name="Sophie Dubois",
        email="sophie@lumierewellness.com",
        phone="+1 (555) 328-9403",
        role_title="Holistic Massage Therapist",
        color_code="#10B981",  # Emerald
        bio="Certified deep tissue, hot stone, and aromatherapy wellness specialist.",
        is_active=True,
    )
    staff4 = Staff(
        name="Liam Chen",
        email="liam@lumierewellness.com",
        phone="+1 (555) 328-9404",
        role_title="Hair & Scalp Specialist",
        color_code="#F59E0B",  # Amber
        bio="Expert in advanced scalp micro-treatments, precision cuts, and keratin restoration.",
        is_active=True,
    )

    session.add_all([staff1, staff2, staff3, staff4])
    session.flush()

    # 4. Seed Working Schedules for Staff (Mon-Sat)
    for staff_member in [staff1, staff2, staff3, staff4]:
        for day in range(7):
            if day < 5:  # Monday to Friday
                sched = StaffSchedule(
                    staff_id=staff_member.id,
                    day_of_week=day,
                    is_working=True,
                    start_time="09:00",
                    end_time="18:00",
                    break_start="13:00",
                    break_end="14:00",
                )
            elif day == 5:  # Saturday
                sched = StaffSchedule(
                    staff_id=staff_member.id,
                    day_of_week=day,
                    is_working=True,
                    start_time="10:00",
                    end_time="16:00",
                    break_start="13:00",
                    break_end="13:30",
                )
            else:  # Sunday
                sched = StaffSchedule(
                    staff_id=staff_member.id,
                    day_of_week=day,
                    is_working=False,
                    start_time="09:00",
                    end_time="18:00",
                    break_start="13:00",
                    break_end="14:00",
                )
            session.add(sched)

    # 5. Seed Services
    srv1 = Service(
        name="Hydra-Luxe Facial Therapy",
        category="Skin Aesthetics",
        description="Deep pore exfoliation, intensive hyaluronic infusion, and peptide LED therapy.",
        duration_minutes=60,
        buffer_minutes=15,
        price=135.0,
    )
    srv2 = Service(
        name="Clinical Skin Consultation",
        category="Dermatology",
        description="Comprehensive diagnostic skin scan, dermoscopy, and personalized treatment roadmap.",
        duration_minutes=30,
        buffer_minutes=15,
        price=95.0,
    )
    srv3 = Service(
        name="Deep Tissue Restoration Massage",
        category="Body & Wellness",
        description="Targeted muscular trigger point relief, warm botanical compresses, and tension release.",
        duration_minutes=75,
        buffer_minutes=15,
        price=120.0,
    )
    srv4 = Service(
        name="Aromatherapy Full Body Ritual",
        category="Body & Wellness",
        description="Sensory organic essential oil massage, lymphatic drainage, and scalp relaxation.",
        duration_minutes=90,
        buffer_minutes=15,
        price=150.0,
    )
    srv5 = Service(
        name="Keratin Precision Scalp Treatment",
        category="Hair & Scalp",
        description="High-potency botanical keratin bonding and micro-steam hair fiber rejuvenation.",
        duration_minutes=60,
        buffer_minutes=15,
        price=110.0,
    )
    srv6 = Service(
        name="Microneedling Collagen Induction",
        category="Skin Aesthetics",
        description="Advanced automated micro-channeling with pharmaceutical-grade growth serum.",
        duration_minutes=75,
        buffer_minutes=15,
        price=210.0,
    )

    session.add_all([srv1, srv2, srv3, srv4, srv5, srv6])
    session.flush()

    # Link Services to Staff
    staff1.services.extend([srv1, srv6])
    staff2.services.extend([srv2, srv6])
    staff3.services.extend([srv3, srv4])
    staff4.services.extend([srv5])
    session.flush()

    # 6. Seed Customers
    cust1 = Customer(
        name="Sophia Martinez",
        email="sophia.m@example.com",
        phone="+1 (555) 214-5511",
        notes="Allergic to synthetic fragrance oils. Prefers lavender or chamomile.",
        total_bookings=4,
    )
    cust2 = Customer(
        name="Alexander Wright",
        email="alex.wright@example.com",
        phone="+1 (555) 388-7722",
        notes="Executive client. Prefers afternoon appointments.",
        total_bookings=2,
    )
    cust3 = Customer(
        name="Chloe Bennett",
        email="chloe.b@example.com",
        phone="+1 (555) 902-3344",
        notes="Interested in long-term aesthetic skincare plans.",
        total_bookings=3,
    )
    cust4 = Customer(
        name="David Kim",
        email="david.kim@example.com",
        phone="+1 (555) 674-1290",
        notes="Regular customer for scalp care.",
        total_bookings=1,
    )
    cust5 = Customer(
        name="Emma Watson",
        email="emma.watson@example.com",
        phone="+1 (555) 831-4455",
        notes="Referred by Dr. Reed.",
        total_bookings=2,
    )

    session.add_all([cust1, cust2, cust3, cust4, cust5])
    session.flush()

    # 7. Seed Sample Appointments around today
    today = date.today()
    dates = [
        today - timedelta(days=2),
        today - timedelta(days=1),
        today,
        today + timedelta(days=1),
        today + timedelta(days=2),
        today + timedelta(days=3),
    ]

    sample_bookings = [
        # Past appointments
        {
            "num": "BK-DEMO-001",
            "cust": cust1,
            "staff": staff1,
            "srv": srv1,
            "date": dates[0].isoformat(),
            "start": "10:00",
            "end": "11:00",
            "status": "completed",
            "price": 135.0,
            "notes": "Client was very pleased with the treatment result.",
        },
        {
            "num": "BK-DEMO-002",
            "cust": cust2,
            "staff": staff2,
            "srv": srv2,
            "date": dates[1].isoformat(),
            "start": "14:00",
            "end": "14:30",
            "status": "completed",
            "price": 95.0,
            "notes": "Follow-up recommended in 6 weeks.",
        },
        # Today's appointments
        {
            "num": "BK-DEMO-003",
            "cust": cust3,
            "staff": staff1,
            "srv": srv6,
            "date": dates[2].isoformat(),
            "start": "10:30",
            "end": "11:45",
            "status": "confirmed",
            "price": 210.0,
            "notes": "Pre-treatment numbing applied.",
        },
        {
            "num": "BK-DEMO-004",
            "cust": cust4,
            "staff": staff4,
            "srv": srv5,
            "date": dates[2].isoformat(),
            "start": "14:00",
            "end": "15:00",
            "status": "confirmed",
            "price": 110.0,
            "notes": "Scalp treatment session 2 of 4.",
        },
        {
            "num": "BK-DEMO-005",
            "cust": cust5,
            "staff": staff3,
            "srv": srv3,
            "date": dates[2].isoformat(),
            "start": "15:30",
            "end": "16:45",
            "status": "confirmed",
            "price": 120.0,
            "notes": "Requested focus on upper shoulders.",
        },
        # Upcoming appointments
        {
            "num": "BK-DEMO-006",
            "cust": cust1,
            "staff": staff3,
            "srv": srv4,
            "date": dates[3].isoformat(),
            "start": "11:00",
            "end": "12:30",
            "status": "confirmed",
            "price": 150.0,
            "notes": "Birthday gift voucher applied.",
        },
        {
            "num": "BK-DEMO-007",
            "cust": cust2,
            "staff": staff1,
            "srv": srv1,
            "date": dates[4].isoformat(),
            "start": "15:00",
            "end": "16:00",
            "status": "confirmed",
            "price": 135.0,
            "notes": "Regular maintenance session.",
        },
    ]

    for b in sample_bookings:
        app = Appointment(
            appointment_number=b["num"],
            customer_id=b["cust"].id,
            staff_id=b["staff"].id,
            service_id=b["srv"].id,
            date=b["date"],
            start_time=b["start"],
            end_time=b["end"],
            status=b["status"],
            price=b["price"],
            notes=b["notes"],
            created_by_user_id=admin_user.id,
        )
        session.add(app)

    # 8. Seed Initial Audit Log
    session.add(
        AuditLog(
            user_id=admin_user.id,
            user_name=admin_user.full_name,
            action="INITIALIZE_DATABASE",
            entity_type="SYSTEM",
            entity_id="0",
            details="Initialized BookEase database with business configuration, staff, and services.",
        )
    )
    session.flush()
