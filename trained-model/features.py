import pandas as pd
import numpy as np
import re


def _first_column(df, *candidates):
    return next((name for name in candidates if name in df.columns), candidates[-1])


def extract_features(df_stays):
    df = df_stays.copy()

    # 1. Prior Intake Count (conteggio ingressi precedenti dello stesso animale)
    df['prior_intake_count'] = df.groupby('animal_id').cumcount()

    # 2. Has Name (Se presente e non è un codice di default)
    name_col = 'name_intake' if 'name_intake' in df.columns else 'name'
    if name_col in df.columns:
        name_values = df[name_col].astype(str).str.lower()
        is_named = ~name_values.str.contains(
            r'unknown|mix|\*|noname',
            na=True,
            regex=True,
        )
        df['has_name'] = df[name_col].notna() & is_named
    else:
        df['has_name'] = 0
    df['has_name'] = df['has_name'].astype(int)

    # 3. Age Band
    # Convertiamo l'età in giorni
    def local_parse_age(age_str):
        if pd.isna(age_str):
            return np.nan
        age_str = str(age_str).lower().strip()
        pattern = r'(\d+)\s*(year|month|week|day)'
        match = re.search(pattern, age_str)
        if not match:
            return np.nan
        val = int(match.group(1))
        unit = match.group(2)
        if 'year' in unit:
            return val * 365.25
        if 'month' in unit:
            return val * 30.4
        if 'week' in unit:
            return val * 7
        return val

    age_col = 'age_upon_intake_intake' if 'age_upon_intake_intake' in df.columns else 'age_upon_intake'
    df['age_days_at_intake'] = df[age_col].apply(local_parse_age)
    df['age_months_at_intake'] = df['age_days_at_intake'] / 30.4

    def get_age_band(m):
        if pd.isna(m):
            return 'Unknown'
        if m < 6:
            return 'puppy_kitten'
        if m < 24:
            return 'young'
        if m < 96:
            return 'adult'
        return 'senior'

    df['age_band'] = df['age_months_at_intake'].apply(get_age_band)

    # 4. Is Mixed (Se contiene Mix o il carattere '/')
    breed_col = _first_column(df, 'breed_intake_intake', 'breed_intake', 'breed')
    df['breed_clean'] = df[breed_col].fillna('Unknown').astype(str).str.strip()
    df['is_mixed'] = df['breed_clean'].str.contains('Mix|/', case=False, regex=True).astype(int)

    # 5. Is Black
    color_col = _first_column(df, 'color_intake_intake', 'color_intake', 'color')
    df['color_clean'] = df[color_col].fillna('Unknown').astype(str).str.lower()
    df['is_black'] = df['color_clean'].str.contains('black', na=False).astype(int)

    # 6. Sesso e stato di sterilizzazione
    def split_sex(sex_str):
        if pd.isna(sex_str) or 'unknown' in str(sex_str).lower():
            return 'Unknown', 0
        s = str(sex_str).strip()
        gender = 'Male' if 'Male' in s else 'Female'
        sterilized = 1 if ('Neutered' in s or 'Spayed' in s) else 0
        return gender, sterilized

    sex_col = 'sex_upon_intake_intake' if 'sex_upon_intake_intake' in df.columns else 'sex_upon_intake'
    gender_and_steril = df[sex_col].apply(split_sex)
    df['sex'] = [x[0] for x in gender_and_steril]
    df['sterilized_at_intake'] = [x[1] for x in gender_and_steril]

    # Selezioniamo le feature finali utili per i modelli
    animal_type_col = _first_column(
        df,
        'animal_type_intake_intake',
        'animal_type_intake',
        'animal_type',
    )
    df['animal_type_intake'] = df[animal_type_col]

    feature_cols = [
        'animal_type_intake', 'sex', 'sterilized_at_intake',
        'age_months_at_intake', 'age_band', 'is_mixed',
        'intake_type', 'intake_condition', 'prior_intake_count',
        'has_name', 'is_black', 'duration_days', 'event_type'
    ]

    # Gestiamo eventuali valori nulli inserendo la mediana/valori di default
    default_age = df['age_months_at_intake'].median() if len(df) > 0 else 12.0
    df['age_months_at_intake'] = df['age_months_at_intake'].fillna(default_age)

    return df[feature_cols]
