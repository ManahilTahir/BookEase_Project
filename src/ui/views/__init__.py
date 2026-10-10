"""UI Views module for BookEase."""

from src.ui.views.login_view import LoginView
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.booking_wizard import BookingWizardView
from src.ui.views.calendar_view import CalendarView
from src.ui.views.appointments_view import AppointmentsView
from src.ui.views.customers_view import CustomersView
from src.ui.views.staff_view import StaffView
from src.ui.views.services_view import ServicesView
from src.ui.views.reports_view import ReportsView
from src.ui.views.settings_view import SettingsView

__all__ = [
    "LoginView",
    "DashboardView",
    "BookingWizardView",
    "CalendarView",
    "AppointmentsView",
    "CustomersView",
    "StaffView",
    "ServicesView",
    "ReportsView",
    "SettingsView",
]
