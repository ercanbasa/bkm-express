BKM Express Ödeme Sistemi Entegrasyonu
======================================

##Yazar Hakkında
Ercan Başa  
Back-End Developer  
İletişim: ercanbasa88@gmail.com

##Sistem Gereksinimleri
* SUDS
* M2Crypto

##Kurulum
```
pip install suds   
sudo apt-get install python-dev  
sudo apt-get install python-m2crypt
```

##Nasıl Çalışır
BKM Express ödeme sistemi temel olarak birkaç adımdan oluşmaktadır. Bunlar sırası ile aşağıda anlatılmaktadır.

###Initialize Payment
Bu adımda BKM Express'e bildirilecek olan sipariş, firmanın kullanacağı bankalar, kredi kartları ve taksit seçenekleri BKM'nin webservice'ine post edilir ve cevap alınır. Dönen cevap başarılı ise kullanıcı BKM sayfasına yönlendirilir.

###Firma Tarafından Sağlanan Webservice
Kullanıcı BKM Express'e yönlendirildikten sonra, kullanıcı sizin göndermiş olduğunuz ödeme seçeneklerinden birini seçerek alışverişi tamamlama button'una basar. İşte bu anda BKM Express sizin belirtmiş olduğunuz webservice'e seçilmiş olan bilgileri post eder ve sizden bu ödeme için kullanmak istediğiniz pos bilgilerini ister.

###Sipariş Başarılı
Eğer sipariş sorunsuz olarak tamamlandıysa, BKM Express kullanıcıyı sizin belirtmiş olduğunuz success url'e yönlendirir.

###Sipariş Başarısız
Eğer sipariş herhangi bir nedenle tamamlanamadıysa BKM Express sizin belirtmiş olduğunuz fail url'e kullanıcıyı yönlendirir.

##Kullanılan Fonksiyonların Kısa Açıklamaları
Bu fonksiyonların detayları kod içerisinde inline olarak detaylıca açıklanmıştır. Zamanla bu dökümantasyona da eklenecektir.

###Sign(text_to_be_hashed)
```bkm_express.py``` içerisinde ```BkmExpress``` class'ına ait fonksiyondur. Tüm imza işlemleri bu fonksiyon ile yapılır.Parametre olarak ```text alır``` ve ```imzayı verir```.
###Verify(to_be_control,to_be_hashed)
Bkm Express tarafından yapılan postlardaki imzayı doğrulamak için kullanır. ```Boolean değer döndürür```. İlk parametresi ```gelen imza```, ikinci parametresi ```bizim üreteceğimiz imzadır```.


##Kullanırken Dikkat Edilmesi Gerekenler
Api, kullanmak isteyenler için pratiklik sağlamak ve uğraşmanız gereken birçok şeyi hafifletmek için yazılmıştır. Yazılan kod, yapılabilecek saldırılar göz ardı edilerek yazılmıştır. Firmanızın güvenliği için bu durumları göz önünde bulundurarak kendi önlemlerinizi alınız. Detaylar için inline dökümantasyonu okumanız faydalı olacaktır.
