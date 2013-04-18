# -*- coding: utf-8 -*-
from bkm_express import BkmExpress
from django.http import HttpResponse
from xml.dom.minidom import parseString

#Kendi sipariş modelinizle değiştirin.
from models import Order

#initialize payment adımında verdiğiniz success url in methodu
#exception ve güvenlik için alacağınız önlemleri kendiniz yazmalısınız
def bkm_success(request):
	token = request.POST.get('t','')
	siparis = Order.objects.get(extra=token)
	return fake_success_function(u"Başarılı Sipariş", siparis)

#initialize payment adımında verdiğiniz fail url in methodu
#exception ve güvenlik için alacağınız önlemleri kendiniz yazmalısınız
def bkm_fail(request):
    hata_mesaji = u"Ödeme Başarısız. Nedeni: "
    hata_kodu = request.POST.get('r', '')
    token = request.POST.get('t','')

    ERROR_CODES = {
    	'1': u"Kullanıcı işlemi iptal ederek ekrandan ayrıldı.",
    	'2': u"Express'e log-in başarısız.",
    	'3': u"Banka doğrulaması başarısız.",
    	'4': u"3D Secure doğrulaması başarısız.",
    	'5': u"POS’tan otorizasyon alınamadı.",
    	'6': u"İş yeri imzası yanlış.",
    	'99': u"İstekle ilgili genel hata (Bad request).",
    }

    hata_mesaji += ERROR_CODES.get(hata_kodu,'')
    #sipariş objesini alıyoruz
    siparis = Order.objects.get(extra= token)
    #bu siparişin başarısız olduğunu belirtiyoruz.
    return fake_fail_function(hata_mesaji, siparis)

#Bu fonksiyonu kullanan url in bkm express tarafında firma için tanımlanması gerek.
#Bkm burayı webservice olarak kullanıyor. SOAP servis gibi görülmeli sanıyorum epey bir diretmişlerdi bunun için.
#Ben burada bir hile yapıyorum. Get yapıldığında wsdl döndüren post edildiğinde xml döndüren bir url oluyor bu.
#Siz başka şekilde anlaşabilirsiniz belki bkm ile yada soap servis yazabilirsiniz.  
def api_for_bkm(request):
	if request.method=="POST":
		#Bkm tarafından müşterinin bkm üzerinde seçtiği banka, kart ve tasit bilgileri post ediliyor.
		istek=request.body
		parsed_istek = parseString(istek).getElementsByTagName('ns2:requestMerchInfoWSRequest')[0]
		t=parsed_istek.getElementsByTagName('t')[0].firstChild.data #token
		bid=parsed_istek.getElementsByTagName('bid')[0].firstChild.data #banka kodu
		bName=parsed_istek.getElementsByTagName('bName')[0].firstChild.data #banka adı
		cBin=parsed_istek.getElementsByTagName('cBin')[0].firstChild.data #kart kodu
		nofInst=parsed_istek.getElementsByTagName('nofInst')[0].firstChild.data #taksit sayısı
		ts=parsed_istek.getElementsByTagName('ts')[0].firstChild.data #postun yapıldığı timestamp
		s=parsed_istek.getElementsByTagName('s')[0].firstChild.data #bkm tarafından gönderilen imza

		siparis = Order.objects.get(extra= t)
		bkm=BkmExpress(siparis)

		#Gelen posttaki imzanın doğruluğu kontrol ediliyor.
		text_to_test=t+bid+bName+cBin+nofInst+ts
		is_verified=bkm.verify(s, text_to_test)
		if not is_verified:
			return fake_fail_function(hata_mesaji, siparis)

		pos_url="" #pos urli
		pos_id="" #pos kullanıcı adı
		pos_pass="" #pos şifresi
		auth_3d="false" #true yada false olacak. 3d desteği vermek isteniyorsa.
		mpi_url="" #mpi urli
		mpi_id="" #mpi idsi
		mpi_pass="" #mpi şifresi
		md="" #
		xid="" #
		dec_3d="false" #işlem 3d ile devam edemezse 3d siz devam edilsin mi
		cip="xxx.xxx.xxx.xxx" #firma ipsi
		extra='{"xx":"xx"}' #her pos için bu parametrelerin içinde olmayan zorunlu alanlar eklenmeli.
						#diğer bankaların dökümantasyonlarını okumalısınız malesef.
		result_code="0"
		result_message="SUCCESS"
		result_det=""
		d=datetime.datetime.now()
		ts= d.strftime("%Y%m%d-%H:%M:%S")

		data_to_hash=t+pos_url+pos_id+pos_pass+auth_3d+mpi_url+mpi_id+mpi_pass+md+xid+dec_3d+cip+extra+ts

		s=bkm.sign(data_to_hash)

		#response için kullanılacak olan xml
		xml_to_response='<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
		xml_to_response+='<s:Body><bkm:requestMerchInfoResponse xmlns:bkm="http://www.bkmexpress.com.tr">'
		xml_to_response+='<bkm:requestMerchInfoWSResponse>'
		xml_to_response+='<t>%s</t>'%t
		xml_to_response+='<posUrl>%s</posUrl>'%pos_url
		xml_to_response+='<posUid>%s</posUid>'%pos_id
		xml_to_response+='<posPwd>%s</posPwd>'%pos_pass
		xml_to_response+='<s3Dauth>%s</s3Dauth>'%auth_3d
		xml_to_response+='<mpiUrl>%s</mpiUrl>'%mpi_url
		xml_to_response+='<mpiUid>%s</mpiUid>'%mpi_id
		xml_to_response+='<mpiPwd>%s</mpiPwd>'%mpi_pass
		xml_to_response+='<md>%s</md>'%md
		xml_to_response+='<xid>%s</xid>'%xid
		xml_to_response+='<s3DFDec>%s</s3DFDec>'%dec_3d
		xml_to_response+='<cIp>%s</cIp>'%cip
		xml_to_response+='<extra>%s</extra>'%extra
		xml_to_response+='<ts>%s</ts>'%ts
		xml_to_response+='<s>%s</s>'%s
		xml_to_response+='<result>'
		xml_to_response+='<resultCode>%s</resultCode>'%result_code
		xml_to_response+='<resultMsg>%s</resultMsg>'%result_message
		xml_to_response+='<resultDet>%s</resultDet>'%result_det
		xml_to_response+='</result>'
		xml_to_response+='</bkm:requestMerchInfoWSResponse>'
		xml_to_response+='</bkm:requestMerchInfoResponse></s:Body></s:Envelope>'

		return HttpResponse(xml_to_response,'text/xml')

	else:
		url = open('/path/to/RequestMerchInfoService_latest.wsdl','r')
        return HttpResponse(url.read(),'text/xml')

#Bu fonksiyon initialize_payment i çağırmak için. 
#Sipriş formu valid ise ve ödeme tipi bkm ise bu fonksiyon çağırılabilir.
def bkm_express_odeme(self, siparis):
	bkm=BkmExpress(siparis)
	return bkm.initialize_payment()
	