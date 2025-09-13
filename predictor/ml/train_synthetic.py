# train_synthetic.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

np.random.seed(42)

def gen_students(n=2000):
    courses = ['Engineering', 'Commerce', 'Health', 'Education', 'ICT']
    student = []
    for i in range(n):
        gpa = np.round(np.clip(np.random.normal(3.0, 0.6), 0.0, 4.0), 2)
        need = np.round(np.clip(np.random.beta(2,5), 0.0, 1.0), 3)
        course = np.random.choice(courses, p=[0.25, 0.25, 0.2, 0.15, 0.15])
        province = np.random.choice(['Gauteng','Western Cape','Limpopo','KwaZulu-Natal','Eastern Cape'])
        student.append({'gpa': gpa, 'need_score': need, 'course': course, 'province': province})
    return pd.DataFrame(student)

def gen_donors(n=300):
    courses = ['Engineering', 'Commerce', 'Health', 'Education', 'ICT', 'Any']
    donor = []
    for i in range(n):
        donor_type = np.random.choice(['alumni','corporate','ngo'], p=[0.6,0.25,0.15])
        preferred_course = np.random.choice(courses, p=[0.2,0.2,0.15,0.15,0.15,0.15])
        min_gpa = np.round(np.random.uniform(0,3.0),2)
        max_amount = np.random.choice([500,1000,2000,5000,10000])
        donor.append({'donor_type': donor_type, 'preferred_course': preferred_course, 'min_gpa':min_gpa, 'max_amount': max_amount})
    return pd.DataFrame(donor)

def make_pairs(students, donors, n_pairs=20000):
    rows=[]
    for _ in range(n_pairs):
        s = students.sample(1).iloc[0]
        d = donors.sample(1).iloc[0]
        # compute heuristic "true" likelihood and label
        score = 0.0
        if (d['preferred_course']=='Any') or (d['preferred_course']==s['course']):
            score += 0.4
        # donors prefer higher GPA
        score += 0.3 * (s['gpa'] / 4.0)
        # donors prefer some need but not extreme? we'll give weight to need
        score += 0.3 * s['need_score']
        # incorporate donor min_gpa (if student below, lower probability)
        if s['gpa'] < d['min_gpa']:
            score *= 0.4
        prob = score
        label = 1 if np.random.rand() < prob else 0
        rows.append({
            'gpa': s['gpa'],
            'need_score': s['need_score'],
            'course': s['course'],
            'donor_type': d['donor_type'],
            'preferred_course': d['preferred_course'],
            'min_gpa': d['min_gpa'],
            'max_amount': d['max_amount'],
            'label': label
        })
    return pd.DataFrame(rows)

def fe(df):
    # one-hot encode course and donor types and preferred_course
    df2 = pd.get_dummies(df, columns=['course','donor_type','preferred_course'], drop_first=True)
    return df2

def main():
    students = gen_students(1000)
    donors = gen_donors(200)
    pairs = make_pairs(students, donors, n_pairs=10000)
    X = fe(pairs.drop(columns=['label']))
    y = pairs['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2)
    model = RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    print("Train score:", model.score(X_train, y_train))
    print("Test score:", model.score(X_test, y_test))
    os.makedirs('predictor/models', exist_ok=True)
    joblib.dump({'model': model, 'columns': X.columns.tolist()}, 'predictor/models/matching_model.joblib')
    print("Model saved to predictor/models/matching_model.joblib")

if __name__ == '__main__':
    main()
