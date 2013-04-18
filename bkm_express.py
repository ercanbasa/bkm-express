# -*- coding: utf-8 -*-
from suds.client import Client
from datetime import datetime
import hashlib
import base64
from M2Crypto import RSA
from django.http import HttpResponse

#Öncelikle sipariş modelinize bir extra field eklemeniz gerekli.
#Bu alana bkm express servisinden aldığınız "token" ı kaydetmeniz gerekli.
#Bunun nedeni siparişlerinizi sadece token ile filtreleyebilecek olmanız.

class BkmExpress(object):

	#birkaç fonksiyonda kullanacağımız için siparişi initte verdim.
	#initialize_payment fonksiyonundaki fiyat değerlerini bu siparişe göre oluşturmanız gerekli.
	#ben static olarak oluşturdum siz değiştirmelisiniz.
	def __init__(self,siparis):
		self.siparis=siparis

	#post edeceğiniz verileri imzalamak için gerekli fonksiyon. verilen texti SHA 256 with RSA olarak.
	#filename alanına bkm express e bildirmiş olduğunuz pem dosyasının yolunu verin.
	def sign(self,text_to_be_hashed=""):
	    filename = '/path/to/mykey.pem'
	    priv_key = RSA.load_key(filename)
	    digest = hashlib.sha256(text_to_be_hashed).digest()
	    signature=priv_key.sign(digest, 'sha256')
	    result=base64.b64encode(signature)
	    return result

	#bkm express den gelen imzaları doğrulamak için gerekli fonksiyon.
	#gelen verileri imzalayıp karşılaştırarak doğruluğunu kontrol eder.
	def verify(self,to_be_control,to_be_hashed):
		hashed=self.here_we_go(to_be_hashed)
		if hashed==to_be_control:
			return True
		return False

	#Buradaki fiyatlar statik olarak girildi.
	#self.siparişten almanız gerekli fakat kendi modelinize göre kendiniz oluşturmalısınız.
	#Ayrıca kullanmak istediğiniz her bankanın, bu bankaların her kartının ve her kart için yapılacak
	#taksitleri tek tek eklemelisiniz. Ben örnek olması amacıyla statik olarak bir tane oluşturdum.
	def initialize_payment(self):
		url = 'file:///path/to/BkmExpressPaymentService.wsdl'
		client = Client(url)

		##installment olustur. karta ait taksitler
		installment=client.factory.create('inst')
		installment.nofInst="1" #taksit sayısı
		installment.amountInst="1,00" #taksit başına düşen toplam tutar
		installment.cAmount="1,00" #kargo tutarı
		installment.tAmount="2,00" #toplam tutar kdv dahil
		installment.cPaid1stInst="true" #true yada false. kargo ücretinin ilk taksitte alınması için true olacak.
		installment.expInst="" #açıklama alanı. boş bırakılabilir

		##bin olustur. bankaya ait kartlar
		bin=client.factory.create('bin')
		bin.value="555555" #kart kodu
		bin.insts.inst.append(installment)

		##banka olustur. bkm express e gönderilecek bankalar.
		bank=client.factory.create('bank')
		bank.id="5555" #banka kodu
		bank.name="x bank" #banka adı
		bank.expBank="" #açıklama alanı. boş bırakılabilir
		bank.bins.bin.append(bin)

		##inst_options olustur
		inst_opt=client.factory.create('instOpts')
		inst_opt.bank.append(bank) #oluşturulan bankalar bu listeye append edilir.

		## ws request olustur
		ws_request=client.factory.create('initializePaymentWSRequest')
		ws_request.mId="xxxxx" #bkm express den alınan firma idsi.(merchant id)
		ws_request.sUrl="https://www.example.com/success_url" #ödeme onaylandığında dönüş yapılacak url
		ws_request.cUrl="https://www.example.com/fail_url" #ödeme başarısız olduğunda dönüş yapılacak url
		ws_request.sAmount="1,00" #kargo hariç toplam tutar
		ws_request.cAmount="1,00" #kargo tutarı
		ws_request.instOpts=inst_opt 
		d=datetime.now()
		ws_request.ts= d.strftime("%Y%m%d-%H:%M:%S")

		#İmzalanacak olan text oluşturuluyor. Değiştirmenize gerek yok. 
		datatoBeHashed=""
		datatoBeHashed+=ws_request.mId
		datatoBeHashed+=ws_request.sUrl
		datatoBeHashed+=ws_request.cUrl
		datatoBeHashed+=ws_request.sAmount
		datatoBeHashed+=ws_request.cAmount
		for item in ws_request.instOpts.bank:
		    datatoBeHashed+=item.id
		    datatoBeHashed+=item.name
		    datatoBeHashed+=item.expBank
		    for it in item.bins.bin:
			datatoBeHashed+=it.value
		        for i in it.insts.inst:
			    datatoBeHashed+=i.nofInst
			    datatoBeHashed+=i.amountInst
			    datatoBeHashed+=i.cAmount
			    datatoBeHashed+=i.tAmount
			    datatoBeHashed+=i.cPaid1stInst
			    datatoBeHashed+=i.expInst
		datatoBeHashed+=ws_request.ts

		ws_request.s=self.sign(datatoBeHashed)

		# initialize payment olustur.
		initialize_payment = client.factory.create('initializePayment')
		initialize_payment.initializePaymentWSRequest=ws_request

		#servise istek yapılıyor.
		payment_response= client.service.initializePayment(initializePaymentWSRequest=ws_request)

		#eğer istek sonucu başarılıysa sayfanız bkm express e yönlendirme adımına geçirilir.
		if payment_response.result.resultMsg =="Success":
			return self.redirect_to_bkm(payment_response)
		else:
			#siparişinizi başarısıza çevirebilirsiniz. sisteminizin akışına göre yazınız.
			return fake_fail_function(payment_response.result.resultMsg, self.siparis)

		#Bu fonksiyonda sayfa bkm express e yönlendirilir.
		#Burada önemli olan initialize_payment aşamasında alınan response daki token ı siparişin
		#extra alanına eklemek.
	def redirect_to_bkm(self,payment_response):
		response = payment_response

		siparis=self.siparis
		siparis.extra=response.t
		siparis.save()

		d=datetime.now()
		ts= d.strftime("%Y%m%d-%H:%M:%S")

		s=self.sign(response.t+ts)

		#response içinde gelen url ve token bilgisi forma hidden olarak geçilir.
		#yeni timestamp ve imza oluşturularak yine hidden olarak eklenir ve submit edilir.

		form_to_post = '<form action="%s" id="bkm" method="POST">'%response.url
		form_to_post += '<input type="hidden" name="t" value="%s">'%response.t
		form_to_post += '<input type="hidden" name="ts" value="%s">'%ts
		form_to_post += '<input type="hidden" name="s" value="%s">'%s
		form_to_post += "</form><script>document.getElementById('bkm').submit();</script>"

		return HttpResponse(form_to_post)