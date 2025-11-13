
from .calculate import Calculate
from .think import Think
from .find_customer_by_email import FindCustomerByEmail
from .find_customer_by_phone import FindCustomerByPhone
from .get_customer_details import GetCustomerDetails
from .get_service_details import GetServiceDetails
from .get_device_details import GetDeviceDetails
from .get_billing_details import GetBillingDetails
from .manage_service import ManageService
from .troubleshoot_device import TroubleshootDevice
from .create_support_ticket import CreateSupportTicket
from .get_support_ticket_details import GetSupportTicketDetails
from .add_device import AddDevice
from .manage_billing import ManageBilling
from .get_services import GetServices
from .get_senior_discount import GetSeniorDiscount
from .record_payment import RecordPayment
from .modify_support_ticket import ModifySupportTicket

ALL_TOOLS = [
    Calculate,
    Think,
    FindCustomerByEmail,
    FindCustomerByPhone,
    GetCustomerDetails,
    GetServiceDetails,
    GetDeviceDetails,
    GetBillingDetails,
    ManageService,
    TroubleshootDevice,
    CreateSupportTicket,
    GetSupportTicketDetails,
    AddDevice,
    ManageBilling,
    GetServices,
    GetSeniorDiscount,
    ModifySupportTicket,
    RecordPayment,
]
