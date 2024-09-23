from flask import Flask, request, jsonify
import pyodbc
from datetime import datetime
import traceback

app = Flask(__name__)

def get_db_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=VOLKAN\SQLEXPRESS;'
            'DATABASE=Kutuphane;'
            'Trusted_Connection=yes;'
        )
        return conn
    except pyodbc.Error as e:
        print(f"Veritabanına bağlanılamadı: {e}")
        return None

@app.route('/book-add', methods=['POST'])
def kitap_ekle():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veri tabanına bağlanılamadı"}), 500
    try:
        data = request.json
        print(f"Alınan veri: {data}")   
        kitap_id = data.get('KitapID')
        yazar_key = data.get('YazarID')
        kitap_baslik = data.get('KitapBasligi')
        yayin_tarih = data.get('YayinTarihi')
        if kitap_id is None or yazar_key is None or kitap_baslik is None or yayin_tarih is None:
            return jsonify({"Error": "Eksik veri: YazarID, KitapBasligi, YayinTarihi eksik"}), 400
        try:
            yayin_tarih = datetime.strptime(yayin_tarih, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"Error": "Zaman geçersiz format, YYYY-MM-DD şeklinde olmalıdır."})
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dbo.Kitaplar (KitapID, YazarID, KitapBasligi, YayinTarihi) VALUES (?, ?, ?, ?)",
            (kitap_id, yazar_key, kitap_baslik, yayin_tarih)
        )
        conn.commit()
        return jsonify({"Message": "Kitaplar veritabanına başarıyla eklendi"}), 201
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/book-yazar', methods=['POST'])
def yazar_ekle():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veri tabanına bağlanılamadı"}), 500
    try:
        data = request.json
        print(f"Alınan veri: {data}")
        yazar_key = data.get('YazarID')
        yazar_adi = data.get('YazarAdi')
        if yazar_key is None or yazar_adi is None:
            return jsonify({"Error": "Eksik veri: YazarID veya YazarAdi eksik"}), 400
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dbo.Yazarlar (YazarID, YazarAdi) VALUES (?, ?)",
            (yazar_key, yazar_adi)
        )
        conn.commit()
        return jsonify({"Message": "Yazar veritabanına başarıyla eklendi"}), 201
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/books/getir', methods=['GET'])
def kitaplar_getir():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT k.KitapID, y.YazarAdi, k.KitapBasligi, k.YayinTarihi
            FROM dbo.Kitaplar k 
            JOIN dbo.Yazarlar y ON k.YazarID = y.YazarID
        """)
    
        """ {
        -----------------------------------------------------------------
        "KitapID": 2,
        "YazarAdi": 101,  ///#GET ATACAĞIN SORGU ŞEKLİ BÖYLE OLMALI
        "KitapBasligi": "Örnek Kitap",
        "YayinTarihi": "2024-01-01"}
        ---------------------------------------------------------------------"""
        books = cursor.fetchall()
        
        book_list = []
        for book in books:
            book_data = {
                "KitapID": book.KitapID,
                "YazarAdi": book.YazarAdi,
                "KitapBasligi": book.KitapBasligi,
                "YayinTarihi": book.YayinTarihi.strftime('%Y-%m-%d')
            }
            book_list.append(book_data)

        return jsonify(book_list), 200
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/books-guncel', methods=['PUT'])
def books_guncel():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    
    try:
        data = request.json
        print(f"Alınan veri: {data}")
        
        kitap_id = data.get('KitapID') 
        yazar_key = data.get('YazarID') 
        kitap_baslik = data.get('KitapBasligi')  
        yayin_tarih = data.get('YayinTarihi')  
        
        if kitap_id is None:
            return jsonify({"Error": "Eksik veri: KitapID gereklidir."}), 400

        update_fields = []
        params = []
    
        """
        ---------------------PUT ATMAK İÇİN-----------------------------------
        {
        "KitapID": "1",   // Güncellenmek istenen kitabın ID'si
        "YazarID": "2",  // İsteğe bağlı: Yeni YazarID
        "KitapBasligi": "Yeni Başlık", // İsteğe bağlı: Yeni başlık
        "YayinTarihi": "2023-09-22" // İsteğe bağlı: Yeni yayın tarihi
        ---------------------------------------------------------------
        }"""


        if yazar_key is not None:
            update_fields.append("YazarID = ?")
            params.append(yazar_key)

        if kitap_baslik is not None:
            update_fields.append("KitapBasligi = ?")
            params.append(kitap_baslik)

        if yayin_tarih is not None:
            try:
                yayin_tarih = datetime.strptime(yayin_tarih, '%Y-%m-%d').date()
                update_fields.append("YayinTarihi = ?")
                params.append(yayin_tarih)
            except ValueError:
                return jsonify({"Error": "Zaman geçersiz format. YYYY-MM-DD şeklinde olmalıdır."})

        if not update_fields:
            return jsonify({"Error": "Güncellenecek veri yok."}), 400

        params.append(kitap_id)
        
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE dbo.Kitaplar SET {', '.join(update_fields)} WHERE KitapID = ?",
            params
        )
        
        if cursor.rowcount == 0:
            return jsonify({"Message": "Güncellenecek kitap bulunamadı."}), 404
        
        conn.commit()
        return jsonify({"Message": "Kitap başarıyla güncellendi."}), 200
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı hatası: {str(e)}"}), 500
    finally:
        conn.close()
@app.route('/books-sil/<int:kitap_id>', methods=['DELETE'])
def book_delete(kitap_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error":"Veritabanı bağlanılamadı"}),500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM dbo.Kitaplar WHERE KitapID = ?",
            (kitap_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({"Error":"Belirtilen KitapID bulunamadı"}),404
        conn.commit()
        return jsonify({"Error":"Kullanıcı başarıyla silindi."}),200
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500

    finally:
        conn.close()
if __name__ == '__main__':
    app.run(debug=True)
