"""Constants and generation templates for PlacementOps datasets."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SEED = 20260829

PLACEMENT_DAYS = ("DAY_1", "DAY_2", "DAY_3", "DAY_4")
OPERATING_START = "09:00"
OPERATING_END = "18:00"
TIME_SLOTS = ("09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00")

COMPANY_COUNT = 35
STUDENT_COUNT = 800
ROOM_COUNT = 20

PRIORITY_TIERS = ("P1", "P2", "P3", "P4")
STUDENT_STATUSES = ("ACTIVE", "WITHDRAWN")
ROOM_STATUSES = ("AVAILABLE", "UNAVAILABLE")
PANEL_STATUSES = ("AVAILABLE", "DROPPED")
INTERVIEW_STATUSES = ("UNSCHEDULED",)

VALIDATION_THRESHOLDS = {
    "room_demand_ratio_min": 0.78,
    "room_demand_ratio_max": 1.03,
    "panel_demand_ratio_max": 0.92,
    "active_zero_shortlist_pct_max": 25.0,
    "cgpa_shortlist_correlation_min": 0.45,
    "popularity_shortlist_correlation_min": 0.45,
}

BRANCHES = (
    "CSE",
    "IT",
    "ECE",
    "EEE",
    "ME",
    "CE",
    "AI",
    "DS",
)

FIRST_NAMES = (
    "Aarav", "Aditi", "Advait", "Akansha", "Akash", "Ananya", "Arjun", "Bhavya",
    "Charvi", "Dev", "Diya", "Harsh", "Ishaan", "Ishita", "Jatin", "Kavya",
    "Krishna", "Lakshya", "Meera", "Mihir", "Neha", "Nikhil", "Pranav", "Priya",
    "Rhea", "Rohan", "Saanvi", "Sakshi", "Shreya", "Siddharth", "Tanvi", "Tara",
    "Utkarsh", "Vaibhav", "Ved", "Yash",
)

LAST_NAMES = (
    "Agarwal", "Bansal", "Chauhan", "Deshmukh", "Ghosh", "Gupta", "Iyer", "Jain",
    "Joshi", "Kapoor", "Kulkarni", "Mehta", "Menon", "Mishra", "Nair", "Patel",
    "Rao", "Reddy", "Saxena", "Shah", "Sharma", "Singh", "Srinivasan", "Trivedi",
    "Verma", "Yadav",
)

BUILDINGS = ("Academic Block A", "Academic Block B", "Innovation Center", "Tech Tower")


@dataclass(frozen=True, slots=True)
class CompanyTemplate:
    name: str
    industry: str
    popularity: float
    cutoff_base: float
    duration_options: tuple[int, ...]
    preferred_branches: tuple[str, ...]


COMPANY_TEMPLATES = (
    CompanyTemplate("Nimbus Cloud", "Cloud Infrastructure", 0.98, 7.6, (45, 60), ("CSE", "IT", "AI", "DS")),
    CompanyTemplate("BrightScale AI", "Artificial Intelligence", 0.96, 7.8, (60, 75), ("CSE", "AI", "DS", "ECE")),
    CompanyTemplate("VectorSoft", "Enterprise Software", 0.94, 7.4, (45, 60), ("CSE", "IT", "AI", "DS")),
    CompanyTemplate("QuantumEdge Analytics", "Analytics", 0.92, 7.5, (45, 60), ("DS", "AI", "CSE", "IT")),
    CompanyTemplate("Nova Payments", "FinTech", 0.91, 7.3, (45, 60), ("CSE", "IT", "ECE", "AI")),
    CompanyTemplate("Apex Fintech", "FinTech", 0.89, 7.7, (60,), ("CSE", "IT", "DS", "ECE")),
    CompanyTemplate("Clearline SaaS", "SaaS", 0.88, 7.2, (45,), ("CSE", "IT", "AI", "DS")),
    CompanyTemplate("Pulse Commerce", "E-Commerce", 0.87, 7.1, (45, 60), ("CSE", "IT", "AI", "DS")),
    CompanyTemplate("Stellar Bank", "Banking", 0.85, 7.4, (45, 60), ("CSE", "IT", "ECE", "EEE")),
    CompanyTemplate("BlueRiver Retail", "Retail Tech", 0.84, 7.0, (30, 45), ("CSE", "IT", "DS", "AI")),
    CompanyTemplate("Meridian Telecom", "Telecom", 0.81, 7.2, (45, 60), ("ECE", "EEE", "CSE", "IT")),
    CompanyTemplate("Fusion Semiconductors", "Semiconductors", 0.80, 7.5, (60, 75), ("ECE", "EEE", "ME")),
    CompanyTemplate("Synapse Security", "Cybersecurity", 0.79, 7.6, (60,), ("CSE", "IT", "ECE", "AI")),
    CompanyTemplate("Vertex Labs", "Product Engineering", 0.77, 7.3, (45, 60), ("CSE", "IT", "ECE", "DS")),
    CompanyTemplate("AccelData Systems", "Data Platforms", 0.76, 7.2, (45, 60), ("CSE", "IT", "DS", "AI")),
    CompanyTemplate("Helio Energy", "Energy", 0.72, 6.9, (45, 60), ("EEE", "ME", "CE", "ECE")),
    CompanyTemplate("Kinetic Mobility", "Automotive", 0.71, 7.0, (45, 60), ("ME", "ECE", "EEE", "CSE")),
    CompanyTemplate("Orion Motors", "Automotive", 0.69, 6.8, (45,), ("ME", "EEE", "ECE", "CE")),
    CompanyTemplate("Granite Consulting", "Consulting", 0.68, 7.4, (30, 45), ("CSE", "IT", "ECE", "ME")),
    CompanyTemplate("Northstar Logistics", "Logistics", 0.67, 6.8, (30, 45), ("CE", "ME", "CSE", "IT")),
    CompanyTemplate("Cedar HealthTech", "HealthTech", 0.66, 7.2, (45, 60), ("CSE", "IT", "ECE", "AI")),
    CompanyTemplate("Prism Networks", "Networking", 0.64, 7.0, (45, 60), ("ECE", "EEE", "CSE", "IT")),
    CompanyTemplate("Beacon Insurance", "Insurance", 0.63, 6.9, (30, 45), ("CSE", "IT", "ECE", "EEE")),
    CompanyTemplate("Maple ERP", "Enterprise Software", 0.62, 6.8, (45,), ("CSE", "IT", "ECE", "DS")),
    CompanyTemplate("Horizon Media", "Digital Media", 0.60, 6.7, (30, 45), ("CSE", "IT", "AI", "DS")),
    CompanyTemplate("TerraGrid Infra", "Infrastructure", 0.59, 6.8, (45, 60), ("CE", "ME", "EEE")),
    CompanyTemplate("Elevate HRTech", "HRTech", 0.57, 6.7, (30, 45), ("CSE", "IT", "DS", "AI")),
    CompanyTemplate("Zentra Devices", "Embedded Systems", 0.56, 7.0, (45, 60), ("ECE", "EEE", "ME")),
    CompanyTemplate("TruVista Pharma", "Pharma Tech", 0.55, 6.9, (45,), ("CSE", "IT", "ECE", "DS")),
    CompanyTemplate("Delta Robotics", "Robotics", 0.54, 7.1, (60, 75), ("ME", "ECE", "EEE", "AI")),
    CompanyTemplate("Argo Aerospace", "Aerospace", 0.50, 7.3, (60,), ("ME", "ECE", "EEE")),
    CompanyTemplate("Riverfront EPC", "Engineering Services", 0.48, 6.6, (45,), ("CE", "ME", "EEE")),
    CompanyTemplate("Summit Foods", "FMCG", 0.46, 6.5, (30, 45), ("CSE", "IT", "ME", "CE")),
    CompanyTemplate("Ironclad Manufacturing", "Manufacturing", 0.44, 6.6, (45, 60), ("ME", "EEE", "CE")),
    CompanyTemplate("DeepCore Mining Tech", "Industrial Tech", 0.41, 6.7, (45, 60), ("ME", "CE", "EEE")),
)
