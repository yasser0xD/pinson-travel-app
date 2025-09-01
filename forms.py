from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed

class FeedbackForm(FlaskForm):
    name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=6, max=20)])
    message = TextAreaField('محتوى الطلب أو الملاحظة', validators=[DataRequired(), Length(min=5)])
    file = FileField('تحميل ملف', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'الملفات المسموحة: PDF, PNG, JPG')
    ])
