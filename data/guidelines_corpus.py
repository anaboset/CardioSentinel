"""Curated cardiovascular guideline corpus for semantic retrieval."""

GUIDELINE_CORPUS = [
    {
        "id": "htn_001",
        "condition": "hypertension",
        "topic": "first-line therapy",
        "text": (
            "First-line therapy for hypertension: ACE inhibitors or ARBs are preferred "
            "for patients with diabetes or CKD. Thiazide diuretics are recommended as "
            "first-line for uncomplicated hypertension. Target BP < 130/80 mmHg for "
            "high-risk patients per ACC/AHA 2023 guidelines."
        ),
        "source": "ACC/AHA 2023 Hypertension Guidelines",
    },
    {
        "id": "htn_002",
        "condition": "hypertension",
        "topic": "beta blockers",
        "text": (
            "Beta-blockers are preferred when concurrent ischemic heart disease is present. "
            "Combination therapy may be required if BP remains above target after "
            "monotherapy. Lifestyle modification including DASH diet and sodium restriction "
            "is recommended as adjunct."
        ),
        "source": "JNC 8 Evidence-Based Guideline",
    },
    {
        "id": "htn_003",
        "condition": "hypertension",
        "topic": "elderly patients",
        "text": (
            "In patients ≥65 years with hypertension, target SBP < 130 mmHg if tolerated. "
            "Start low and go slow with antihypertensive titration. Monitor for orthostatic "
            "hypotension and renal function with ACE inhibitors/ARBs."
        ),
        "source": "ESC/ESH 2023 Arterial Hypertension Guidelines",
    },
    {
        "id": "dys_001",
        "condition": "dyslipidemia",
        "topic": "statin therapy",
        "text": (
            "High-intensity statin therapy is indicated for LDL > 190 mg/dL or ASCVD risk > 20%. "
            "LDL target < 70 mg/dL for very high cardiovascular risk patients. "
            "Lifestyle modification (Mediterranean diet + aerobic exercise) as adjunct."
        ),
        "source": "ACC/AHA 2022 Cholesterol Guidelines",
    },
    {
        "id": "dys_002",
        "condition": "dyslipidemia",
        "topic": "secondary prevention",
        "text": (
            "For secondary prevention in established ASCVD, maximally tolerated statin therapy "
            "is recommended. Consider ezetimibe or PCSK9 inhibitor if LDL remains above target "
            "despite statin therapy."
        ),
        "source": "ESC/EAS 2023 Dyslipidaemia Guidelines",
    },
    {
        "id": "smk_001",
        "condition": "smoker",
        "topic": "smoking cessation",
        "text": (
            "Smoking cessation counseling is mandatory for all smokers. "
            "NRT (nicotine replacement therapy) or varenicline as pharmacotherapy. "
            "Smoking doubles cardiovascular risk — cessation is the highest-yield intervention."
        ),
        "source": "USPSTF Tobacco Cessation Guidelines 2021",
    },
    {
        "id": "smk_002",
        "condition": "smoker",
        "topic": "cardiovascular risk",
        "text": (
            "Active smoking is a major modifiable cardiovascular risk factor. "
            "Within 1 year of cessation, coronary heart disease risk drops by 50%. "
            "Combine behavioral counseling with pharmacotherapy for best outcomes."
        ),
        "source": "ACC/AHA 2023 Primary Prevention Guidelines",
    },
    {
        "id": "dm_001",
        "condition": "diabetes",
        "topic": "cardiovascular protection",
        "text": (
            "In diabetes with cardiovascular disease, SGLT2 inhibitors or GLP-1 receptor "
            "agonists with proven CV benefit are recommended. Target HbA1c < 7% for most "
            "adults. BP target < 130/80 mmHg and statin therapy for age ≥40."
        ),
        "source": "ADA Standards of Care 2024",
    },
    {
        "id": "ckd_001",
        "condition": "ckd",
        "topic": "blood pressure management",
        "text": (
            "In CKD, target BP < 130/80 mmHg. ACE inhibitors or ARBs are first-line "
            "to reduce proteinuria and slow progression. Monitor potassium and creatinine "
            "within 2 weeks of initiation or dose change."
        ),
        "source": "KDIGO 2021 Blood Pressure Guidelines",
    },
    {
        "id": "cad_001",
        "condition": "coronary_artery_disease",
        "topic": "secondary prevention",
        "text": (
            "Secondary prevention for CAD: dual antiplatelet therapy post-ACS, high-intensity "
            "statin, beta-blocker, ACE inhibitor, and lifestyle modification. "
            "Cardiac rehabilitation is strongly recommended."
        ),
        "source": "ACC/AHA 2023 Chronic Coronary Disease Guidelines",
    },
]
