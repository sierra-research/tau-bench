# Mock Data Generation

## Current Mock Data for the Telehealth Benchmark
Feel free to use some of the data for other purposes.
- `patients.json`: a database of patients with their demographics, medical history, and insurance information
- `providers.json`: a database of healthcare providers, their specialties, schedules, and availability
- `appointments.json`: a database of telehealth appointments that can be scheduled, modified, or cancelled
- `medical_records.json`: a database of consultation notes, prescriptions, and test results

Check `../tools` for mock APIs on top of current mock data.

### Experience of Mock Data Generation

Read our paper to learn more about the generation process for each database. In general, it involves the following stages:

1. Design the type and schema of each database. Can use GPT for co-brainstorming but has to be human decided as it is the foundation of everything else.
2. For each schema, figure out which parts can be programmaticly generated and which parts need GPT. For example,
    - Provider specialties (cardiology, dermatology, psychiatry) and patient names (Sara, John, Noah) need GPT generation
    - Appointment times and insurance copays can be generated via code
3. Use GPT to generate seed data (first names, last names, addresses, cities, medical conditions, etc.), then use a program to compose them with other code generated data. Can use GPT to help write the code for this part, but I think code-based database construction is more reliable than GPT-based database construction (e.g., give some example patient profiles and ask GPT to generate more --- issues with diversity and reliability).