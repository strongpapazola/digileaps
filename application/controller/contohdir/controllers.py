from flask import Blueprint, jsonify, request, make_response, render_template
from flask_jwt import JWT, jwt_required, current_identity
from flask import current_app as app
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import hashlib
import datetime
import requests
import cv2
from models import Data
from time import gmtime, strftime
import os
import numpy as np
import base64
import random
import warnings
from werkzeug.datastructures import ImmutableMultiDict

from pyfcm import FCMNotification

now = datetime.datetime.now()

contoh = Blueprint('contoh', __name__, static_folder = '../../upload/foto_contoh', static_url_path="/media")
#UNTUK SAVE GAMBAR
def save(encoded_data, filename):
	arr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
	img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
	return cv2.imwrite(filename, img)

def tambahLogs(logs):
	f = open(app.config['LOGS'] + "/" + secure_filename(strftime("%Y-%m-%d"))+ ".txt", "a")
	f.write(logs)
	f.close()

push_service = FCMNotification(api_key=app.config['FCM_ANDROID'])
def push_notifications(id_user,id_notification_category,data_users,message_title,message_body):
	dt 					= Data()
	registration_ids 	= data_users

	message_body = {
		"title"		: message_title,
		"body"		: str(id_notification_category)+'#'+message_body,
		"content_available": True,
		"priority"	: "high"
	}

	query1 	= 'INSERT INTO `notification`(`id_user`, `id_notification_category`, `message_title`, `message_body`) VALUES (%s,%s,%s,%s)'
	values1 = (id_user, id_notification_category, message_title, message_body['body'])
	dt.insert_data(query1,values1)

	result = push_service.notify_multiple_devices(registration_ids=registration_ids, data_message=message_body)
	return result

def kirim_email():
	template = render_template('templates2/course_checkout.html', invoice=invoice_number, nama_course=nama_course, harga=harga_potong, code_unic=kode_unik_pem, batas_waktu=waktu_akhir_pem, no_rek="1260007875718")
	url = app.config['MAIL_SERVER']
	payload = {'pengirim': app.config['MAIL_SENDER'],'penerima': email,'isi': template,'judul': '[DAFTAR COURSE BERHASIL]'}
	files = {}
	headers = {'X-API-KEY': app.config['X-API-KEY']}
	response = requests.request('POST', url, headers = headers, data = payload, files = files, allow_redirects=False)

@contoh.route('/hello', methods=['GET','OPTIONS'])
@cross_origin()
def hello():
	return make_response('lol')

# ========================= GET AREA ===============================
@contoh.route('/contoh', methods=['GET', 'OPTIONS'])
# @jwt_required()
@cross_origin()
def get_contoh():
	query = "SELECT * FROM contoh"
	values = ()

	page = request.args.get("page")
	is_aktif = request.args.get("is_aktif")
	q = request.args.get("q")

	if (page == None):
		page = 1
	if is_aktif:
		query = query + " AND is_aktif = %s "
		values = values + (is_aktif, )
	if q:
		query += " AND CONCAT_WS('|', judul, deskripsi) LIKE %s "
		values += ('%'+q+'%',)
	
	dt = Data()
	rowCount = dt.row_count(query, values)
	hasil = dt.get_data_lim(query, values, page)
	hasil = {'data': hasil , 'status_code': 200, 'page': page, 'offset': '10', 'row_count': rowCount}
	########## INSERT LOG ##############
	imd = ImmutableMultiDict(request.args)
	imd = imd.to_dict()
	param_logs = "[" + str(imd) + "]"
	logs = "{'action':'Lihat contoh','params':'"+ param_logs +"','date':'"+secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+"'}\n"
	tambahLogs(logs)
	####################################
	return make_response(jsonify(hasil),200)

# ================================= POST AREA ==============================
@contoh.route('/contoh', methods=['POST', 'OPTIONS'])
# @jwt_required()
@cross_origin()
def insert_contoh():
	query = ""
	values = ()
	try:
		data = request.json
		contoh1 = data['contoh1']
		foto = data['foto']
		
		filename = secure_filename(strftime("%Y-%m-%d %H:%M:%S")+"_foto_contoh.png")
		save(foto, os.path.join(app.config['UPLOAD_FOLDER_GAMBAR_CONTOH'], filename))

		dt = Data()
		values = (contoh1, pass_ency, nama, no_telepon, alamat, filename, jk, tanggal_lahir)
		dt.insert_data(query,values)

		hasil = "berhasil"
		param_logs = "[" + str(data) + "]"
		logs = "{'id_user':'"+ "str(current_identity['user_id'])" +"','roles':'"+ "str(current_identity['roles'])" +"','action':'Tambah Artikel','date':'"+secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+"'}\n"
		tambahLogs(logs)
	except Exception as e:
			return make_response(jsonify({'description':str(e),'error': 'Bad Request','id_user_code':400}), 400)
	return make_response(jsonify({'id_user_code':200, 'description': hasil } ), 200)

# ================================ UPDATE AREA =================================
@contoh.route('/contoh', methods=['PUT', 'OPTIONS'])
# @jwt_required()
@cross_origin()
def update_contoh():
	tableName = "contoh"
	try:
		dt = Data()
		data = request.json

		query = "UPDATE "+tableName+" SET id_contoh = id_contoh"

		values = ()

		id_contoh = data['id_contoh']

		if 'contoh1' in data:
			contoh1 = data["contoh1"]
			query = query + ", contoh1 = %s"
			values = values + (contoh1, )
		if 'foto' in data:
			foto = data["foto"]
			query = query + ", foto = %s"

			filename = secure_filename(strftime("%Y-%m-%d %H:%M:%S")+"_foto_contoh.png")
			save(foto, os.path.join(app.config['UPLOAD_FOLDER_GAMBAR_CONTOH'], filename))
			
			values = values + (filename, )
			del data['foto']

		query = query + " WHERE id_contoh = %s "
		values = values + (id_contoh, )
		dt = Data()
		dt.insert_data(query,values)

		
		hasil = "berhasil"
		if "" in data:
			del data['foto']
		param_logs = "[" + str(data) + "]"
		logs = "{'id_user':'"+ "str(current_identity['user_id'])" +"','roles':'"+ "str(current_identity['roles'])" +"','action':'Update artikel','params':'"+ param_logs +"','date':'"+secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+"'}\n"
		tambahLogs(logs)
	except Exception as e:
		return make_response(jsonify({'description':str(e),'error': 'Bad Request','id_user_code':400}), 400)
	return make_response(jsonify({'id_user_code':200, 'description': hasil } ), 200)
