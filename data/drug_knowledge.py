"""Structured drug interaction and contraindication knowledge base."""

# (drug_a, drug_b) → clinical warning (curated from FDA labels and clinical references)
INTERACTION_DB = {
    ("warfarin", "aspirin"): "Increased bleeding risk — avoid combination or monitor INR closely.",
    ("warfarin", "ibuprofen"): "Increased bleeding risk — NSAIDs inhibit platelet function.",
    ("ace_inhibitor", "potassium_supplement"): "Risk of hyperkalemia — monitor serum potassium.",
    ("ace_inhibitor", "spironolactone"): "Risk of hyperkalemia — monitor potassium and renal function.",
    ("statin", "fibrate"): "Risk of myopathy/rhabdomyolysis — use with caution.",
    ("beta_blocker", "verapamil"): "Severe bradycardia and AV block risk — avoid combination.",
    ("beta_blocker", "diltiazem"): "Additive negative chronotropic effects — monitor heart rate.",
    ("thiazide", "lithium"): "Thiazides reduce lithium clearance — risk of lithium toxicity.",
    ("ssri", "tramadol"): "Serotonin syndrome risk — avoid combination.",
    ("metformin", "contrast_dye"): "Risk of lactic acidosis — hold metformin before contrast studies.",
    ("nsaid", "ace_inhibitor"): "NSAIDs reduce antihypertensive effect and worsen renal function.",
    ("digoxin", "amiodarone"): "Increased digoxin levels — reduce digoxin dose and monitor.",
}

# condition → medications to avoid
CONTRAINDICATION_DB = {
    "hyperkalemia": ["ace_inhibitor", "arb", "potassium_supplement", "spironolactone"],
    "bilateral_renal_artery_stenosis": ["ace_inhibitor", "arb"],
    "asthma": ["beta_blocker", "nsaid"],
    "gout": ["thiazide"],
    "pregnancy": ["ace_inhibitor", "arb", "statin", "warfarin"],
    "liver_disease": ["statin"],
    "bradycardia": ["beta_blocker", "verapamil", "diltiazem"],
    "ckd": ["nsaid"],
    "heart_failure": ["nsaid", "diltiazem"],
}

# Drug name aliases for normalization
DRUG_ALIASES = {
    "lisinopril": "ace_inhibitor",
    "enalapril": "ace_inhibitor",
    "ramipril": "ace_inhibitor",
    "losartan": "arb",
    "valsartan": "arb",
    "atorvastatin": "statin",
    "simvastatin": "statin",
    "rosuvastatin": "statin",
    "metoprolol": "beta_blocker",
    "atenolol": "beta_blocker",
    "carvedilol": "beta_blocker",
    "hydrochlorothiazide": "thiazide",
    "hctz": "thiazide",
    "coumadin": "warfarin",
    "jantoven": "warfarin",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "tylenol": "acetaminophen",
}
