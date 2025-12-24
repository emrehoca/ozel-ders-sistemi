from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Ogrenci, Ders, Odev, Odeme
from datetime import datetime
import uuid
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ozelders2025superkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/ozelders.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'future': True}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('12345')
        db.session.add(admin)
        db.session.commit()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Giriş yapmalısınız!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            flash('Hoş geldiniz!', 'success')
            return redirect(url_for('ana_sayfa'))
        flash('Hatalı giriş!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Bu kullanıcı adı alınmış!', 'danger')
        else:
            user = User(username=request.form['username'])
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            flash('Kayıt başarılı! Giriş yapın.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def ana_sayfa():
    user_id = session['user_id']
    ogrenci_sayisi = Ogrenci.query.filter_by(user_id=user_id).count()
    ders_sayisi = Ders.query.filter_by(user_id=user_id).count()
    return render_template('index.html', ogrenci_sayisi=ogrenci_sayisi, ders_sayisi=ders_sayisi)

# === ÖĞRENCİLER ===
@app.route('/ogrenciler')
@login_required
def ogrenciler():
    user_id = session['user_id']
    arama = request.args.get('arama', '')
    query = Ogrenci.query.filter_by(user_id=user_id)
    if arama:
        query = query.filter(Ogrenci.ad.ilike(f'%{arama}%'))
    ogrenciler = query.all()
    return render_template('ogrenciler.html', ogrenciler=ogrenciler, arama=arama)

@app.route('/ogrenci/ekle', methods=['GET', 'POST'])
@app.route('/ogrenci/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def ogrenci_form(id=None):
    user_id = session['user_id']
    ogrenci = Ogrenci.query.get_or_404(id) if id else None
    if ogrenci and ogrenci.user_id != user_id:
        flash('Yetkisiz erişim!', 'danger')
        return redirect(url_for('ogrenciler'))

    if request.method == 'POST':
        if ogrenci:
            ogrenci.ad = request.form['ad']
            ogrenci.telefon = request.form['telefon']
            ogrenci.veli_telefon = request.form['veli_telefon']
            ogrenci.notlar = request.form['notlar']
        else:
            ogrenci = Ogrenci(
                ad=request.form['ad'],
                telefon=request.form['telefon'],
                veli_telefon=request.form['veli_telefon'],
                notlar=request.form['notlar'],
                user_id=user_id
            )
            db.session.add(ogrenci)
        db.session.commit()
        flash('Öğrenci kaydedildi!', 'success')
        return redirect(url_for('ogrenciler'))
    return render_template('ogrenci_form.html', ogrenci=ogrenci)

@app.route('/ogrenci/sil/<int:id>')
@login_required
def ogrenci_sil(id):
    user_id = session['user_id']
    ogrenci = Ogrenci.query.get_or_404(id)
    if ogrenci.user_id != user_id:
        flash('Yetkisiz!', 'danger')
        return redirect(url_for('ogrenciler'))
    db.session.delete(ogrenci)
    db.session.commit()
    flash('Öğrenci silindi.', 'success')
    return redirect(url_for('ogrenciler'))

# Diğer route'lar (dersler, odevler, takvim, odemeler) benzer yapıdadır.
# Yer kısıtlaması nedeniyle burada tümü yazılmadı ama aynı mantıkla devam eder.

if __name__ == '__main__':
    app.run(debug=True)
# === DERSLER ===
@app.route('/dersler')
@login_required
def dersler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    dersler = Ders.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    return render_template('dersler.html', ogrenciler=ogrenciler, dersler=dersler)

@app.route('/ders/ekle', methods=['GET', 'POST'])
@login_required
def ders_ekle():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    if request.method == 'POST':
        link = request.form.get('link')
        if request.form.get('platform') == 'Jitsi Meet' and not link:
            link = f"https://meet.jit.si/OzelDers-{uuid.uuid4().hex[:8]}"
        
        ders = Ders(
            ogrenci_id=request.form['ogrenci_id'],
            tarih=request.form['tarih'],
            saat=request.form['saat'],
            konu=request.form['konu'],
            online='online' in request.form,
            platform=request.form.get('platform'),
            link=link,
            user_id=user_id
        )
        db.session.add(ders)
        db.session.commit()
        flash('Ders eklendi!', 'success')
        return redirect(url_for('dersler'))
    return render_template('ders_form.html', ogrenciler=ogrenciler)

@app.route('/ders/sil/<int:id>')
@login_required
def ders_sil(id):
    ders = Ders.query.get_or_404(id)
    if ders.user_id != session['user_id']:
        flash('Yetkisiz!', 'danger')
        return redirect(url_for('dersler'))
    db.session.delete(ders)
    db.session.commit()
    flash('Ders silindi.', 'success')
    return redirect(url_for('dersler'))

# === ÖDEVLER ===
@app.route('/odevler')
@login_required
def odevler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    odevler = Odev.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    return render_template('odevler.html', ogrenciler=ogrenciler, odevler=odevler)

@app.route('/odev/ekle', methods=['POST'])
@login_required
def odev_ekle():
    user_id = session['user_id']
    odev = Odev(
        ogrenci_id=request.form['ogrenci_id'],
        tanim=request.form['tanim'],
        teslim_tarihi=request.form['teslim_tarihi'],
        user_id=user_id
    )
    db.session.add(odev)
    db.session.commit()
    flash('Ödev verildi!', 'success')
    return redirect(url_for('odevler'))

@app.route('/odev/tamamla/<int:id>')
@login_required
def odev_tamamla(id):
    odev = Odev.query.get_or_404(id)
    if odev.user_id != session['user_id']:
        flash('Yetkisiz!', 'danger')
    else:
        odev.tamamlandi = True
        db.session.commit()
        flash('Ödev tamamlandı!', 'success')
    return redirect(url_for('odevler'))

# === TAKVİM ===
@app.route('/takvim')
@login_required
def takvim():
    user_id = session['user_id']
    yil = int(request.args.get('yil', datetime.now().year))
    ay = int(request.args.get('ay', datetime.now().month))
    cal = calendar.monthcalendar(yil, ay)
    dersler = Ders.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    ders_dict = {}
    for ders in dersler:
        key = ders.tarih
        if key not in ders_dict:
            ders_dict[key] = []
        ders_dict[key].append(ders)
    return render_template('takvim.html', yil=yil, ay=ay, cal=cal, ders_dict=ders_dict, calendar=calendar)

# === ÖDEMELER ===
@app.route('/odemeler')
@login_required
def odemeler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    odemeler = Odeme.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    toplamlar = {}
    for ogr in ogrenciler:
        toplam = db.session.query(db.func.sum(Odeme.tutar)).filter(Odeme.ogrenci_id == ogr.id).scalar() or 0
        toplamlar[ogr.id] = toplam
    return render_template('odemeler.html', ogrenciler=ogrenciler, odemeler=odemeler, toplamlar=toplamlar)

@app.route('/odeme/ekle', methods=['POST'])
@login_required
def odeme_ekle():
    user_id = session['user_id']
    odeme = Odeme(
        ogrenci_id=request.form['ogrenci_id'],
        tutar=float(request.form['tutar']),
        aciklama=request.form['aciklama'],
        user_id=user_id
    )
    db.session.add(odeme)
    db.session.commit()
    flash('Ödeme kaydedildi!', 'success')
    return redirect(url_for('odemeler'))
# === DERSLER ===
@app.route('/dersler')
@login_required
def dersler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    dersler = Ders.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    return render_template('dersler.html', ogrenciler=ogrenciler, dersler=dersler)

@app.route('/ders/ekle', methods=['GET', 'POST'])
@login_required
def ders_ekle():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    if request.method == 'POST':
        link = request.form.get('link')
        if request.form.get('platform') == 'Jitsi Meet' and not link:
            link = f"https://meet.jit.si/OzelDers-{uuid.uuid4().hex[:8]}"
        
        ders = Ders(
            ogrenci_id=request.form['ogrenci_id'],
            tarih=request.form['tarih'],
            saat=request.form['saat'],
            konu=request.form['konu'],
            online='online' in request.form,
            platform=request.form.get('platform'),
            link=link,
            user_id=user_id
        )
        db.session.add(ders)
        db.session.commit()
        flash('Ders eklendi!', 'success')
        return redirect(url_for('dersler'))
    return render_template('ders_form.html', ogrenciler=ogrenciler)

@app.route('/ders/sil/<int:id>')
@login_required
def ders_sil(id):
    ders = Ders.query.get_or_404(id)
    if ders.user_id != session['user_id']:
        flash('Yetkisiz!', 'danger')
        return redirect(url_for('dersler'))
    db.session.delete(ders)
    db.session.commit()
    flash('Ders silindi.', 'success')
    return redirect(url_for('dersler'))

# === ÖDEVLER ===
@app.route('/odevler')
@login_required
def odevler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    odevler = Odev.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    return render_template('odevler.html', ogrenciler=ogrenciler, odevler=odevler)

@app.route('/odev/ekle', methods=['POST'])
@login_required
def odev_ekle():
    user_id = session['user_id']
    odev = Odev(
        ogrenci_id=request.form['ogrenci_id'],
        tanim=request.form['tanim'],
        teslim_tarihi=request.form['teslim_tarihi'],
        user_id=user_id
    )
    db.session.add(odev)
    db.session.commit()
    flash('Ödev verildi!', 'success')
    return redirect(url_for('odevler'))

@app.route('/odev/tamamla/<int:id>')
@login_required
def odev_tamamla(id):
    odev = Odev.query.get_or_404(id)
    if odev.user_id != session['user_id']:
        flash('Yetkisiz!', 'danger')
    else:
        odev.tamamlandi = True
        db.session.commit()
        flash('Ödev tamamlandı!', 'success')
    return redirect(url_for('odevler'))

# === TAKVİM ===
@app.route('/takvim')
@login_required
def takvim():
    user_id = session['user_id']
    yil = int(request.args.get('yil', datetime.now().year))
    ay = int(request.args.get('ay', datetime.now().month))
    cal = calendar.monthcalendar(yil, ay)
    dersler = Ders.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    ders_dict = {}
    for ders in dersler:
        key = ders.tarih
        if key not in ders_dict:
            ders_dict[key] = []
        ders_dict[key].append(ders)
    return render_template('takvim.html', yil=yil, ay=ay, cal=cal, ders_dict=ders_dict, calendar=calendar)

# === ÖDEMELER ===
@app.route('/odemeler')
@login_required
def odemeler():
    user_id = session['user_id']
    ogrenciler = Ogrenci.query.filter_by(user_id=user_id).all()
    odemeler = Odeme.query.join(Ogrenci).filter(Ogrenci.user_id == user_id).all()
    toplamlar = {}
    for ogr in ogrenciler:
        toplam = db.session.query(db.func.sum(Odeme.tutar)).filter(Odeme.ogrenci_id == ogr.id).scalar() or 0
        toplamlar[ogr.id] = toplam
    return render_template('odemeler.html', ogrenciler=ogrenciler, odemeler=odemeler, toplamlar=toplamlar)

@app.route('/odeme/ekle', methods=['POST'])
@login_required
def odeme_ekle():
    user_id = session['user_id']
    odeme = Odeme(
        ogrenci_id=request.form['ogrenci_id'],
        tutar=float(request.form['tutar']),
        aciklama=request.form['aciklama'],
        user_id=user_id
    )
    db.session.add(odeme)
    db.session.commit()
    flash('Ödeme kaydedildi!', 'success')

    return redirect(url_for('odemeler'))
