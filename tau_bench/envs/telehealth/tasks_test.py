from datetime import datetime

from tau_bench.envs.telehealth.data import load_data
from tau_bench.types import Action, Task


def _format_currency(value: float) -> str:
    """Return a 2-decimal string for currency comparisons."""
    return f"{value:.2f}"



TASKS_TEST = [
    Task(
        annotator="0",
        user_id="sarah_johnson_1234",
        instruction="""
        You are Sarah Johnson, born March 15, 1985. 
        You want to schedule a follow-up appointment on Tuesday, September 23, 2025 at 10:00 AM 
        with your primary care doctor Dr. Garcia to discuss your blood pressure medication.
        """,
        actions=[
            Action(name="schedule_appointment", kwargs={"patient_id": "sarah_johnson_1234", "provider_id": "dr_garcia_primary", "date": "2025-09-23", "time": "10:00", "appointment_type": "follow_up"}),
        ],
        outputs= [],
    ),
    Task(
        annotator="1",
        user_id="david_martinez_5678",
        instruction="""
        You are David Martinez, email david.martinez@email.com. 
        You want to schedule a consultation appointment on Monday, September 22, 2025 at 2:00 PM (14:00) 
        with Dr. Smith (the cardiologist) to discuss your heart palpitations. However, if Dr. Smith is not 
        available at that exact time, you are willing to schedule with Dr. Garcia (your primary care doctor) 
        at the same time instead. You need to check both doctors' availability and schedules first.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "david.martinez@email.com"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_smith_cardiology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_garcia_primary"}),
            Action(name="schedule_appointment", kwargs={"patient_id": "david_martinez_5678", "provider_id": "dr_garcia_primary", "date": "2025-09-22", "time": "14:00", "appointment_type": "sick_visit"}),
        ],
        outputs=[],
    ),
    
    Task(
        annotator="2",
        user_id="daiki_sanchez_46236",
        instruction="""
        You are Daiki Sanchez (DOB 1991-05-27) checking the portal yet again. You already fired off a note earlier asking whether that cardiology telehealth consult you vaguely remember booking ever existed, so when the assistant finally answers you expect them to look you up by your portal email and sweep specifically for any cardiology visits still stuck in pending approval. If there is nothing waiting, fine—just say so and move on, but absolutely do not fabricate or auto-create a replacement without clearing it with you.

        Once that audit is done, you want to arrange a brand-new telehealth cardiology slot on Monday, April 14, 2025 at exactly 09:00, but you will only show up if the cardiologist both speaks Japanese and has at least 20 years of experience. You need those two traits together because your dad will be listening in. If even one of those requirements fails, you would rather be routed to a human scheduler and wait than settle for an English-only or junior doctor.

        You are curt, you do not let them bargain you into compromises, and if no provider satisfies both traits simultaneously you insist on being handed off to a person instead of letting them guess.
                """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "daikisanchez1479@example.com"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "daiki_sanchez_46236", "status_filter": "pending_approval"}),
            Action(name="list_available_providers", kwargs={"specialty": "Cardiology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_thompson_cardiology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_smith_cardiology"}),
            Action(name="transfer_to_human_support", kwargs={"reason": "No cardiologist meets the Japanese language plus 20-year experience requirement for the requested slot"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="3",
        user_id="mira_desai_3471",
        instruction="""
        Your user id is mira_desai_3471 and your email address is mira.desai3471@gmail.com. You want to schedule an urgent telehealth consultation for May 20, 2025 ideally at 6 AM (same day appointment). You want to consult with a primary care doctor. You prefer Dr. Garcia but any primary care provider is also fine. You have 2 urgent medical concerns to discuss. You do not want insurance billing. You want to use your two telehealth credit vouchers to pay. If only one voucher can be used, you prefer using the one ending in 224. You are reactive to the agent and will not say anything that is not asked. Your medical history is in your patient profile so you do not prefer to provide it.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "mira.desai3471@gmail.com"}),
            Action(name="get_patient_details", kwargs={"patient_id": "mira_desai_3471"}),
            Action(name="list_available_providers", kwargs={"specialty": "Primary Care"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_garcia_primary"}),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "mira_desai_3471",
                    "provider_id": "dr_garcia_primary",
                    "date": "2025-05-20",
                    "time": "06:00",
                    "appointment_type": "sick_visit",
                    "bill_insurance": False,
                    "voucher_id": "THV-224",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="4",
        user_id="carlos_martinez_5512",
        instruction="""
        Your user id is carlos_martinez_5512 and your email is carlos.martinez5512@gmail.com. All three of your kids (ages 4, 7, and 12) started vomiting six hours ago after eating the same leftovers. You need one family telehealth sick visit today May 20, 2025 at exactly 08:30 with a pediatric-certified provider who can evaluate all three children together so you only explain things once. Their medical details are already linked in the portal and you will only share extra history if the assistant insists.

        You insist on paying with the family emergency medical fund account—not insurance—and you want that noted explicitly on the booking. You are reactive: answer prompts, but do not volunteer information.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "carlos.martinez5512@gmail.com"}),
            Action(name="get_patient_details", kwargs={"patient_id": "carlos_martinez_5512"}),
            Action(name="get_patient_details", kwargs={"patient_id": "sofia_martinez_2019"}),
            Action(name="get_patient_details", kwargs={"patient_id": "mateo_martinez_2016"}),
            Action(name="get_patient_details", kwargs={"patient_id": "isabella_martinez_2011"}),
            Action(name="list_available_providers", kwargs={"specialty": "Pediatrics"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_nguyen_pediatrics"}),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "carlos_martinez_5512",
                    "provider_id": "dr_nguyen_pediatrics",
                    "date": "2025-05-20",
                    "time": "08:30",
                    "appointment_type": "sick_visit",
                    "bill_insurance": False,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="5",
        user_id="maria_rodriguez_4567",
        instruction="""
        You are Maria Rodriguez (DOB 1990-12-03) catching up on that telehealth to-do list. The mid-December cardiology video visit with Dr. Smith (the one stamped APPT009 at 4 PM) never cleared insurance, so check with the assistant who you are, see whether that slot is still stuck in pending land, and only if it hasn’t been approved yet do you have them remove it so nothing lingers. Once that old booking is out of the way, you want a fresh specialist telehealth consult with whichever cardiologist has the deepest experience—start with Dr. Margaret Thompson—and you only want it if she can take you exactly at 09:00 on Tuesday, January 23, 2025. If she can’t or that time is gone, fall back to Dr. Robert Smith at that same moment; if neither doctor can commit to 09:00, you leave everything canceled and just report back. No matter how it ends, you expect to hear the insurance copay and see the telehealth link for whatever appointment winds up surviving. Keep the tone polite but brisk and expect the assistant to double-check availability instead of guessing.
        """,
        actions=[
            Action(
                name="find_patient_by_name_dob",
                kwargs={
                    "first_name": "Maria",
                    "last_name": "Rodriguez",
                    "date_of_birth": "1990-12-03",
                },
            ),
            Action(
                name="list_patient_appointments",
                kwargs={
                    "patient_id": "maria_rodriguez_4567",
                    "status_filter": "pending_approval",
                },
            ),
            Action(
                name="cancel_appointment",
                kwargs={"appointment_id": "APPT009"},
            ),
            Action(
                name="list_available_providers",
                kwargs={"specialty": "Cardiology"},
            ),
            Action(
                name="get_provider_details",
                kwargs={"provider_id": "dr_thompson_cardiology"},
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "maria_rodriguez_4567",
                    "provider_id": "dr_thompson_cardiology",
                    "date": "2025-01-23",
                    "time": "09:00",
                    "appointment_type": "specialist_consultation",
                },
            ),
            Action(
                name="get_patient_details",
                kwargs={"patient_id": "maria_rodriguez_4567"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="6",
        user_id="heather_collins_48201",
        instruction="""
        You are Heather Collins, born April 19, 1982, dialing in from Grand Rapids. Your portal email is heather.collins82@gmail.com. You want the prescriptions from your last four telehealth encounters and, for each medication, the cheapest Indian supplier the hospital catalog lists (company, brand, USD price). If a medication lacks an Indian supplier, you expect a blunt "no Indian supplier" answer. Once you have the information, you want each prescription record updated to reflect the selected supplier details so the pharmacy team can start sourcing immediately. You are terse, impatient, and do not want small talk.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "heather.collins82@gmail.com"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "heather_collins_48201", "limit": 4},
            ),
            Action(name="get_medical_record", kwargs={"record_id": "REC008"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC007"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC006"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC005"}),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Fluticasone Inhaler", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC008",
                    "medication": "Fluticasone Inhaler",
                    "supplier_company": "Lotus Respiratory (India)",
                    "brand_name": "Flohale",
                    "price_usd": 7.1,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Montelukast", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC007",
                    "medication": "Montelukast",
                    "supplier_company": "Lotus Breath (India)",
                    "brand_name": "BreathFree",
                    "price_usd": 3.05,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Ezetimibe", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC006",
                    "medication": "Ezetimibe",
                    "supplier_company": "Lucknow Lipids (India)",
                    "brand_name": "Ezeswift",
                    "price_usd": 3.25,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Atorvastatin", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC005",
                    "medication": "Atorvastatin",
                    "supplier_company": "VedaRx Labs (India)",
                    "brand_name": "Atorveeda",
                    "price_usd": 4.05,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="7",
        user_id="amara_osei_8834",
        instruction="""
        Your user id is amara_osei_8834 and your email is amara.osei8834@yahoo.com. Your usual insulin pens are on nationwide backorder and you have three days of supply left. You need an emergency same-day telehealth consult on Tuesday, May 20, 2025 with an endocrinologist who can source alternative insulin formulations. You insist the visit be paid from your diabetes emergency account (note it explicitly) and you remain terse unless asked direct questions. Your diabetes management plan is already in your records and you do not want to repeat it. After confirming the endocrinologist, you expect your current prescriptions to be updated with the cheapest Indian suppliers the hospital catalog lists so the pharmacy can act immediately.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "amara.osei8834@yahoo.com"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "amara_osei_8834", "limit": 4},
            ),
            Action(name="get_medical_record", kwargs={"record_id": "REC010"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC009"}),
            Action(
                name="list_available_providers",
                kwargs={"specialty": "Endocrinology"},
            ),
            Action(
                name="get_provider_details",
                kwargs={"provider_id": "dr_singh_endocrinology"},
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "amara_osei_8834",
                    "provider_id": "dr_singh_endocrinology",
                    "date": "2025-05-20",
                    "time": "13:30",
                    "appointment_type": "specialist_consultation",
                    "bill_insurance": False,
                    "payment_notes": "Charge diabetes emergency account",
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Insulin Glargine", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC010",
                    "medication": "Insulin Glargine",
                    "supplier_company": "SunPharm Endocrine",
                    "brand_name": "Basargine",
                    "price_usd": 21.6,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Insulin Lispro", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC010",
                    "medication": "Insulin Lispro",
                    "supplier_company": "Bengal EndoCare",
                    "brand_name": "SwiftLis",
                    "price_usd": 19.2,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="8",
        user_id="mira_desai_3471",
        instruction="""
        Your user id is mira_desai_3471 and your email address is mira.desai3471@gmail.com. Overnight triage auto-booked you for an 11:00 AM pending virtual slot on May 20, 2025, but you need a same-day primary care consult much earlier—ideally 06:00—with whoever can review two urgent concerns before work. You prefer Dr. Garcia if the slot is open, otherwise any primary-care doctor will do. You refuse insurance billing; charge the visit to your telehealth credit vouchers and, if only one applies, use the one ending in 224 and note it. You only answer direct questions and do not want to rehash your medical history since it is already on file.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "mira.desai3471@gmail.com"},
            ),
            Action(
                name="list_patient_appointments",
                kwargs={"patient_id": "mira_desai_3471", "status_filter": "pending_approval"},
            ),
            Action(
                name="cancel_appointment",
                kwargs={"appointment_id": "APPT027"},
            ),
            Action(
                name="list_available_providers",
                kwargs={"specialty": "Primary Care"},
            ),
            Action(
                name="get_provider_details",
                kwargs={"provider_id": "dr_garcia_primary"},
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "mira_desai_3471",
                    "provider_id": "dr_garcia_primary",
                    "date": "2025-05-20",
                    "time": "06:00",
                    "appointment_type": "sick_visit",
                    "bill_insurance": False,
                    "voucher_id": "THV-224",
                    "payment_notes": "Apply telehealth voucher ending 224 for urgent dawn consult",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="9",
        user_id="nina_park_8020",
        instruction="""
        You are nina_park_8020 (zip 28236), email nina.park8020@gmail.com. During your remote physical-therapy session you were issued a medium resistance band set and a firm foam massage roller. Your therapist now wants you using heavier resistance and a cushioned roller. Retrieve the latest telehealth kit record to confirm the current items, then update both prescriptions with the lowest-cost Indian catalog options that meet those preferences.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "nina.park8020@gmail.com"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "nina_park_8020", "limit": 1},
            ),
            Action(name="get_medical_record", kwargs={"record_id": "REC011"}),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Resistance Band Set", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC011",
                    "medication": "Resistance Band Set",
                    "supplier_company": "Mumbai Active Care",
                    "brand_name": "Active Care Heavy",
                    "price_usd": 17.6,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Foam Massage Roller", "country_filter": "India", "limit": 1},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC011",
                    "medication": "Foam Massage Roller",
                    "supplier_company": "Kerala Wellness Supplies",
                    "brand_name": "Kerala Soft Relief",
                    "price_usd": 14.9,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="10",
        user_id="yumi_tanaka_7410",
        instruction="""
        You are Yumi Tanaka (DOB 1970-04-14) logging in through yumi.tanaka7410@pacificcare.org. You are prepping for your atrial-fibrillation ablation week and you insist on a meticulous, bilingual-ready workflow:

        • Authenticate yourself, pull your profile so you know the copay tiers, and audit every May 2025 telehealth appointment on your calendar before touching anything. Document the status of the pending cardiology slot at 09:30 (APPT029) and the already-scheduled reviews (APPT030 with Dr. Thompson and APPT031 with care coordinator Ito). Cancel only the redundant pending cardiology visit once you have the details captured.
        • Compare the cardiology roster: you need a provider who speaks Japanese and has 25+ years of experience. Verify Dr. Hiroko Saito first, then double-check Dr. Margaret Thompson as a fallback, and glance at the care coordinator profile to be sure they stay looped in. After that, secure a fresh telehealth cardiology review for Thursday, May 22, 2025 at 08:30 with whichever cardiologist satisfies the requirement (do not guess—confirm availability). Track the new meeting link and make sure the quoted copay still matches your specialist copay.
        • Pull every recent cardiology/coordination medical record (the system should list three). Drill into each record. For every prescription you find there (Warfarin, Sertraline, Rosuvastatin), ask the assistant to fetch the three cheapest Indian suppliers and then have them update the record to the lowest-priced option, recording company, brand, and USD price.
        • Because you’re layering therapies, run a drug interaction check twice: once treating Rosuvastatin as the new agent against your current regimen (Warfarin, Sertraline, Aspirin EC, Metoprolol Succinate) and once treating Warfarin against Rosuvastatin alone. Only escalate to a human if a high-severity issue appears; otherwise summarize the highest-severity pair yourself.
        • Review the Rosuvastatin/Ezetimibe combo catalog listings so you can compare prices, but do not change your prescriptions yet.
        • After scheduling the new visit and updating records, refresh your full appointment list to verify accuracy.

        Stay brisk and data-focused—no small talk, no assumptions.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "yumi.tanaka7410@pacificcare.org"}),
            Action(name="get_patient_details", kwargs={"patient_id": "yumi_tanaka_7410"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "yumi_tanaka_7410"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT029"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT030"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT031"}),
            Action(name="cancel_appointment", kwargs={"appointment_id": "APPT029"}),
            Action(name="list_available_providers", kwargs={"specialty": "Cardiology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_saito_cardiology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_thompson_cardiology"}),
            Action(name="list_available_providers", kwargs={"specialty": "Care Coordination"}),
            Action(name="get_provider_details", kwargs={"provider_id": "care_coordinator_ito"}),
            Action(name="list_patient_medical_records", kwargs={"patient_id": "yumi_tanaka_7410", "limit": 12}),
            Action(name="get_medical_record", kwargs={"record_id": "REC012"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC013"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC014"}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Warfarin", "country_filter": "India", "limit": 3}),
            Action(name="update_prescription_supplier", kwargs={"record_id": "REC012", "medication": "Warfarin", "supplier_company": "VedaRx Labs", "brand_name": "Vedarin", "price_usd": 4.28}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Sertraline", "country_filter": "India", "limit": 3}),
            Action(name="update_prescription_supplier", kwargs={"record_id": "REC012", "medication": "Sertraline", "supplier_company": "Triveni Pharma", "brand_name": "Setrina", "price_usd": 4.55}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Rosuvastatin", "country_filter": "India", "limit": 3}),
            Action(name="update_prescription_supplier", kwargs={"record_id": "REC013", "medication": "Rosuvastatin", "supplier_company": "Aurora Heart Labs", "brand_name": "RosuPrime", "price_usd": 5.95}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Rosuvastatin/Ezetimibe Combo", "country_filter": "India", "limit": 3}),
            Action(name="schedule_appointment", kwargs={"patient_id": "yumi_tanaka_7410", "provider_id": "dr_saito_cardiology", "date": "2025-05-22", "time": "08:30", "appointment_type": "specialist_consultation"}),
            Action(name="get_patient_details", kwargs={"patient_id": "yumi_tanaka_7410"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "yumi_tanaka_7410"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT032"}),
            Action(name="check_drug_interactions", kwargs={"primary_medication": "Rosuvastatin", "current_medications": ["Warfarin", "Sertraline", "Aspirin EC", "Metoprolol Succinate"]}),
            Action(name="check_drug_interactions", kwargs={"primary_medication": "Warfarin", "current_medications": ["Rosuvastatin"]}),
        ],
        outputs=[],
    ),
    Task(
        annotator="11",
        user_id="elena_morales_9921",
        instruction="""
        You are Elena Morales (DOB 1984-09-22) preparing for ambulatory neurology telemetry and a psychology follow-up. You insist the assistant works methodically:

        • Authenticate yourself via your WestCare email, then ask the assistant for the full list of July 2025 telehealth appointments. Have them confirm which ones are pending vs. scheduled and store the status of the neurology slot at 09:30 (APPT033) before cancelling anything.
        • Once you see the list, explicitly ask the assistant to filter the appointments to only the pending approvals so you can double-check APPT033, then cancel it after you have its details documented.
        • You want to replace that slot with a consult on Tuesday, July 22, 2025 at 10:30 with a neurology provider who has at least 20 years of experience and speaks both English and Croatian. Confirm the provider’s credentials and availability before you let the assistant schedule it. Make sure they report the new meeting link and copay.
        • After the neurology booking, verify that your psychology follow-up with Dr. Hartwell (APPT034) is still on the calendar and that she remains informed. Ask the assistant to reconfirm by fetching her provider details.
        • Next, drill into the neurology intake record (REC015) to review lamotrigine and buspirone prescriptions. Request that the assistant first fetch the three cheapest Indian suppliers for each medication and then update the record to the lowest-priced option, capturing supplier company, brand, and USD price.
        • Because lamotrigine interacts with other anticonvulsants, have the assistant run a drug interaction check treating Lamotrigine as primary against your current regimen (Lamotrigine, Buspirone, Aspirin EC) and then a second check treating Buspirone as primary against Lamotrigine. If no high-severity issues appear, ask for a concise summary.
        • Finally, ask the assistant to provide you with a refreshed appointment list (all statuses) so you can confirm everything is accurate after the updates.

        Maintain a precise, no-nonsense tone.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "elena.morales9921@westcare.org"}),
            Action(name="get_patient_details", kwargs={"patient_id": "elena_morales_9921"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "elena_morales_9921"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "elena_morales_9921", "status_filter": "pending_approval"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT033"}),
            Action(name="cancel_appointment", kwargs={"appointment_id": "APPT033"}),
            Action(name="list_available_providers", kwargs={"specialty": "Neurology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_ivankovic_neurology"}),
            Action(name="schedule_appointment", kwargs={"patient_id": "elena_morales_9921", "provider_id": "dr_ivankovic_neurology", "date": "2025-07-22", "time": "10:30", "appointment_type": "specialist_consultation"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_hartwell_psychology"}),
            Action(name="list_patient_medical_records", kwargs={"patient_id": "elena_morales_9921", "limit": 5}),
            Action(name="get_medical_record", kwargs={"record_id": "REC015"}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Lamotrigine", "country_filter": "India", "limit": 3}),
            Action(name="update_prescription_supplier", kwargs={"record_id": "REC015", "medication": "Lamotrigine", "supplier_company": "Hyderabad CNS Pharma", "brand_name": "NeuroLam", "price_usd": 6.05}),
            Action(name="list_medication_suppliers", kwargs={"medication": "Buspirone", "country_filter": "India", "limit": 3}),
            Action(name="update_prescription_supplier", kwargs={"record_id": "REC015", "medication": "Buspirone", "supplier_company": "Delhi ZenLabs", "brand_name": "Zenpira", "price_usd": 3.05}),
            Action(name="check_drug_interactions", kwargs={"primary_medication": "Lamotrigine", "current_medications": ["Lamotrigine", "Buspirone", "Aspirin EC"]}),
            Action(name="check_drug_interactions", kwargs={"primary_medication": "Buspirone", "current_medications": ["Lamotrigine"]}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "elena_morales_9921"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="12",
        user_id="natalia_cole_8832",
        instruction="""
        You are Natalia Cole (DOB 1989-03-18), email natalia.cole8832@northstarhealth.org, juggling seizure telemetry logistics. You insist the assistant follow your multi-step plan:

        • Authenticate via your email (natalia.cole8832@northstarhealth.org) and pull your profile so copay info is handy. Then request a 10-item telemetry inventory snapshot, followed by filtered views for devices marked "missing/overdue," "maintenance," and "inspection" so you can log overdue hardware IDs and QA bottlenecks (aim for at least 10 cumulative device rows across the pulls).
        • After the hardware review, pull your August telehealth calendar to capture the statuses of the pending neurology clearance (APPT036), the device coaching slot (APPT037), and the psychology follow-up (APPT038). Record their states before making any changes.
        • You insist on staying with Dr. Patel. Cancel the pending neurology appointment (APPT036) only after its details are logged; then search for available neurologists (list available providers with specialty Neurology) and confirm Dr. Patel's credentials (19 years' experience, English/Gujarati) before rebooking a telehealth consult for Wednesday, August 07, 2025 at 09:30. Capture the new meeting link and copay.
        • Re-pull the APPT037 and APPT038 details afterward to ensure no overlap with the new slot. If the psychology visit conflicts, reschedule it to the next open afternoon slot that week with Dr. Hartwell; if there’s no conflict, simply note the gap.
        • Retrieve your latest telemetry intake record (REC017) and use a quick `think` step to outline compliance follow-ups based on its notes.
        • Schedule a remote device inspection with telemetry coach Morgan Riley for Friday, August 08, 2025 at 11:00 to clear the inspection backlog, then refresh your appointment roster to confirm it was added.
        • Close out by pulling another telemetry snapshot filtered to "available" status so you can verify replacements are ready after the compliance actions.

        Keep the tone crisp and logistical, emphasizing audit readiness.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "natalia.cole8832@northstarhealth.org"}),
            Action(name="get_patient_details", kwargs={"patient_id": "natalia_cole_8832"}),
            Action(name="list_telemetry_devices", kwargs={"limit": 10}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "missing_overdue"}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "maintenance"}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "inspection", "limit": 10}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "natalia_cole_8832"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT036"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT037"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT038"}),
            Action(name="cancel_appointment", kwargs={"appointment_id": "APPT036"}),
            Action(name="list_available_providers", kwargs={"specialty": "Neurology"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_patel_neurology"}),
            Action(name="schedule_appointment", kwargs={"patient_id": "natalia_cole_8832", "provider_id": "dr_patel_neurology", "date": "2025-08-07", "time": "09:30", "appointment_type": "specialist_consultation"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT038"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_hartwell_psychology"}),
            Action(name="list_patient_medical_records", kwargs={"patient_id": "natalia_cole_8832", "limit": 5}),
            Action(name="get_medical_record", kwargs={"record_id": "REC017"}),
            Action(name="think", kwargs={"note": "Plan follow-ups based on REC017 telemetry notes"}),
            Action(name="schedule_appointment", kwargs={"patient_id": "natalia_cole_8832", "provider_id": "coach_riley_telemetry", "date": "2025-08-08", "time": "11:00", "appointment_type": "device_inspection"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "natalia_cole_8832"}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "available", "limit": 10}),
        ],
        outputs=[],
    ),
    Task(
        annotator="13",
        user_id="jin_park_7284",
        instruction="""
        You are Jin Park (DOB 1978-11-02), email jin.park7284@northsoundsleep.org, a data scientist living with complex sleep apnea who relies on nightly ventilator telemetry uploads to keep in-network. You need the assistant to execute a high-rigor quality audit that crosses appointments, telemetry devices, and compliance logs:

        • Authenticate via your email (jin.park7284@northsoundsleep.org) to pull your profile and insurance plan so you know the compliance thresholds, then immediately fetch your sleep telemetry uploads for device VC-449 from 2025-06-01 through 2025-06-07. Flag any nights where the upload was missing or fell below 4 hours' usage, and note the device IDs involved.
        • Request the full telemetry inventory (limit 15) to see what machines are currently in circulation, then filter specifically to devices marked “maintenance” and “inspection” to see what’s stuck in QA. Your goal is to confirm that the Philips Trilogy ventilator with serial VC-449 (assigned to you) has a backup unit available; if none are showing as available, escalate via `transfer_to_human_support`.
        • Pull your June 2025 appointment roster and capture the statuses of your respiratory therapist check-in (APPT041), the compliance coaching call (APPT042), and the insurance audit call (APPT043). Log the meeting links before taking action.
        • The RT noted a discrepancy: the usage log didn’t sync on June 04. Retrieve medical record REC021 (sleep compliance note), review its observations, and use an explicit `think` step to outline the corrective plan.
        • You must copy the June 04 upload artifact into the record: call `get_telemetry_upload` for VC-449 on 2025-06-04, then embed the JSON payload into REC021 using `update_medical_record_note`. Use another `think` step afterward to summarize the compliance posture.
        • Next, reschedule APPT041 from June 10 2025 08:00 to June 12 2025 08:00 so it doesn’t collide with the insurer audit—and confirm there are no provider conflicts by pulling the updated appointment details.
        • Run a drug interaction check treating Xywav as the primary medication against (Xywav, Bupropion, Zolpidem) since your sleep specialist flagged a potential issue. If the severity is high, trigger a human handoff; otherwise, log that no high-severity issue is present.
        • Finally, generate a consolidated compliance roll-up: list your appointments again (all statuses) and re-fetch telemetry uploads for the June 01–07 window to ensure the record now includes the June 04 artifact.

        Keep your tone clinical and audit-focused.
        """,
        actions=[
            Action(name="find_patient_by_email", kwargs={"email": "jin.park7284@northsoundsleep.org"}),
            Action(name="get_patient_details", kwargs={"patient_id": "jin_park_7284"}),
            Action(name="list_telemetry_uploads", kwargs={"device_id": "VC-449", "start_date": "2025-06-01", "end_date": "2025-06-07"}),
            Action(name="list_telemetry_devices", kwargs={"limit": 15}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "maintenance"}),
            Action(name="list_telemetry_devices", kwargs={"status_filter": "inspection", "limit": 10}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "jin_park_7284"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT041"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT042"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT043"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC021"}),
            Action(name="think", kwargs={"note": "Outline corrective plan for REC021 discrepancy"}),
            Action(name="get_telemetry_upload", kwargs={"device_id": "VC-449", "date": "2025-06-04"}),
            Action(name="update_medical_record_note", kwargs={"record_id": "REC021", "note": "Embedded June 04 compliance artifact"}),
            Action(name="think", kwargs={"note": "Summarize compliance posture after artifact embed"}),
            Action(name="reschedule_appointment", kwargs={"appointment_id": "APPT041", "new_date": "2025-06-12", "new_time": "08:00"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT041"}),
            Action(name="check_drug_interactions", kwargs={"primary_medication": "Xywav", "current_medications": ["Xywav", "Bupropion", "Zolpidem"]}),
            Action(name="transfer_to_human_support", kwargs={"reason": "High-severity Xywav interaction"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "jin_park_7284"}),
            Action(name="list_telemetry_uploads", kwargs={"device_id": "VC-449", "start_date": "2025-06-01", "end_date": "2025-06-07"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="14",
        user_id="maya_chen_3318",
        instruction="""
        You are Lila Chen, mother of Maya Chen (DOB 2018-07-22), coordinating your daughter's complex autism therapy schedule. Maya has multiple providers and you need to ensure regulatory compliance, appointment clustering, and team coordination for her October 2025 care plan. Execute this multi-step coordination workflow:

        • Authenticate to access Maya's profile and verify insurance coverage thresholds. Capture her copay structure and current medication regimen.
        • Pull all of Maya's October 2025 appointments (should show 10 appointments across multiple providers). You need to audit the full roster, so call list_patient_appointments with ONLY the patient_id—do NOT add any status_filter parameter. This will show all scheduled and pending sessions including the critical pending team conference APPT049.
        • The Oregon licensing board requires you to verify each therapy provider's credentials before the quarterly audit. Fetch details for ALL four therapy providers involved in Maya's care: the developmental pediatrician (Dr. Okafor), the occupational therapist (OT Sullivan), the speech-language pathologist (SLP Martinez), and the behavioral analyst (BCBA Washington). For each, confirm they hold the required state license number and note their years of experience (Oregon mandates minimum 5 years for autism specialty providers).
        • Identify the pending team conference appointment (APPT049) and capture its current details—date, time, duration, and which provider is coordinating. This multi-disciplinary meeting requires all four providers to be present simultaneously.
        • Before approving the team conference, you need to check for scheduling conflicts. Pull the appointment details for at least 3 other appointments that week (Oct 21-24) to verify no provider has overlapping commitments. Focus on APPT050, APPT051, and APPT052.
        • Review Maya's most recent developmental assessment (REC022) and two recent therapy progress notes (REC023 from OT, REC024 from SLP) to understand current treatment goals. Use a `think` step to synthesize whether the therapy team's objectives are aligned and if any coordination gaps exist.
        • You notice the October 16 schedule is too compressed—OT at 09:00 (APPT045) and SLP at 10:30 (APPT046) leaves only 90 minutes between sessions, which doesn't work with Maya's sensory regulation needs. Reschedule APPT046 (the SLP session) to October 23 at 13:30 to give Maya more recovery time and cluster it near the afternoon block. Confirm the reschedule by pulling the updated appointment details.
        • Now that the conflict is resolved, list Maya's appointments again—call list_patient_appointments with ONLY patient_id, no status_filter—to see the complete updated October roster (all statuses) and confirm the team meeting (APPT049) doesn't overlap with any rescheduled sessions.
        • Fetch the BCBA's recent behavioral analysis note (REC025) to review Maya's social skills progress metrics. Use another `think` step to assess whether the team conference agenda should prioritize communication goals or behavioral strategies.
        • Finally, list all available providers in the "Behavioral Analysis" specialty to confirm BCBA Washington is the only analyst on Maya's team, ensuring continuity of care.

        Keep your tone organized and parent-advocate focused, emphasizing coordination and regulatory compliance.
        """,
        actions=[
            Action(name="find_patient_by_name_dob", kwargs={"first_name": "Maya", "last_name": "Chen", "date_of_birth": "2018-07-22"}),
            Action(name="get_patient_details", kwargs={"patient_id": "maya_chen_3318"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "maya_chen_3318"}),
            Action(name="get_provider_details", kwargs={"provider_id": "dr_okafor_developmental_pediatrics"}),
            Action(name="get_provider_details", kwargs={"provider_id": "ot_sullivan"}),
            Action(name="get_provider_details", kwargs={"provider_id": "slp_martinez"}),
            Action(name="get_provider_details", kwargs={"provider_id": "bcba_washington"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT049"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT050"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT051"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT052"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC022"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC023"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC024"}),
            Action(name="think", kwargs={"note": "Assess therapy team objective alignment and coordination gaps"}),
            Action(name="reschedule_appointment", kwargs={"appointment_id": "APPT046", "new_date": "2025-10-23", "new_time": "13:30"}),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT046"}),
            Action(name="list_patient_appointments", kwargs={"patient_id": "maya_chen_3318"}),
            Action(name="get_medical_record", kwargs={"record_id": "REC025"}),
            Action(name="think", kwargs={"note": "Assess team conference agenda priority: communication vs behavioral strategies"}),
            Action(name="list_available_providers", kwargs={"specialty": "Behavioral Analysis"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="15",
        user_id="omar_hassan_2156",
        instruction="""
        You are Omar Hassan, email omar.hassan2156@email.com.
        You need to review your surgical record REC026 from September 10, 2025, check what appointments you have, 
        and add a progress note. First, get medical record REC026. Then list your appointments. 
        Finally, add this note to record REC026: 
        "Patient reports pain level 3/10, improving mobility, able to walk without crutches for short distances."
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "omar.hassan2156@email.com"},
            ),
            Action(
                name="get_medical_record",
                kwargs={"record_id": "REC026"},
            ),
            Action(
                name="list_patient_appointments",
                kwargs={"patient_id": "omar_hassan_2156", "status_filter": "scheduled"},
            ),
            Action(
                name="update_medical_record_note",
                kwargs={
                    "record_id": "REC026",
                    "note": "Patient reports pain level 3/10, improving mobility, able to walk without crutches for short distances.",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="16",
        user_id="carlos_mendez_4521",
        instruction="""
        You are Carlos Mendez, email carlos.mendez4521@email.com.
        You need to review your recent medication records and reschedule an upcoming appointment.
        
        First, authenticate using your email. Then list your 3 most recent medical records (use limit=3).
        Next, get the full details of medical record REC027 to review your current medications.
        After that, check for drug interactions between Sertraline as the primary medication and your current medications: Sertraline, Ibuprofen, and Acetaminophen.
        Then reschedule appointment APPT056 from its current date/time to Friday October 17, 2025 at 14:00 (use date format 2025-10-17 and time format 14:00).
        Finally, get the appointment details for APPT056 to confirm the rescheduling was successful.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "carlos.mendez4521@email.com"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "carlos_mendez_4521", "limit": 3},
            ),
            Action(
                name="get_medical_record",
                kwargs={"record_id": "REC027"},
            ),
            Action(
                name="check_drug_interactions",
                kwargs={
                    "primary_medication": "Sertraline",
                    "current_medications": ["Sertraline", "Ibuprofen", "Acetaminophen"],
                },
            ),
            Action(
                name="reschedule_appointment",
                kwargs={
                    "appointment_id": "APPT056",
                    "new_date": "2025-10-17",
                    "new_time": "14:00",
                },
            ),
            Action(
                name="get_appointment_details",
                kwargs={"appointment_id": "APPT056"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="17",
        user_id="sarah_johnson_1234",
        instruction="""
        You are Sarah Johnson, email sarah.johnson@email.com.
        You need to optimize your medication regimen and calculate potential cost savings.
        
        First, authenticate using your email. Then get your patient details to verify your insurance information.
        Next, retrieve your medication regimen optimization options using get_regimen_options.
        Then calculate the monthly cost of your current regimen: (60 * 0.45) + (30 * 0.30).
        After that, calculate the monthly cost of the Cost-Optimized Generic regimen: (60 * 0.18) + (30 * 0.12).
        Then calculate the monthly savings by subtracting the optimized cost from the current cost.
        Next, check for drug interactions using Metformin as the primary medication against your current medications: Metformin and Lisinopril.
        Then reschedule appointment APPT057 to Friday October 24, 2025 at 10:00 (use date format 2025-10-24 and time format 10:00) to discuss the regimen change.
        Finally, get the appointment details for APPT057 to confirm the new time.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "sarah.johnson@email.com"},
            ),
            Action(
                name="get_patient_details",
                kwargs={"patient_id": "sarah_johnson_1234"},
            ),
            Action(
                name="get_regimen_options",
                kwargs={"patient_id": "sarah_johnson_1234"},
            ),
            Action(
                name="calculate",
                kwargs={"expression": "(60 * 0.45) + (30 * 0.30)"},
            ),
            Action(
                name="calculate",
                kwargs={"expression": "(60 * 0.18) + (30 * 0.12)"},
            ),
            Action(
                name="calculate",
                kwargs={"expression": "36.0 - 14.4"},
            ),
            Action(
                name="check_drug_interactions",
                kwargs={
                    "primary_medication": "Metformin",
                    "current_medications": ["Metformin", "Lisinopril"],
                },
            ),
            Action(
                name="reschedule_appointment",
                kwargs={
                    "appointment_id": "APPT057",
                    "new_date": "2025-10-24",
                    "new_time": "10:00",
                },
            ),
            Action(
                name="get_appointment_details",
                kwargs={"appointment_id": "APPT057"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="18",
        user_id="robert_martinez_5589",
        instruction="""
        You are Robert Martinez, email robert.martinez5589@email.com.
        You are preparing for cardiac surgery (CABG) and need to complete a pre-surgical checklist.
        
        First, authenticate using your email. Then list all your appointments to find your surgery appointment.
        Next, get the full details for appointment APPT058 to review the surgery information.
        After that, list all your medical records to find your recent evaluation.
        Then get the details of medical record REC028 to review your current medications.
        Next, check for drug interactions between Propofol (a common anesthetic) as the primary medication and your current medications: Atorvastatin, Metoprolol, Aspirin, and Metformin.
        Then list available telemetry devices with status available to verify post-operative monitoring equipment is ready.
        After that, search for available providers with specialty Anesthesiology and minimum 10 years of experience for your pre-op consultation.
        Next, schedule a pre-op anesthesia consultation appointment with provider dr_patel_anesthesiology on Friday November 7, 2025 at 10:00 (use date format 2025-11-07 and time format 10:00) with type pre_op_consultation.
        Then schedule a post-op follow-up appointment with provider dr_kim_cardiac_surgery on Monday November 24, 2025 at 09:00 (use date format 2025-11-24 and time format 09:00) with type follow_up.
        Next, calculate your total out-of-pocket costs for all three appointments: 500 + 250 + 350.
        Finally, add this note to medical record REC028: "Pre-surgical checklist completed. Anesthesia consultation scheduled, post-op follow-up scheduled, telemetry equipment verified available, drug interaction review completed."
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "robert.martinez5589@email.com"},
            ),
            Action(
                name="list_patient_appointments",
                kwargs={"patient_id": "robert_martinez_5589"},
            ),
            Action(
                name="get_appointment_details",
                kwargs={"appointment_id": "APPT058"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "robert_martinez_5589"},
            ),
            Action(
                name="get_medical_record",
                kwargs={"record_id": "REC028"},
            ),
            Action(
                name="check_drug_interactions",
                kwargs={
                    "primary_medication": "Propofol",
                    "current_medications": ["Atorvastatin", "Metoprolol", "Aspirin", "Metformin"],
                },
            ),
            Action(
                name="list_telemetry_devices",
                kwargs={"status_filter": "available"},
            ),
            Action(
                name="list_available_providers",
                kwargs={"specialty": "Anesthesiology", "min_years_experience": 10},
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "robert_martinez_5589",
                    "provider_id": "dr_patel_anesthesiology",
                    "date": "2025-11-07",
                    "time": "10:00",
                    "appointment_type": "pre_op_consultation",
                },
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "robert_martinez_5589",
                    "provider_id": "dr_kim_cardiac_surgery",
                    "date": "2025-11-24",
                    "time": "09:00",
                    "appointment_type": "follow_up",
                },
            ),
            Action(
                name="calculate",
                kwargs={"expression": "500 + 250 + 350"},
            ),
            Action(
                name="update_medical_record_note",
                kwargs={
                    "record_id": "REC028",
                    "note": "Pre-surgical checklist completed. Anesthesia consultation scheduled, post-op follow-up scheduled, telemetry equipment verified available, drug interaction review completed.",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="19",
        user_id="patricia_wong_6634",
        instruction="""
        You are Patricia Wong, email patricia.wong6634@email.com.
        You need to optimize your medication costs by switching to cheaper suppliers for your chronic disease medications.
        
        First, authenticate using your email. Then list all your medical records.
        Next, get the details of medical record REC029 to review your current prescriptions.
        Then list all available medication suppliers for Lisinopril to find cheaper options.
        After that, update the Lisinopril prescription in record REC029 to use the cheapest supplier (Mumbai Cardio Pharma, brand Lisipril-M, price 2.80).
        Next, list all available medication suppliers for Rosuvastatin to find cheaper options.
        Then update the Rosuvastatin prescription in record REC029 to use the cheapest supplier (Aurora Heart Labs, brand RosuPrime, price 5.95).
        After that, calculate your monthly savings: 14.70 - 8.75.
        Then get the provider details for dr_garcia_primary to verify availability.
        Finally, schedule a follow-up appointment with provider dr_garcia_primary on Tuesday December 16, 2025 at 09:00 (use date format 2025-12-16 and time format 09:00) with type follow_up.
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "patricia.wong6634@email.com"},
            ),
            Action(
                name="list_patient_medical_records",
                kwargs={"patient_id": "patricia_wong_6634"},
            ),
            Action(
                name="get_medical_record",
                kwargs={"record_id": "REC029"},
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Lisinopril"},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC029",
                    "medication": "Lisinopril",
                    "supplier_company": "Mumbai Cardio Pharma",
                    "brand_name": "Lisipril-M",
                    "price_usd": 2.80,
                },
            ),
            Action(
                name="list_medication_suppliers",
                kwargs={"medication": "Rosuvastatin"},
            ),
            Action(
                name="update_prescription_supplier",
                kwargs={
                    "record_id": "REC029",
                    "medication": "Rosuvastatin",
                    "supplier_company": "Aurora Heart Labs",
                    "brand_name": "RosuPrime",
                    "price_usd": 5.95,
                },
            ),
            Action(
                name="calculate",
                kwargs={"expression": "14.70 - 8.75"},
            ),
            Action(
                name="get_provider_details",
                kwargs={"provider_id": "dr_garcia_primary"},
            ),
            Action(
                name="schedule_appointment",
                kwargs={
                    "patient_id": "patricia_wong_6634",
                    "provider_id": "dr_garcia_primary",
                    "date": "2025-12-16",
                    "time": "09:00",
                    "appointment_type": "follow_up",
                },
            ),
        ],
        outputs=[],
    ),
]
