
from .find_patient_by_email import FindPatientByEmail
from .find_patient_by_name_dob import FindPatientByNameDOB
from .get_patient_details import GetPatientDetails
from .get_appointment_details import GetAppointmentDetails
from .get_provider_details import GetProviderDetails
from .get_medical_record import GetMedicalRecord
from .get_regimen_options import GetRegimenOptions
from .list_patient_medical_records import ListPatientMedicalRecords
from .list_available_providers import ListAvailableProviders
from .list_patient_appointments import ListPatientAppointments
from .list_medication_suppliers import ListMedicationSuppliers
from .list_telemetry_uploads import ListTelemetryUploads
from .check_drug_interactions import CheckDrugInteractions
from .schedule_appointment import ScheduleAppointment
from .cancel_appointment import CancelAppointment
from .reschedule_appointment import RescheduleAppointment
from .calculate import Calculate
from .think import Think
from .transfer_to_human_support import TransferToHumanSupport
from .update_prescription_supplier import UpdatePrescriptionSupplier
from .list_telemetry_devices import ListTelemetryDevices
from .get_telemetry_upload import GetTelemetryUpload
from .update_medical_record_note import UpdateMedicalRecordNote


ALL_TOOLS = [
    FindPatientByEmail,
    FindPatientByNameDOB,
    GetPatientDetails,
    GetAppointmentDetails,
    GetProviderDetails,
    GetMedicalRecord,
    GetRegimenOptions,
    ListPatientMedicalRecords,
    ListAvailableProviders,
    ListPatientAppointments,
    ListMedicationSuppliers,
    ListTelemetryUploads,
    CheckDrugInteractions,
    ScheduleAppointment,
    CancelAppointment,
    RescheduleAppointment,
    Calculate,
    Think,
    TransferToHumanSupport,
    UpdatePrescriptionSupplier,
    ListTelemetryDevices,
    GetTelemetryUpload,
    UpdateMedicalRecordNote,
]
