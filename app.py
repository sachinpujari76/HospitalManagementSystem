from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)

# ==========================================
# SESSION SECRET KEY
# ==========================================

app.secret_key = "hospital-management-secret-key"


# ==========================================
# MYSQL CONNECTION
# ==========================================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sani@9276",
        database="hospital_db"
    )


# ==========================================
# LOGIN
# ==========================================

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username = %s AND password = %s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:

            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        else:

            return render_template(
                "login.html",
                error="Invalid username or password"
            )

    return render_template("login.html")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------
    # TOTAL PATIENTS
    # --------------------------------------

    cursor.execute(
        "SELECT COUNT(*) AS total FROM patients"
    )

    total_patients = cursor.fetchone()["total"]

    # --------------------------------------
    # TOTAL DOCTORS
    # --------------------------------------

    cursor.execute(
        "SELECT COUNT(*) AS total FROM doctors"
    )

    total_doctors = cursor.fetchone()["total"]

    # --------------------------------------
    # TOTAL APPOINTMENTS
    # --------------------------------------

    cursor.execute(
        "SELECT COUNT(*) AS total FROM appointments"
    )

    total_appointments = cursor.fetchone()["total"]

    # --------------------------------------
    # TODAY'S APPOINTMENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE appointment_date = CURDATE()
        """
    )

    appointments_today = cursor.fetchone()["total"]

    # --------------------------------------
    # TOTAL BILLING
    # --------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM bills
        """
    )

    total_billing = cursor.fetchone()["total"]

    # --------------------------------------
    # RECENT APPOINTMENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT
            a.id,
            a.appointment_date,
            a.appointment_time,
            a.status,
            p.patient_name,
            d.doctor_name
        FROM appointments a

        LEFT JOIN patients p
            ON a.patient_id = p.id

        LEFT JOIN doctors d
            ON a.doctor_id = d.id

        ORDER BY a.id DESC

        LIMIT 5
        """
    )

    recent_appointments = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        appointments_today=appointments_today,
        total_billing=total_billing,
        recent_appointments=recent_appointments
    )


# ==========================================
# PATIENT MANAGEMENT
# ==========================================

@app.route("/patients", methods=["GET", "POST"])
def patients():

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------
    # ADD PATIENT
    # --------------------------------------

    if request.method == "POST":

        patient_name = request.form.get("patient_name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        email = request.form.get("email")
        blood_group = request.form.get("blood_group")
        disease = request.form.get("disease")
        address = request.form.get("address")

        cursor.execute(
            """
            INSERT INTO patients
            (
                patient_name,
                age,
                gender,
                phone,
                email,
                blood_group,
                disease,
                address
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_name,
                age,
                gender,
                phone,
                email,
                blood_group,
                disease,
                address
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("patients"))

    # --------------------------------------
    # GET PATIENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM patients
        ORDER BY id DESC
        """
    )

    patients_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "patients.html",
        patients=patients_data
    )



# ==========================================
# EDIT PATIENT
# ==========================================

@app.route("/edit-patient/<int:id>", methods=["GET", "POST"])
def edit_patient(id):

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        patient_name = request.form.get("patient_name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        email = request.form.get("email")
        blood_group = request.form.get("blood_group")
        disease = request.form.get("disease")
        address = request.form.get("address")

        cursor.execute(
            """
            UPDATE patients
            SET
                patient_name = %s,
                age = %s,
                gender = %s,
                phone = %s,
                email = %s,
                blood_group = %s,
                disease = %s,
                address = %s
            WHERE id = %s
            """,
            (
                patient_name,
                age,
                gender,
                phone,
                email,
                blood_group,
                disease,
                address,
                id
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("patients"))

    cursor.execute(
        """
        SELECT *
        FROM patients
        WHERE id = %s
        """,
        (id,)
    )

    patient = cursor.fetchone()

    cursor.close()
    db.close()

    if patient is None:
        return redirect(url_for("patients"))

    return render_template(
        "edit_patient.html",
        patient=patient
    )



# ==========================================
# DELETE PATIENT
# ==========================================

@app.route("/delete-patient/<int:id>")
def delete_patient(id):

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM patients
            WHERE id = %s
            """,
            (id,)
        )

        db.commit()

    except mysql.connector.Error as error:
        db.rollback()
        print("Error deleting patient:", error)

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("patients"))


# ==========================================
# DOCTOR MANAGEMENT
# ==========================================

@app.route("/doctors", methods=["GET", "POST"])
def doctors():

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------
    # ADD DOCTOR
    # --------------------------------------

    if request.method == "POST":

        doctor_name = request.form.get("doctor_name")
        specialization = request.form.get("specialization")
        phone = request.form.get("phone")
        email = request.form.get("email")
        experience = request.form.get("experience")
        available_time = request.form.get("available_time")
        consultation_fee = request.form.get("consultation_fee")

        cursor.execute(
            """
            INSERT INTO doctors
            (
                doctor_name,
                specialization,
                phone,
                email,
                experience,
                available_time,
                consultation_fee
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                doctor_name,
                specialization,
                phone,
                email,
                experience,
                available_time,
                consultation_fee
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("doctors"))

    # --------------------------------------
    # GET DOCTORS
    # --------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM doctors
        ORDER BY id DESC
        """
    )

    doctors_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "doctors.html",
        doctors=doctors_data
    )


# ==========================================
# APPOINTMENT MANAGEMENT
# ==========================================

@app.route("/appointments", methods=["GET", "POST"])
def appointments():

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------
    # ADD APPOINTMENT
    # --------------------------------------

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")
        status = request.form.get("status")

        cursor.execute(
            """
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                status
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("appointments"))

    # --------------------------------------
    # GET PATIENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT id, patient_name
        FROM patients
        ORDER BY patient_name ASC
        """
    )

    patients_data = cursor.fetchall()

    # --------------------------------------
    # GET DOCTORS
    # --------------------------------------

    cursor.execute(
        """
        SELECT id, doctor_name, specialization
        FROM doctors
        ORDER BY doctor_name ASC
        """
    )

    doctors_data = cursor.fetchall()

    # --------------------------------------
    # GET APPOINTMENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT
            a.id,
            a.appointment_date,
            a.appointment_time,
            a.status,
            p.patient_name,
            d.doctor_name,
            d.specialization
        FROM appointments a
        LEFT JOIN patients p
            ON a.patient_id = p.id
        LEFT JOIN doctors d
            ON a.doctor_id = d.id
        ORDER BY a.id DESC
        """
    )

    appointments_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "appointments.html",
        patients=patients_data,
        doctors=doctors_data,
        appointments=appointments_data
    )


# ==========================================
# DELETE APPOINTMENT
# ==========================================

@app.route("/delete-appointment/<int:id>")
def delete_appointment(id):

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM appointments
        WHERE id = %s
        """,
        (id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("appointments"))


# ==========================================
# UPDATE APPOINTMENT STATUS
# ==========================================

@app.route("/update-appointment-status/<int:id>", methods=["POST"])
def update_appointment_status(id):

    if "username" not in session:
        return redirect(url_for("home"))

    status = request.form.get("status")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET status = %s
        WHERE id = %s
        """,
        (status, id)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("appointments"))


# ==========================================
# BILLING MANAGEMENT
# ==========================================

@app.route("/billing", methods=["GET", "POST"])
def billing():

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------
    # CREATE BILL
    # --------------------------------------

    if request.method == "POST":

        patient_id = request.form.get("patient_id")

        consultation_fee = float(
            request.form.get("consultation_fee") or 0
        )

        room_charges = float(
            request.form.get("room_charges") or 0
        )

        medicine_charges = float(
            request.form.get("medicine_charges") or 0
        )

        other_charges = float(
            request.form.get("other_charges") or 0
        )

        payment_status = request.form.get("payment_status")

        # Calculate total

        total_amount = (
            consultation_fee
            + room_charges
            + medicine_charges
            + other_charges
        )

        cursor.execute(
            """
            INSERT INTO bills
            (
                patient_id,
                consultation_fee,
                room_charges,
                medicine_charges,
                other_charges,
                total_amount,
                payment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                consultation_fee,
                room_charges,
                medicine_charges,
                other_charges,
                total_amount,
                payment_status
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("billing"))

    # --------------------------------------
    # GET PATIENTS
    # --------------------------------------

    cursor.execute(
        """
        SELECT id, patient_name
        FROM patients
        ORDER BY patient_name ASC
        """
    )

    patients_data = cursor.fetchall()

    # --------------------------------------
    # GET BILLS
    # --------------------------------------

    cursor.execute(
        """
        SELECT
            b.id,
            b.consultation_fee,
            b.room_charges,
            b.medicine_charges,
            b.other_charges,
            b.total_amount,
            b.payment_status,
            b.created_at,
            p.patient_name
        FROM bills b
        LEFT JOIN patients p
            ON b.patient_id = p.id
        ORDER BY b.id DESC
        """
    )

    bills_data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "billing.html",
        patients=patients_data,
        bills=bills_data
    )


# ==========================================
# DELETE BILL
# ==========================================

@app.route("/delete-bill/<int:id>")
def delete_bill(id):

    if "username" not in session:
        return redirect(url_for("home"))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM bills
        WHERE id = %s
        """,
        (id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("billing"))


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==========================================
# DATABASE TEST
# ==========================================

@app.route("/test-db")
def test_db():

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SHOW TABLES")

    tables = cursor.fetchall()

    cursor.close()
    db.close()

    return str(tables)


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)