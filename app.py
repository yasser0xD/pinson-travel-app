from flask import Flask, render_template, request, flash, redirect, abort
import secrets
import os
import requests
from werkzeug.utils import secure_filename
import mysql.connector
import uuid
from datetime import datetime
from markupsafe import escape
from flask_wtf.csrf import CSRFProtect
from forms import FeedbackForm

# الاتصال بقاعدة البيانات
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pinson25@",
    database="pinson_travel"
)
cursor = db.cursor(dictionary=True)

# إعداد مجلد رفع الملفات
BASE_UPLOAD_FOLDER = 'uploads'
FEEDBACK_SUBFOLDER = 'feedbacks'
FULL_UPLOAD_PATH = os.path.join(BASE_UPLOAD_FOLDER, FEEDBACK_SUBFOLDER)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = FULL_UPLOAD_PATH
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# إنشاء مجلد رفع الملفات إن لم يكن موجودًا
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# التحقق من امتداد الملف

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# تمرير السنة الحالية إلى القوالب

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@app.route('/')
def home():
    cursor.execute("""
        SELECT * FROM offers 
        WHERE expires_at IS NULL OR expires_at >= CURDATE()
        ORDER BY id DESC
        LIMIT 6
    """)
    offers = cursor.fetchall()
    return render_template('home.html', offers=offers)


@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    gallery_folder = os.path.join(app.static_folder, 'gallery')
    images = []
    for filename in os.listdir(gallery_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images.append({'filename': filename})
    return render_template('gallery.html', images=images)

# ✅ صفحة feedback
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        name = escape(form.name.data)
        phone = form.phone.data
        message = escape(form.message.data)
        file = form.file.data

        if file.filename == '':
            flash("❌ يرجى اختيار ملف صالح.")
            return redirect("/feedback")

        if not allowed_file(file.filename):
            flash("❌ امتداد الملف غير مدعوم.")
            return redirect("/feedback")

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        try:
            with open(filepath, "rb") as f:
                res = requests.post(
                    "http://192.168.1.3:5001/receive",
                    files={"file": f},
                    data={"name": name, "phone": phone, "message": message}
                )
            if res.status_code == 200:
                flash("✅ تم إرسال الملف بنجاح.")
            else:
                flash("⚠ فشل في إرسال الملف إلى السيرفر.")
        except Exception as e:
            flash(f"❌ خطأ أثناء الإرسال: {e}")

        return redirect("/feedback")

    return render_template("feedback.html", form=form)

# ✅ صفحة العروض
@app.route("/offers")
def offers():
    try:
        cursor.execute("""
            SELECT * FROM offers 
            WHERE expires_at IS NULL OR expires_at >= CURDATE()
            ORDER BY id DESC
        """)
        offers = cursor.fetchall()
        return render_template("offers.html", offers=offers)
    except Exception as e:
        flash("⚠ حدث خطأ أثناء تحميل العروض", "danger")
        print("Offers error:", e)
        return render_template("offers.html", offers=[])

# ✅ تفاصيل عرض
@app.route("/offers/<int:offer_id>")
def offer_details(offer_id):
    cursor.execute("SELECT * FROM offers WHERE id = %s", (offer_id,))
    offer = cursor.fetchone()
    if not offer:
        abort(404)
    return render_template("offer_details.html", offer=offer)

# ✅ تشغيل السيرفر
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
