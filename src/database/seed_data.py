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
        role_title="Master Aesthetician & Medical Director",
        specialties="Hydra-Luxe Rejuvenation, Peptide LED Therapy, Anti-Aging Facials",
        color_code="#0DA58E",  # Vivid Teal
        bio="Licensed medical aesthetician with 12+ years of clinical facial rejuvenation experience.",
        is_active=True,
    )
    staff2 = Staff(
        user_id=staff_user.id,
        name="Dr. Marcus Reed",
        email="marcus@lumierewellness.com",
        phone="+1 (555) 328-9402",
        role_title="Senior Board-Certified Dermatologist",
        specialties="Clinical Dermatology, Dermoscopy, Acne Scars, Diagnostic Consults",
        color_code="#0284C7",  # Sky Blue
        bio="Board-certified dermatologist specializing in holistic skin health and diagnostic consults.",
        is_active=True,
    )
    staff3 = Staff(
        name="Sophie Dubois",
        email="sophie@lumierewellness.com",
        phone="+1 (555) 328-9403",
        role_title="Holistic Massage & Body Therapy Director",
        specialties="Deep Tissue Restoration, Hot Stone Therapy, Lymphatic Drainage",
        color_code="#10B981",  # Emerald
        bio="Certified deep tissue, hot stone, and aromatherapy wellness specialist.",
        is_active=True,
    )
    staff4 = Staff(
        name="Liam Chen",
        email="liam@lumierewellness.com",
        phone="+1 (555) 328-9404",
        role_title="Lead Trichologist & Hair Restoration Specialist",
        specialties="Keratin Bonding, Scalp Micro-Channeling, Follicle Health & Growth",
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

    # 5b. Seed duration/price options for selected services
    from src.database.models import ServiceOption
    service_options = [
        # Deep Tissue Restoration Massage — 30 / 45 / 60 / 75 min
        (srv3, "30 min", 30, 60.0, 0),
        (srv3, "45 min", 45, 85.0, 1),
        (srv3, "60 min", 60, 110.0, 2),
        (srv3, "75 min", 75, 120.0, 3),
        # Hydra-Luxe Facial Therapy — 45 / 60 / 90 min
        (srv1, "45 min", 45, 105.0, 0),
        (srv1, "60 min", 60, 135.0, 1),
        (srv1, "90 min", 90, 180.0, 2),
        # Aromatherapy Full Body Ritual — 60 / 90 min
        (srv4, "60 min", 60, 110.0, 0),
        (srv4, "90 min", 90, 150.0, 1),
    ]
    for svc, label, dur, price, order in service_options:
        session.add(ServiceOption(
            service_id=svc.id, label=label, duration_minutes=dur,
            price=price, sort_order=order, is_active=True,
        ))
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


def sync_and_seed_staff(session: Session):
    """Seed or update staff members with designations and specialties idempotently.

    If staff members already exist, they are not duplicated; their specialties
    and designations are updated if missing.
    """
    # 1. Ensure complementary services exist
    existing_services = {srv.name.lower(): srv for srv in session.query(Service).all()}

    new_services_def = [
        {
            "name": "Botox & Facial Contouring Consult",
            "category": "Aesthetic Injectables",
            "description": "High-precision assessment, facial muscle mapping, and youth-restoring micro-toxin treatment roadmap.",
            "duration_minutes": 45,
            "buffer_minutes": 15,
            "price": 180.0,
        },
        {
            "name": "Laser Glow Rejuvenation Peel",
            "category": "Laser Therapeutics",
            "description": "Non-ablative dermal photo-rejuvenation, pigment clearance, and intense collagen stimulation.",
            "duration_minutes": 60,
            "buffer_minutes": 15,
            "price": 220.0,
        },
        {
            "name": "Targeted Kinetic Sports Recovery",
            "category": "Body & Wellness",
            "description": "Myofascial tension unraveling, kinetic posture release, and athletic recovery stretch therapy.",
            "duration_minutes": 60,
            "buffer_minutes": 15,
            "price": 130.0,
        },
    ]

    for srv_data in new_services_def:
        if srv_data["name"].lower() not in existing_services:
            srv_obj = Service(
                name=srv_data["name"],
                category=srv_data["category"],
                description=srv_data["description"],
                duration_minutes=srv_data["duration_minutes"],
                buffer_minutes=srv_data["buffer_minutes"],
                price=srv_data["price"],
                is_active=True,
            )
            session.add(srv_obj)
            session.flush()
            existing_services[srv_data["name"].lower()] = srv_obj

    # 2. Comprehensive Staff Profiles (Designation + Specialties)
    staff_profiles = [
        {
            "name": "Eleanor Vance",
            "email": "eleanor@lumierewellness.com",
            "phone": "+1 (555) 328-9401",
            "role_title": "Master Aesthetician & Medical Director",
            "specialties": "Hydra-Luxe Rejuvenation, Peptide LED Therapy, Anti-Aging Facials",
            "color_code": "#0DA58E",
            "bio": "Licensed medical aesthetician with 12+ years of clinical facial rejuvenation experience.",
            "service_names": ["Hydra-Luxe Facial Therapy", "Microneedling Collagen Induction"],
        },
        {
            "name": "Dr. Marcus Reed",
            "email": "marcus@lumierewellness.com",
            "phone": "+1 (555) 328-9402",
            "role_title": "Senior Board-Certified Dermatologist",
            "specialties": "Clinical Dermatology, Dermoscopy, Acne Scars, Diagnostic Consults",
            "color_code": "#0284C7",
            "bio": "Board-certified dermatologist specializing in holistic skin health and diagnostic consults.",
            "service_names": ["Clinical Skin Consultation", "Microneedling Collagen Induction"],
        },
        {
            "name": "Sophie Dubois",
            "email": "sophie@lumierewellness.com",
            "phone": "+1 (555) 328-9403",
            "role_title": "Holistic Massage & Body Therapy Director",
            "specialties": "Deep Tissue Restoration, Hot Stone Therapy, Lymphatic Drainage",
            "color_code": "#10B981",
            "bio": "Certified deep tissue, hot stone, and aromatherapy wellness specialist.",
            "service_names": ["Deep Tissue Restoration Massage", "Aromatherapy Full Body Ritual"],
        },
        {
            "name": "Liam Chen",
            "email": "liam@lumierewellness.com",
            "phone": "+1 (555) 328-9404",
            "role_title": "Lead Trichologist & Hair Restoration Specialist",
            "specialties": "Keratin Bonding, Scalp Micro-Channeling, Follicle Health & Growth",
            "color_code": "#F59E0B",
            "bio": "Expert in advanced scalp micro-treatments, precision cuts, and keratin restoration.",
            "service_names": ["Keratin Precision Scalp Treatment"],
        },
        {
            "name": "Dr. Alexander Hayes",
            "email": "alexander.hayes@lumierewellness.com",
            "phone": "+1 (555) 328-9405",
            "role_title": "Consultant Cosmetic Surgeon & Injectables Lead",
            "specialties": "Botox & Dermal Fillers, Collagen Induction Therapy, Facial Contouring",
            "color_code": "#8B5CF6",
            "bio": "Pioneering cosmetic specialist focused on natural facial contours and non-surgical youth restoration.",
            "service_names": ["Botox & Facial Contouring Consult", "Clinical Skin Consultation", "Microneedling Collagen Induction"],
        },
        {
            "name": "Maya Patel",
            "email": "maya.patel@lumierewellness.com",
            "phone": "+1 (555) 328-9406",
            "role_title": "Senior Laser & Skin Rejuvenation Specialist",
            "specialties": "Laser Skin Resurfacing, Hyperpigmentation Peels, Carbon Glow Peels",
            "color_code": "#EC4899",
            "bio": "Internationally trained laser practitioner specializing in pigment correction, vascular treatment, and glow renewal.",
            "service_names": ["Laser Glow Rejuvenation Peel", "Hydra-Luxe Facial Therapy"],
        },
        {
            "name": "Lucas Moreau",
            "email": "lucas.moreau@lumierewellness.com",
            "phone": "+1 (555) 328-9407",
            "role_title": "Master Sports Physiotherapist & Body Restoration Specialist",
            "specialties": "Postural Correction, Trigger Point Therapy, Sports Recovery & Cupping",
            "color_code": "#059669",
            "bio": "Clinical sports therapist dedicated to biomechanical kinetic alignment and deep musculoskeletal tension relief.",
            "service_names": ["Targeted Kinetic Sports Recovery", "Deep Tissue Restoration Massage"],
        },
        {
            "name": "Chloe Davenport",
            "email": "chloe.davenport@lumierewellness.com",
            "phone": "+1 (555) 328-9408",
            "role_title": "Naturopathic Wellness & Sensory Rituals Practitioner",
            "specialties": "Aromatherapy Rituals, Stress Relief, Botanical Herbal Wraps, Reflexology",
            "color_code": "#6366F1",
            "bio": "Integrative holistic practitioner blending botanical essential extracts, guided acupressure, and restorative touch.",
            "service_names": ["Aromatherapy Full Body Ritual", "Deep Tissue Restoration Massage"],
        },
    ]

    existing_staff_map = {s.name.lower().strip(): s for s in session.query(Staff).all()}
    all_db_services = {srv.name.lower(): srv for srv in session.query(Service).all()}

    for prof in staff_profiles:
        name_key = prof["name"].lower().strip()
        if name_key in existing_staff_map:
            # Already added: DO NOT ADD AGAIN! Update missing attributes only
            st = existing_staff_map[name_key]
            if not getattr(st, "specialties", None):
                st.specialties = prof["specialties"]
            if prof.get("role_title") and (not st.role_title or st.role_title == "Specialist"):
                st.role_title = prof["role_title"]
            # Ensure assigned services are linked
            for s_name in prof.get("service_names", []):
                srv_match = all_db_services.get(s_name.lower())
                if srv_match and srv_match not in st.services:
                    st.services.append(srv_match)
        else:
            # Brand new staff member to add!
            new_st = Staff(
                name=prof["name"],
                email=prof["email"],
                phone=prof["phone"],
                role_title=prof["role_title"],
                specialties=prof["specialties"],
                color_code=prof["color_code"],
                bio=prof["bio"],
                is_active=True,
            )
            session.add(new_st)
            session.flush()

            # Add Mon-Sat working schedule
            for d in range(7):
                sched = StaffSchedule(
                    staff_id=new_st.id,
                    day_of_week=d,
                    is_working=(d < 6),
                    start_time="09:00" if d < 5 else "10:00",
                    end_time="18:00" if d < 5 else "16:00",
                    break_start="13:00",
                    break_end="14:00" if d < 5 else "13:30",
                )
                session.add(sched)
            session.flush()

            # Link services
            for s_name in prof.get("service_names", []):
                srv_match = all_db_services.get(s_name.lower())
                if srv_match:
                    new_st.services.append(srv_match)

            existing_staff_map[name_key] = new_st

    # 3. Comprehensive distinct specialist schedules & shift timings
    SPECIALIST_SCHEDULES = {
        "eleanor vance": {
            0: (False, "09:00", "17:00", "12:30", "13:30"),  # Mon OFF
            1: (True,  "09:00", "17:00", "12:30", "13:30"),  # Tue
            2: (True,  "09:00", "17:00", "12:30", "13:30"),  # Wed
            3: (True,  "09:00", "17:00", "12:30", "13:30"),  # Thu
            4: (True,  "09:00", "17:00", "12:30", "13:30"),  # Fri
            5: (True,  "10:00", "16:00", "13:00", "13:30"),  # Sat
            6: (False, "09:00", "17:00", "12:30", "13:30"),  # Sun OFF
        },
        "dr. marcus reed": {
            0: (True,  "08:30", "15:30", "12:00", "13:00"),  # Mon
            1: (True,  "08:30", "15:30", "12:00", "13:00"),  # Tue
            2: (True,  "08:30", "15:30", "12:00", "13:00"),  # Wed
            3: (True,  "08:30", "15:30", "12:00", "13:00"),  # Thu
            4: (False, "08:30", "15:30", "12:00", "13:00"),  # Fri OFF
            5: (False, "08:30", "15:30", "12:00", "13:00"),  # Sat OFF
            6: (False, "08:30", "15:30", "12:00", "13:00"),  # Sun OFF
        },
        "sophie dubois": {
            0: (False, "11:00", "19:30", "15:00", "16:00"),  # Mon OFF
            1: (False, "11:00", "19:30", "15:00", "16:00"),  # Tue OFF
            2: (True,  "11:00", "19:30", "15:00", "16:00"),  # Wed
            3: (True,  "11:00", "19:30", "15:00", "16:00"),  # Thu
            4: (True,  "11:00", "19:30", "15:00", "16:00"),  # Fri
            5: (True,  "11:00", "19:30", "15:00", "16:00"),  # Sat
            6: (True,  "11:00", "17:00", "14:00", "14:30"),  # Sun
        },
        "liam chen": {
            0: (True,  "10:00", "18:00", "14:00", "15:00"),  # Mon
            1: (True,  "10:00", "18:00", "14:00", "15:00"),  # Tue
            2: (False, "10:00", "18:00", "14:00", "15:00"),  # Wed OFF
            3: (True,  "10:00", "18:00", "14:00", "15:00"),  # Thu
            4: (True,  "10:00", "18:00", "14:00", "15:00"),  # Fri
            5: (False, "10:00", "18:00", "14:00", "15:00"),  # Sat OFF
            6: (False, "10:00", "18:00", "14:00", "15:00"),  # Sun OFF
        },
        "dr. alexander hayes": {
            0: (True,  "09:00", "14:30", "12:00", "12:30"),  # Mon
            1: (False, "09:00", "14:30", "12:00", "12:30"),  # Tue OFF
            2: (True,  "09:00", "14:30", "12:00", "12:30"),  # Wed
            3: (False, "09:00", "14:30", "12:00", "12:30"),  # Thu OFF
            4: (True,  "09:00", "14:30", "12:00", "12:30"),  # Fri
            5: (False, "09:00", "14:30", "12:00", "12:30"),  # Sat OFF
            6: (False, "09:00", "14:30", "12:00", "12:30"),  # Sun OFF
        },
        "maya patel": {
            0: (False, "10:30", "18:30", "14:00", "14:45"),  # Mon OFF
            1: (True,  "10:30", "18:30", "14:00", "14:45"),  # Tue
            2: (False, "10:30", "18:30", "14:00", "14:45"),  # Wed OFF
            3: (True,  "10:30", "18:30", "14:00", "14:45"),  # Thu
            4: (False, "10:30", "18:30", "14:00", "14:45"),  # Fri OFF
            5: (True,  "10:30", "18:30", "14:00", "14:45"),  # Sat
            6: (False, "10:30", "18:30", "14:00", "14:45"),  # Sun OFF
        },
        "lucas moreau": {
            0: (True,  "08:00", "16:00", "12:00", "13:00"),  # Mon
            1: (True,  "08:00", "16:00", "12:00", "13:00"),  # Tue
            2: (True,  "08:00", "16:00", "12:00", "13:00"),  # Wed
            3: (False, "08:00", "16:00", "12:00", "13:00"),  # Thu OFF
            4: (True,  "08:00", "16:00", "12:00", "13:00"),  # Fri
            5: (True,  "09:00", "15:00", "12:00", "12:30"),  # Sat
            6: (False, "08:00", "16:00", "12:00", "13:00"),  # Sun OFF
        },
        "chloe davenport": {
            0: (False, "12:00", "20:00", "16:00", "17:00"),  # Mon OFF
            1: (False, "12:00", "20:00", "16:00", "17:00"),  # Tue OFF
            2: (False, "12:00", "20:00", "16:00", "17:00"),  # Wed OFF
            3: (True,  "12:00", "20:00", "16:00", "17:00"),  # Thu
            4: (True,  "12:00", "20:00", "16:00", "17:00"),  # Fri
            5: (True,  "12:00", "20:00", "16:00", "17:00"),  # Sat
            6: (True,  "11:00", "18:00", "14:00", "14:45"),  # Sun
        },
    }

    # Update or add schedules for all staff members according to their individual work timings
    for name_key, sched_dict in SPECIALIST_SCHEDULES.items():
        st = existing_staff_map.get(name_key)
        if st:
            for d_idx, (is_work, s_time, e_time, b_start, b_end) in sched_dict.items():
                sc = (
                    session.query(StaffSchedule)
                    .filter(StaffSchedule.staff_id == st.id, StaffSchedule.day_of_week == d_idx)
                    .first()
                )
                if sc:
                    sc.is_working = is_work
                    sc.start_time = s_time
                    sc.end_time = e_time
                    sc.break_start = b_start
                    sc.break_end = b_end
                else:
                    new_sc = StaffSchedule(
                        staff_id=st.id,
                        day_of_week=d_idx,
                        is_working=is_work,
                        start_time=s_time,
                        end_time=e_time,
                        break_start=b_start,
                        break_end=b_end,
                    )
                    session.add(new_sc)

    # 4. Update theme preference if it was default emerald
    theme_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "color_theme").first()
    if theme_setting and theme_setting.value in ("emerald", "slate"):
        theme_setting.value = "midnight_teal"

    session.commit()
