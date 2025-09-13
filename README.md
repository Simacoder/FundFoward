# AI-Powered Micro-Bursaries for Student Banking

[How the app works Demo](https://drive.google.com/file/d/164wOa8xzqG_2N51M5ujVqO7b2GTOsc5X/view?usp=sharing)
[Live Demo](https://nodumehlezi.pythonanywhere.com/)

## 📌 Problem Statement

In South Africa, **over 60% of the population lives below the poverty line** ([World Bank, 2022](https://www.worldbank.org/en/country/southafrica/overview)). This socio-economic reality directly impacts access to higher education.

Every year, thousands of students face a **registration crisis**: they cannot pay the upfront registration fees required to secure a place at university. This leads to:

* Long queues at campuses as students appeal for fee exemptions.
* Stress and uncertainty for students and their families.
* Administrative burden for tertiary institutions, who face protests and delays.
* Donors and funding bodies struggling with late applications, unclear priorities, and bottlenecks in distributing aid.

Financial exclusion remains a leading cause of **student dropout**, with delayed funding from schemes like NSFAS leaving many unable to continue studies.

---

## 🚀  Factor

Imagine a seamless registration season where:

* Students apply online for help with **registration fees** and are instantly matched with donors.
* Donors (alumni, corporates, NGOs) receive **AI-curated student profiles** and can fund students in real time.
* Universities drastically **reduce queues, protests, and admin stress**.
* Students start the semester without financial anxiety, focusing on academics.

This transforms registration from **chaos into a data-driven, AI-powered funding ecosystem**.

---

## 💡 Proposed Solution

We are building an **AI-driven micro-bursary and peer-to-peer funding platform**, integrated with a **student banking system**.

* **Students** register with academic, socio-economic, and course details.
* They can request **specific support for registration fees, tuition, or living costs**.
* **Donors/alumni/corporates** set funding preferences (field of study, GPA thresholds, type of support).
* **AI algorithms** match students with donors based on financial need, academic trajectory, and donor intent.
* Funds are **disbursed instantly** into student bank accounts, ensuring they can register and stay enrolled.

---

## 📊 Actionable Insights

* Early detection of **students at risk of missing registration** due to unpaid fees.
* AI identifies **donor-student alignment**, increasing donor satisfaction and impact.
* Universities gain **predictive insights** into registration bottlenecks.
* Students access **financial literacy tools** via their digital bank account.

---

## 🧠 Novel Innovation

* **AI-Powered Matching Engine** – Matches donors to students at the exact point of need.
* **Micro-Bursary Model** – Splits donor contributions into **bite-sized bursaries** to clear registration blocks.
* **Registration Fee Priority Feature** – Fast-tracks urgent cases to prevent dropouts.
* **Digital Queue Reduction** – Automates bursary allocation, reducing campus queues and protests.
* **Impact Dashboards** – Real-time donor impact tracking.
* **Financial Wellbeing Layer** – Budgeting and savings tools for students.

---

## 🏗️ System Architecture

* **Django Backend** – Handles authentication, bursary requests, donor profiles, and AI match logic.
* **Machine Learning Layer** – A trained model (Random Forest / Recommendation System) predicts donor-student matching scores.
* **REST API** – Exposes matching scores, bursary status, registration alerts, and transaction history.
* **Frontend** – HTML/CSS templates with:

  * Student dashboard (apply for bursaries, see match score)
  * Donor dashboard (view students, fund with 1 click, view impact dashboard)
  * Wallet simulation (mock transactions, disbursement updates)
  * Academic record uploads and registration status flags

---

## ⚙️ Features

* ✅ Student & donor registration
* ✅ Bursary request creation
* ✅ AI-powered donor-student matching
* ✅ Donor funding (mock payments)
* ✅ Academic record upload
* ✅ Real-time queue reduction insights for universities
* ✅ Alerts for at-risk students

---

## 🛠️ Tech Stack

* **Backend:** Django, Django REST Framework
* **ML Model:** Scikit-learn (RandomForest / Logistic Regression)
* **Database:** SQLite (can scale to PostgreSQL)
* **Frontend:** HTML, CSS, JS (Bootstrap or Tailwind)
* **Payments:** Mock payment API integration

---

## 🏃 Getting Started

1. **Clone the repo**

```bash
git clone https://github.com/Simacoder/FundForward.git
cd FundForward
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run migrations & server**

```bash
python manage.py migrate
python manage.py runserver
```


4. **Access app:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📢 Future Roadmap

* ✅ Mobile app for students
* ✅ Integration with real payment gateways
* ✅ Machine Learning model optimization with real data
* ✅ Predictive dropout alerts for university admins

---

## 📜 License

MIT License – free to use, modify, and distribute.

# AUTHOR
- Simanga Mchunu
- Yusairah Ismail
- Patience Mabuza
- Nkosinathi Nhlapo