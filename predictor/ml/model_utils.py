import joblib
import pandas as pd
import os


MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'matching_model.joblib')


class Matcher:
	def __init__(self):
		data = joblib.load(MODEL_PATH)
		self.model = data['model']
		self.columns = data['columns']

	def prepare(self, student, donor):
		row = {
			'gpa': student.get('gpa', 0.0),
			'need_score': student.get('need_score', 0.0),
			'course': student.get('course', 'Unknown'),
			'donor_type': donor.get('donor_type','alumni'),
			'preferred_course': donor.get('preferred_course','Any'),
			'min_gpa': donor.get('min_gpa', 0.0),
			'max_amount': donor.get('max_amount', 0.0),
		}
		df = pd.DataFrame([row])
		df = pd.get_dummies(df)
		for c in self.columns:
			if c not in df.columns:
				df[c] = 0
		df = df[self.columns]
		return df

	def score(self, student, donor):
		X = self.prepare(student, donor)
		proba = self.model.predict_proba(X)[0][1]
		return float(proba)