schema_description = {
    "ProductGroup": ["name"],
    "Manufacturer": ["name"],
    "Model": ["name", "series"],
    "Component": ["name"],
    "Problem": ["name"],
    "AdditionalInfo": ["name"],
    "Procedures": ["name"],
    "BasicInfo": ["name"],
    "SubComponent": ["name"],
    "SuspectArea": ["name"],
    "Symptom": ["name"],
    "TestProcedures": ["name"]
}
vector_index_names = {
    label: f"vectorIndex_{label}" for label in schema_description
}

fulltext_index_names = {
    label: f"search_{label}" for label in schema_description
}


tag_to_label_map =  {
    "AdditionalInfo": ["additional_info", "junction_block", "maintenance", "parts", "parts_location", "precaution",
                       "repair_instruction"],
    "Procedures": ["adjustment_procedure", "information_on_adjustment", "information_on_removal_procedure",
                   "information_on_replacement", "information_on_suspect_area", "inspection_procedure", "installation",
                   "installation_info", "installation_procedure", "installation_procedures", "installation_step",
                   "installation_steps", "map_light", "mirror", "preparation", "procedures", "reassembly",
                   "reassembly_procedure", "reassembly_procedures", "removal_procedure", "repair", "room_light"],
    "BasicInfo": ["car", "car_details", "car_info", "car_information", "car_model", "communication_system",
                  "engine_type", "identification_information", "introduction", "manufacture", "manufacturer", "model",
                  "model_number", "type", "vehicle_details", "vehicle_info", "vehicle_information"],
    "SubComponent": ["component", "components", "control_system", "engine_hood_door", "issue", "lock_system",
                     "manual_transaxle", "power_system", "procedure", "radio", "relay_blocks", "security_system",
                     "sound_quality", "theft_deterrent_system", "transaxle_service", "vehicle"],
    "Problem": ["problem"],
    "SuspectArea": ["suspect_area", "suspect_area_info", "suspect_areas"],
    "Symptom": ["symptom", "symptoms"],
    "TestProcedures": ["test", "tests", "tests_and_procedure", "tests_and_procedures", "tests_procedure",
                       "tests_procedures"]
}

default_prompt = (
    "You are a vehicle repair expert. "
    "Based on the context, answer the user query accurately and concisely."
)
